#!/usr/bin/env python3
"""
FastAPI backend for the MEA pipeline control UI.

Serves the single-page frontend and exposes the watcher as a REST API:

    GET  /api/schema        every run_pipeline_driver.py option (drives the form)
    GET  /api/config        current saved job config
    POST /api/config        save job config (validates paths)
    POST /api/browse        list subdirectories of a server path (path picker)
    POST /api/preview       show the exact command that will be run
    GET  /api/status        watcher state + per-run status (polled by the UI)
    POST /api/watcher/start start watching
    POST /api/watcher/stop  stop watching
    POST /api/runs/reset    forget a run so it can be re-processed
    GET  /api/runs/log      tail a run's pipeline log
    POST /api/requirements  save the AI report requirements (any time)
    POST /api/handoff       prepare an AI report handoff folder
    GET  /api/handoff       the last handoff prepared

Run:
    pip install fastapi uvicorn
    python orchestration/api.py --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
from driver_schema import schema_for_ui, validate_options, default_options  # noqa: E402
from checkpoints import read_checkpoints, summarise  # noqa: E402
from mea_repo import (  # noqa: E402
    find_mea_repo, describe as describe_repo, report as report_repo,
    find_driver_python, check_python,
)
import native_picker  # noqa: E402
from watcher import (  # noqa: E402
    JobConfig, Watcher, DEFAULT_WORK_DIR, JOB_LABELS,
    has_finished_marker, list_h5,
)
import handoff  # noqa: E402

LOG = logging.getLogger("mea.api")
HERE = Path(__file__).resolve().parent
FRONTEND = HERE / "static" / "index.html"


class RingLogHandler(logging.Handler):
    """Keeps recent log records in memory so the UI can stream watcher activity.

    Each record gets a monotonic sequence number; the client polls with the last
    sequence it saw and receives only what is new.
    """

    def __init__(self, maxlen: int = 2000):
        super().__init__()
        self.records: deque = deque(maxlen=maxlen)
        self.seq = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.seq += 1
            self.records.append({
                "seq": self.seq,
                "time": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            })
        except Exception:  # noqa: BLE001 - logging must never raise
            pass

    def since(self, seq: int, limit: int = 500) -> list[dict]:
        return [r for r in self.records if r["seq"] > seq][-limit:]


LOG_RING = RingLogHandler()

app = FastAPI(title="MEA Pipeline Control", version="1.0")
# /api/status is ~30 KB of JSON every two seconds, usually over an SSH tunnel.
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

# --------------------------------------------------------------------------- #
# Process-wide state
# --------------------------------------------------------------------------- #
WORK_DIR = DEFAULT_WORK_DIR
CONFIG_PATH = WORK_DIR / "job.json"
_watcher: Optional[Watcher] = None
_events: list[dict] = []


def _record_event(kind: str, payload: dict) -> None:
    _events.append({"kind": kind, **payload})
    del _events[:-200]  # keep the last 200


def load_job_config() -> JobConfig:
    """Saved intent + this machine's environment, resolved now.

    The driver path is always taken from the repo detected at startup, never
    from the saved file: a config written before the repos were split, or on a
    different machine, must not pin an interpreter or driver that does not
    exist here.
    """
    cfg = None
    if CONFIG_PATH.exists():
        try:
            cfg = JobConfig.load(CONFIG_PATH)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Could not load %s (%s); using defaults", CONFIG_PATH, exc)
    if cfg is None:
        cfg = JobConfig()

    cfg.work_dir = str(WORK_DIR)
    # config.env can name the pipeline's interpreter; the UI still overrides it.
    if not cfg.driver_python and os.environ.get("MEA_DRIVER_PYTHON"):
        cfg.driver_python = os.environ["MEA_DRIVER_PYTHON"]
    repo = find_mea_repo(os.environ.get("MEA_REPO"))
    if repo:
        driver = repo / "run_pipeline_driver.py"
        if str(driver) != cfg.driver:
            LOG.info("Driver resolved to %s", driver)
        cfg.driver = str(driver)
    return cfg


_watcher_lock = threading.Lock()


def get_watcher() -> Watcher:
    """The one Watcher for this process.

    The lock is not ceremony. FastAPI runs sync endpoints in a thread pool and
    the UI fires several requests the moment the page loads, so an unguarded
    "if None: create" let two threads each build a Watcher. Two watchers means
    two scan loops walking the same directory, two StateStores writing the same
    watcher_state.tmp — which raced and lost entries, so runs vanished from the
    UI — and every log line printed twice. Double-checked under the lock.
    """
    global _watcher
    if _watcher is None:
        with _watcher_lock:
            if _watcher is None:
                _watcher = Watcher(load_job_config(), on_event=_record_event)
    return _watcher


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class ConfigPayload(BaseModel):
    watch_dir: str = ""
    driver_options: dict[str, Any] = {}
    h5_glob: str = "data.raw.h5"
    assay_subfolder: str = "Network"
    run_network: bool = True
    run_activity: bool = False
    activity_subfolder: str = "ActivityScan"
    activity_output_dir: str = ""
    activity_active_hz: float = 0.05
    activity_figures: bool = True
    max_concurrent_network: int = 1
    max_concurrent_activity: int = 2
    gpu_cooldown_seconds: int = 5
    queue_poll_seconds: int = 2
    settle_seconds: int = 600
    poll_seconds: int = 30
    require_finished_marker: bool = True
    skip_settle_for_existing: bool = False
    driver_python: str = ""
    ai_requirements: str = ""
    auto_handoff: bool = True
    logs_in_output: bool = True
    stage_locally: bool = False
    scratch_dir: str = ""
    stage_min_free_gb: int = 200
    dry_run: bool = False


class BrowsePayload(BaseModel):
    path: str = ""


class PickPayload(BaseModel):
    start: str = ""
    title: str = "Select folder"


class RunKeyPayload(BaseModel):
    path: str


class ResetAllPayload(BaseModel):
    # "failed" | "done" | "all" — what to forget in one go
    which: str = "failed"


class QueuePayload(BaseModel):
    folders: list[str] = []
    rerun: bool = False
    auto_handoff: Optional[bool] = None   # None = use the saved setting


# --------------------------------------------------------------------------- #
# Routes — schema & config
# --------------------------------------------------------------------------- #
@app.get("/api/schema")
def api_schema():
    return {"groups": schema_for_ui(), "defaults": default_options()}


def _runtime_env() -> dict:
    """Detect containerization so the UI can warn about container-vs-host paths."""
    in_container = (
        Path("/.dockerenv").exists()
        or os.environ.get("MEA_REPO", "").startswith("/MEA_Analysis")
    )
    repo = find_mea_repo(os.environ.get("MEA_REPO"))
    return {
        "mea_repo": describe_repo(repo),
        "in_container": in_container,
        "suggested_input": os.environ.get("MEA_INPUT_DIR"),
        "suggested_output": os.environ.get("MEA_OUTPUT_DIR"),
    }


@app.get("/api/env")
def api_env():
    return _runtime_env()


@app.get("/api/config")
def api_get_config():
    cfg = get_watcher().cfg
    env = _runtime_env()
    # First run inside a container: prefill the mount points so nobody types
    # host paths that don't exist in here.
    if not cfg.watch_dir and env["suggested_input"]:
        cfg.watch_dir = env["suggested_input"]
    if not cfg.driver_options.get("output_dir") and env["suggested_output"]:
        cfg.driver_options["output_dir"] = env["suggested_output"]
    return {
        "env": env,
        "watch_dir": cfg.watch_dir,
        "driver_options": cfg.driver_options,
        "h5_glob": cfg.h5_glob,
        "assay_subfolder": cfg.assay_subfolder,
        "run_network": cfg.run_network,
        "run_activity": cfg.run_activity,
        "activity_subfolder": cfg.activity_subfolder,
        "activity_output_dir": cfg.activity_output_dir,
        "activity_active_hz": cfg.activity_active_hz,
        "activity_figures": cfg.activity_figures,
        "max_concurrent_network": cfg.max_concurrent_network,
        "max_concurrent_activity": cfg.max_concurrent_activity,
        "gpu_cooldown_seconds": cfg.gpu_cooldown_seconds,
        "queue_poll_seconds": cfg.queue_poll_seconds,
        "settle_seconds": cfg.settle_seconds,
        "poll_seconds": cfg.poll_seconds,
        "require_finished_marker": cfg.require_finished_marker,
        "skip_settle_for_existing": cfg.skip_settle_for_existing,
        "driver_python": cfg.driver_python,
        "logs_in_output": cfg.logs_in_output,
        "stage_locally": cfg.stage_locally,
        "scratch_dir": cfg.scratch_dir,
        "stage_min_free_gb": cfg.stage_min_free_gb,
        "dry_run": cfg.dry_run,
        "work_dir": cfg.work_dir,
        "ai_requirements": cfg.ai_requirements,
        "auto_handoff": cfg.auto_handoff,
    }


@app.post("/api/config")
def api_set_config(payload: ConfigPayload):
    watcher = get_watcher()
    if watcher.is_running:
        raise HTTPException(409, "Stop the watcher before changing configuration.")

    opt_errors = validate_options(payload.driver_options)
    if opt_errors:
        raise HTTPException(400, {"errors": opt_errors})

    opts = default_options()
    opts.update(payload.driver_options)

    cfg = JobConfig(
        watch_dir=payload.watch_dir,
        driver_options=opts,
        h5_glob=payload.h5_glob,
        assay_subfolder=payload.assay_subfolder,
        run_network=payload.run_network,
        run_activity=payload.run_activity,
        activity_subfolder=payload.activity_subfolder,
        activity_output_dir=payload.activity_output_dir,
        activity_active_hz=payload.activity_active_hz,
        activity_figures=payload.activity_figures,
        max_concurrent_network=payload.max_concurrent_network,
        max_concurrent_activity=payload.max_concurrent_activity,
        gpu_cooldown_seconds=payload.gpu_cooldown_seconds,
        queue_poll_seconds=payload.queue_poll_seconds,
        settle_seconds=payload.settle_seconds,
        poll_seconds=payload.poll_seconds,
        require_finished_marker=payload.require_finished_marker,
        skip_settle_for_existing=payload.skip_settle_for_existing,
        driver_python=payload.driver_python,
        logs_in_output=payload.logs_in_output,
        stage_locally=payload.stage_locally,
        scratch_dir=payload.scratch_dir,
        stage_min_free_gb=payload.stage_min_free_gb,
        work_dir=str(WORK_DIR),
        dry_run=payload.dry_run,
        ai_requirements=payload.ai_requirements,
        auto_handoff=payload.auto_handoff,
    )
    errors = cfg.validate()
    if errors:
        raise HTTPException(400, {"errors": errors})

    cfg.save(CONFIG_PATH)
    global _watcher
    with _watcher_lock:
        # Stop the old one first. Replacing the reference does not stop its
        # scan loop: that thread keeps walking the watch directory and keeps
        # its own StateStore, so the process ends up with two watchers writing
        # the same state file. Saving config from the UI is the ordinary way to
        # reach this line, which made it the ordinary way to get two.
        #
        # stop() ends the scan loop but deliberately leaves running jobs alone
        # — a Kilosort run mid-flight should survive a settings change.
        old, _watcher = _watcher, None
        if old is not None and old.is_running:
            LOG.info("Configuration changed — stopping the previous watcher")
            old.stop()
        _watcher = Watcher(cfg, on_event=_record_event)

    # "detected" is only ever produced by a dry run, and it counts as claimed —
    # so a run marked that way would never be analyzed for real. Clear those
    # entries when leaving dry-run mode, otherwise turning the switch off
    # appears to do nothing.
    cleared = 0
    if not cfg.dry_run:
        for key, entry in list(_watcher.state.all().items()):
            if entry.get("status") == "detected":
                _watcher.state.reset(key)
                cleared += 1
        if cleared:
            LOG.info("Dry run disabled — cleared %d detected run(s) for real analysis", cleared)

    return {"ok": True, "saved_to": str(CONFIG_PATH), "cleared_detected": cleared}


# --------------------------------------------------------------------------- #
# Routes — helpers
# --------------------------------------------------------------------------- #
@app.post("/api/browse")
def api_browse(payload: BrowsePayload):
    """List subdirectories so the UI can offer a server-side path picker."""
    raw = payload.path.strip() or str(Path.home())
    p = Path(raw).expanduser()
    if not p.exists():
        raise HTTPException(404, f"Path does not exist: {p}")
    if not p.is_dir():
        p = p.parent
    try:
        entries = sorted(
            (c for c in p.iterdir() if c.is_dir() and not c.name.startswith(".")),
            key=lambda c: c.name.lower(),
        )
    except PermissionError:
        raise HTTPException(403, f"Permission denied: {p}")

    cfg = get_watcher().cfg
    items = []
    for c in entries:
        # One cached, depth-limited listing per folder answers all three
        # questions. This used to be up to four full rglob walks per child,
        # which over the NAS made the picker take minutes during a job.
        found = list_h5(c, cfg.h5_glob)
        recs = [r for r in found if not cfg.assay_subfolder or cfg.assay_subfolder in r.parts]
        rec = recs[0] if recs else (found[0] if found else None)
        items.append({
            "name": c.name,
            "path": str(c),
            "is_run": rec is not None,
            "recordings": len(recs) or (1 if rec else 0),
            "finished": (has_finished_marker(c, cfg.h5_glob, cfg.assay_subfolder,
                                             listing=found)
                         if rec is not None else None),
        })
    return {"path": str(p), "parent": str(p.parent) if p.parent != p else None, "entries": items}


class PythonPayload(BaseModel):
    python: str = ""


@app.post("/api/driver-python")
def api_driver_python(payload: PythonPayload):
    """Check whether an interpreter can actually run the pipeline.

    The orchestration virtualenv deliberately lacks pandas/torch/kilosort, so
    launching the driver with it fails at `import pandas`. This reports which
    dependencies a candidate interpreter is missing, before a run is started.
    """
    watcher = get_watcher()
    repo = Path(watcher.cfg.driver).parent if watcher.cfg.driver else None
    if payload.python:
        res = check_python(payload.python)
        res["source"] = "configured"
        return res
    return find_driver_python(repo)


@app.get("/api/picker")
def api_picker_status():
    """Whether a desktop folder chooser can be used on this machine."""
    return native_picker.describe()


@app.post("/api/picker")
def api_pick(payload: PickPayload):
    """Open the desktop folder chooser and return the chosen path.

    Blocks until the dialog is dismissed. The dialog appears on the *server's*
    display, so this is only useful when the browser is on the same machine.
    """
    info = native_picker.describe()
    if not info["available"]:
        raise HTTPException(400, info["reason"] or "No folder chooser available")
    LOG.info("Opening %s folder chooser…", info["tool"])
    path = native_picker.choose_directory(payload.start, payload.title)
    if not path:
        return {"cancelled": True, "path": None}
    LOG.info("Folder chosen: %s", path)
    return {"cancelled": False, "path": path, "is_dir": Path(path).is_dir()}


@app.post("/api/preview")
def api_preview(payload: ConfigPayload):
    """Show the exact command(s) the watcher will execute for a detected run.

    Mirrors the full payload — including which analyses are enabled — so the
    preview matches what actually runs. Returns one command per enabled
    analysis, since the two are dispatched independently.
    """
    import shlex

    opts = default_options()
    opts.update(payload.driver_options)
    cfg = JobConfig(
        watch_dir=payload.watch_dir,
        driver_options=opts,
        h5_glob=payload.h5_glob,
        assay_subfolder=payload.assay_subfolder,
        run_network=payload.run_network,
        run_activity=payload.run_activity,
        activity_subfolder=payload.activity_subfolder,
        activity_output_dir=payload.activity_output_dir,
        activity_active_hz=payload.activity_active_hz,
        activity_figures=payload.activity_figures,
        work_dir=str(WORK_DIR),
    )
    probe = Watcher(cfg, on_event=lambda *_: None, reconcile=False)

    # Never walk the whole input tree to draw a preview. Reuse what the live
    # watcher already found for the same folder; otherwise look at one
    # recording folder, which is all an example command needs.
    live = get_watcher()
    candidates: list = []
    if live.cfg.watch_dir == cfg.watch_dir and live._cand_cache:
        candidates = list(live._cand_cache[1])
    elif cfg.watch_dir and Path(cfg.watch_dir).is_dir():
        for child in sorted(Path(cfg.watch_dir).iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                jobs = probe.jobs_for(child)
                if jobs:
                    candidates = [(child, jobs)]
                    break
    sample, jobs = (candidates[0] if candidates
                    else (Path(payload.watch_dir or "/path/to") / "000000",
                          cfg.enabled_jobs()))

    commands = [
        {"job": job,
         "job_label": JOB_LABELS.get(job, job),
         "command": " ".join(shlex.quote(c) for c in probe.build_command(sample, job))}
        for job in jobs
    ]
    return {
        "detected_runs": [d.name for d, _ in candidates],
        "example_run": sample.name,
        "enabled_jobs": cfg.enabled_jobs(),
        "commands": commands,
        # Kept for older clients; first enabled analysis.
        "command": commands[0]["command"] if commands else "",
    }


# --------------------------------------------------------------------------- #
# Routes — watcher control & status
# --------------------------------------------------------------------------- #
@app.post("/api/watcher/start")
def api_start():
    watcher = get_watcher()
    errors = watcher.cfg.validate()
    if errors:
        raise HTTPException(400, {"errors": errors})
    watcher.start()
    return {"ok": True, "running": watcher.is_running}


@app.post("/api/watcher/stop")
def api_stop(cancel_running: bool = False):
    """Stop scanning, and optionally cancel work already in flight.

    Plain stop leaves running drivers alone, which is right when settings are
    being changed mid-run. It is wrong when the operator wants the machine
    quiet: the jobs carry on for hours and the only recourse was killing
    processes from a terminal — which orphans the per-well subprocesses and
    causes the stray-process problem.
    """
    watcher = get_watcher()
    if cancel_running:
        result = watcher.cancel_all()
        return {"ok": True, "running": watcher.is_running, **result}
    watcher.stop()
    return {"ok": True, "running": watcher.is_running, "cancelled": 0}


@app.get("/api/status")
def api_status():
    watcher = get_watcher()
    snap = watcher.snapshot()
    snap["events"] = _events[-25:]
    # None while the first directory scan is still running. Kept distinct from
    # [] so the UI can say "scanning" rather than "nothing found" — on a slow
    # network mount that first walk takes a minute or more.
    found = watcher.candidate_runs()
    snap["candidates"] = None if found is None else [c.name for c in found]
    snap["scanning"] = found is None
    # How many jobs a Start would resume, so the UI can say so beforehand
    # rather than the operator watching the whole previous queue reappear.
    snap["resumable"] = len(watcher.resumable())
    return snap


@app.get("/api/gpu")
def api_gpu(refresh: bool = False):
    """Whether spike sorting can actually run right now.

    The answer is cached after the first call because the probe starts a
    process and imports torch; pass ``?refresh=true`` after fixing the machine.
    """
    watcher = get_watcher()
    return watcher.check_gpu(force=refresh)


@app.post("/api/runs/reset")
def api_reset(payload: RunKeyPayload):
    """Forget a run so it can be processed again.

    State is keyed ``<folder>::<job>`` but the settle-window fingerprint cache is
    keyed by folder alone. Clearing only the state entry would leave a stale
    fingerprint whose timestamp already satisfies the settle window, so the run
    would be declared stable immediately instead of being re-observed.
    """
    watcher = get_watcher()
    watcher.state.reset(payload.path)
    folder = payload.path.split("::")[0]
    watcher._prints.pop(folder, None)
    watcher._prints.pop(payload.path, None)   # tolerate a bare folder path
    return {"ok": True, "cleared_fingerprint_for": folder}


@app.post("/api/runs/reset-all")
def api_reset_all(payload: ResetAllPayload):
    """Forget many runs at once, so a fresh start is one click.

    Anything still in flight is left alone: clearing a running job would let the
    watcher re-dispatch the same folder while the first process still holds the
    GPU. Those are reported back rather than silently skipped.
    """
    if payload.which not in ("failed", "done", "all"):
        raise HTTPException(400, f"Unknown selection: {payload.which}")

    watcher = get_watcher()
    in_flight = {"dispatched", "running", "queued", "detected"}
    cleared, skipped = [], []
    for key, entry in list(watcher.state.all().items()):
        status = entry.get("status")
        if status in in_flight:
            skipped.append({"run": entry.get("run") or key, "status": status})
            continue
        if payload.which != "all" and status != payload.which:
            continue
        watcher.state.reset(key)
        folder = key.split("::")[0]
        watcher._prints.pop(folder, None)
        cleared.append(entry.get("run") or key)

    LOG.info("Cleared %d run(s) [%s]%s", len(cleared), payload.which,
             f", {len(skipped)} still running" if skipped else "")
    return {"ok": True, "cleared": len(cleared), "runs": sorted(set(cleared)),
            "skipped": skipped}


@app.get("/api/runs/log")
def api_log(path: str, tail: int = 400):
    """Read a pipeline log.

    Restricted to the watcher's log directory. The UI is unauthenticated by
    design, so an unrestricted path parameter here would be an arbitrary
    file-read primitive for anyone who can reach the port.
    """
    watcher = get_watcher()
    # Logs may live in the work dir or beside the results, so several roots are
    # allowed — but still only these, never an arbitrary path.
    roots = []
    for candidate in (watcher.log_dir, watcher.cfg.output_dir, watcher.cfg.activity_out):
        if candidate:
            try:
                roots.append(Path(candidate).resolve())
            except OSError:
                pass
    try:
        p = Path(path).resolve(strict=True)
    except (OSError, RuntimeError):
        raise HTTPException(404, "Log not found")

    if not any(p == r or r in p.parents for r in roots):
        LOG.warning("Rejected log read outside %s: %s", roots, p)
        raise HTTPException(403, "Log path is outside the allowed log directories")
    if not p.is_file():
        raise HTTPException(404, "Log not found")

    lines = p.read_text(errors="ignore").splitlines()
    return {"path": str(p), "lines": lines[-tail:], "size": p.stat().st_size}


@app.get("/api/runs/checkpoints")
def api_checkpoints(path: str = "", tail: int = 0):
    """True per-well status, read from the pipeline's own checkpoint files.

    A subprocess exit code cannot distinguish "every well failed" from "one well
    hit an OOM and the rest are fine". The checkpoints can.
    """
    watcher = get_watcher()
    # The scratch root is searched too. While a run is staged on local disk its
    # checkpoints are written there, not to the output directory, so leaving it
    # out would blank the per-well view for exactly the run you are watching.
    roots = [Path(p) for p in (watcher.cfg.output_dir,
                               watcher.cfg.driver_options.get("checkpoint_dir"),
                               str(watcher._scratch_root())
                               if watcher.cfg.stage_locally else None) if p]
    if not roots:
        return {"summary": {"wells": 0}, "wells": [], "note": "No output directory configured"}

    folder = Path(path.split("::")[0]) if path else None
    rows = read_checkpoints(roots, folder)
    return {"summary": summarise(rows), "wells": rows,
            "searched": [str(r) for r in roots]}


# --------------------------------------------------------------------------- #
# Queue
# --------------------------------------------------------------------------- #
LAST_HANDOFF: dict = {"state": "idle"}
HANDOFF_LOCK = threading.Lock()


def _make_handoff(folders: Optional[list[str]] = None, label: str = "",
                  requirements: Optional[str] = None) -> dict:
    """Write an AI handoff folder for these input folders (all, if None)."""
    cfg = get_watcher().cfg
    out = cfg.output_dir
    if not out:
        raise ValueError("No output directory is configured.")
    # One project per handoff: its activity scans and its handoff folder both
    # live under <output>/<project>/. Folders from several projects fall back
    # to the output root.
    probe_dirs = folders or ([cfg.watch_dir.rstrip("/") + "/x"] if cfg.watch_dir else [])
    projects = {JobConfig.project_of(f) for f in probe_dirs}
    if len(projects) == 1 and probe_dirs:
        act = cfg.activity_out_for(probe_dirs[0])
        root = cfg.project_dir(probe_dirs[0])
        # Older outputs kept scans in <output>/ActivityScan.
        if not (act and Path(act).is_dir()) and (Path(out) / "ActivityScan").is_dir():
            act = str(Path(out) / "ActivityScan")
    else:
        act, root = str(Path(out) / "ActivityScan"), Path(out)
    with HANDOFF_LOCK:
        LAST_HANDOFF.clear()
        LAST_HANDOFF.update({"state": "running", "started": time.time(), "label": label})
    try:
        res = handoff.generate(
            Path(out), cfg.ai_requirements if requirements is None else requirements,
            watch_dir=cfg.watch_dir,
            activity_dir=Path(act) if act and Path(act).is_dir() else None,
            folders=folders, label=label, handoff_root=root)
    except Exception as exc:  # noqa: BLE001
        with HANDOFF_LOCK:
            LAST_HANDOFF.update({"state": "error", "error": str(exc), "finished": time.time()})
        raise
    with HANDOFF_LOCK:
        LAST_HANDOFF.update({"state": "done", **res, "finished": time.time()})
    return res


def _batch_handoff(batch: dict) -> None:
    """Prepare the AI handoff for a finished batch. Runs on its own thread."""
    folders = sorted({k.split("::")[0] for k in batch.get("keys", [])})
    try:
        res = _make_handoff(folders, label=batch["id"])
        LOG.info("Batch %s: AI handoff ready — %s", batch["id"], res["prompt"])
    except Exception:  # noqa: BLE001
        LOG.exception("Batch %s: could not prepare the AI handoff", batch["id"])


@app.post("/api/queue/inspect")
def api_queue_inspect(payload: QueuePayload):
    """What queueing these folders would do, before anything is started."""
    return {"folders": get_watcher().inspect_folders(payload.folders)}


@app.post("/api/queue")
def api_queue(payload: QueuePayload):
    if not payload.folders:
        raise HTTPException(400, "Select at least one folder.")
    watcher = get_watcher()
    errors = watcher.cfg.validate()
    if errors:
        raise HTTPException(400, {"errors": errors})

    auto = watcher.cfg.auto_handoff if payload.auto_handoff is None else payload.auto_handoff
    res = watcher.queue_folders(
        payload.folders, rerun=payload.rerun,
        on_complete=_batch_handoff if auto else None)
    if not res["queued"]:
        # Nothing to do is a useful answer, not an error — but say why.
        reasons = sorted({s.get("reason", "") for s in res["skipped"]})
        raise HTTPException(409, "Nothing was queued: " + "; ".join(reasons))
    return res


@app.get("/api/queue")
def api_queue_status():
    with HANDOFF_LOCK:
        last = dict(LAST_HANDOFF)
    return {"batches": get_watcher().batches(), "handoff": last}


@app.get("/api/logs")
def api_logs(since: int = 0, limit: int = 500):
    """Live watcher activity — polled by the UI with the last seq it received."""
    return {"lines": LOG_RING.since(since, limit), "last_seq": LOG_RING.seq}


# --------------------------------------------------------------------------- #
# AI report handoff
# --------------------------------------------------------------------------- #
class RequirementsPayload(BaseModel):
    text: str = ""
    auto_handoff: Optional[bool] = None


class HandoffPayload(BaseModel):
    folders: list[str] = []      # input folders to cover; empty = everything
    label: str = ""


@app.post("/api/requirements")
def api_requirements(payload: RequirementsPayload):
    """Save the report requirements. Allowed while running — it is not a
    pipeline setting, and the text box should never be locked."""
    watcher = get_watcher()
    watcher.cfg.ai_requirements = payload.text
    if payload.auto_handoff is not None:
        watcher.cfg.auto_handoff = payload.auto_handoff
    watcher.cfg.save(CONFIG_PATH)
    return {"ok": True, "chars": len(payload.text)}


@app.post("/api/handoff")
def api_handoff(payload: HandoffPayload):
    label = "".join(ch for ch in payload.label if ch.isalnum() or ch in "-_")[:40]
    try:
        return _make_handoff(payload.folders or None, label=label)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/handoff")
def api_handoff_status():
    with HANDOFF_LOCK:
        return dict(LAST_HANDOFF)


# --------------------------------------------------------------------------- #
# Frontend
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    if not FRONTEND.exists():
        return JSONResponse({"error": f"Frontend not found at {FRONTEND}"}, status_code=500)
    # Stamp app.js with its mtime so a rebuilt UI is never served from cache.
    app_js = FRONTEND.parent / "app.js"
    version = str(int(app_js.stat().st_mtime)) if app_js.exists() else "0"
    return HTMLResponse(FRONTEND.read_text().replace("__APP_VERSION__", version),
                        headers={"Cache-Control": "no-cache"})


def main() -> None:
    global WORK_DIR, CONFIG_PATH
    p = argparse.ArgumentParser(description="MEA pipeline control UI server")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR,
                   help="Where job config, watcher state, and logs are written")
    p.add_argument("--mea-repo", default=None,
                   help="Path to the MEA-Analysis checkout (else $MEA_REPO, else ../MEA-Analysis)")
    p.add_argument("--strict", action="store_true",
                   help="Refuse to start if the MEA repo is missing or its options have drifted")
    a = p.parse_args()

    WORK_DIR = a.work_dir
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH = WORK_DIR / "job.json"

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    # Capture watcher + API activity for the UI's live log panel.
    LOG_RING.setLevel(logging.INFO)
    for name in ("mea.watcher", "mea.api"):
        logging.getLogger(name).addHandler(LOG_RING)

    if not FRONTEND.exists():
        raise SystemExit(f"Frontend missing: {FRONTEND}\n"
                         "Expected orchestration/static/index.html next to api.py.")

    # Fail fast with a clear message if the port is taken.
    import socket
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind((a.host, a.port))
    except OSError as exc:
        raise SystemExit(f"Cannot bind {a.host}:{a.port} — {exc}\n"
                         f"Another process may be using it. Try --port {a.port + 1}.")
    finally:
        probe.close()

    url_host = "localhost" if a.host in ("0.0.0.0", "127.0.0.1") else a.host
    repo = find_mea_repo(a.mea_repo)
    if repo:
        os.environ["MEA_REPO"] = str(repo)
    report_repo(repo, strict=a.strict)
    LOG.info("Work dir: %s", WORK_DIR)
    LOG.info("=" * 58)
    LOG.info("  Open this in your browser:  http://%s:%s", url_host, a.port)
    LOG.info("  (do not open index.html directly — it must be served)")
    LOG.info("=" * 58)

    import uvicorn
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
