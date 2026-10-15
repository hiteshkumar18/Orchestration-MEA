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
    POST /api/runs/hold     take runs off the queue, keep them for later
    POST /api/queue/reset   clear the queue: stop everything unfinished, hold it
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
    if kind == "date_finished" and payload.get("folder"):
        # A date the watcher picked up by itself; batches report through
        # their own hook. Never on the job's thread: a report takes a while.
        threading.Thread(target=_date_handoff, args=(payload["folder"],),
                         name="mea-date-report", daemon=True).start()


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
    nwb_convert: bool = False
    nwb_python: str = ""
    nwb_compression: str = "gzip"
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


class HoldPayload(BaseModel):
    paths: list[str] = []      # state keys, "<folder>::<job>"


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
        "nwb_convert": cfg.nwb_convert,
        "nwb_python": cfg.nwb_python,
        "nwb_compression": cfg.nwb_compression,
    }


@app.post("/api/config")
def api_set_config(payload: ConfigPayload):
    watcher = get_watcher()
    if watcher.is_running:
        raise HTTPException(409, "Stop the watcher before changing configuration.")
    # Saving replaces the watcher. Jobs still in flight belong to the old one:
    # the new one would mark them interrupted while they are in fact running,
    # and the same folder could then be started a second time on top of them.
    # The settings page is already locked while analyses run; this holds the
    # same line for anything else that calls the API.
    busy = sorted({e.get("run") or k for k, e in watcher.state.all().items()
                   if e.get("status") in ("dispatched", "queued", "running")})
    if busy:
        raise HTTPException(409, "Settings cannot be changed while analyses are running "
                                 f"({', '.join(busy)}). Wait for them to finish, or stop them first.")

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
        nwb_convert=payload.nwb_convert,
        nwb_python=payload.nwb_python,
        nwb_compression=payload.nwb_compression if payload.nwb_compression in ("gzip", "maxwell") else "gzip",
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
        nwb_convert=payload.nwb_convert,
        nwb_python=payload.nwb_python,
        nwb_compression=payload.nwb_compression,
        driver_python=payload.driver_python,
        stage_locally=payload.stage_locally,
        scratch_dir=payload.scratch_dir,
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
def api_start(hold_interrupted: bool = False):
    """Start watching. Interrupted runs are picked up again unless
    ``hold_interrupted`` asks for them to be put on hold first."""
    watcher = get_watcher()
    errors = watcher.cfg.validate()
    if errors:
        raise HTTPException(400, {"errors": errors})
    watcher.start(hold_interrupted=hold_interrupted)
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
    # Each row's run in the history, so the UI can open its detail page.
    if watcher.history is not None:
        for r in snap.get("runs", []):
            try:
                r["run_id"] = watcher.history.current_run_id(r["path"])
            except Exception:  # noqa: BLE001
                r["run_id"] = None
    return snap


# --------------------------------------------------------------------------- #
# Dashboard: history, run detail, system health, overview
# --------------------------------------------------------------------------- #
from rundetail import (estimate, expected_wells_cached, outputs as run_outputs,  # noqa: E402
                       parse_log_file)
from history import HEARTBEAT as RUN_HEARTBEAT, TERMINAL as RUN_TERMINAL  # noqa: E402
from monitor import SystemMonitor  # noqa: E402

_monitor: Optional[SystemMonitor] = None
_monitor_lock = threading.Lock()


def get_monitor() -> SystemMonitor:
    global _monitor
    with _monitor_lock:
        if _monitor is None:
            def paths() -> dict[str, str]:
                w = get_watcher()
                cfg = w.cfg
                return {"Output disk": cfg.output_dir or "",
                        "Fast disk": str(w._scratch_root().parent) if cfg.stage_locally else "",
                        "Recordings (NAS)": cfg.watch_dir or "",
                        "Work folder": str(WORK_DIR)}
            _monitor = SystemMonitor(paths, own_pids=lambda: set(get_watcher()._own_pids))
        return _monitor


def _seconds_since(iso: Optional[str]) -> Optional[float]:
    if not iso:
        return None
    try:
        return time.time() - datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _live_detail(status: Optional[str], detail: Optional[str]) -> Optional[str]:
    """The watcher's current note on a run in flight. Why it was queued stops
    being news once it is running."""
    if status not in ("running", "dispatched", "queued") or not detail:
        return None
    if status == "running" and (detail.startswith("queued") or RUN_HEARTBEAT.match(detail)):
        return None
    return detail


def _run_detail(run: dict, light: bool = False) -> dict:
    """A history run plus what its log, the recordings and the output folder say."""
    w = get_watcher()
    status = run.get("status")
    finished = status in RUN_TERMINAL
    is_current = w.history is not None and w.history.current_run_id(run["key"]) == run["id"]
    state = w.state.get(run["key"]) if is_current else {}
    parsed = parse_log_file(run.get("log"), run.get("job") or "network", finished)
    elapsed = run.get("duration_s")
    if elapsed is None and status in ("running",):
        elapsed = _seconds_since(run.get("started_at"))
    progress = None
    if (run.get("job") == "network") and parsed and "counts" in parsed:
        exp = expected_wells_cached(run["folder"], w.cfg.assay_subfolder or "Network")
        progress = estimate(parsed, (exp or {}).get("total") or 0, elapsed)
        progress["expected_known"] = exp is not None
    out = {**run, "is_current": is_current, "elapsed_s": round(elapsed) if elapsed else elapsed,
           "live_detail": _live_detail(status, state.get("detail")),
           "last_output_age_s": round(time.time() - parsed["log_mtime"]) if parsed else None,
           "progress": progress}
    if light:
        out["counts"] = (parsed or {}).get("counts")
        out["conversion_summary"] = (parsed or {}).get("conversion_summary")
        return out
    out["log_summary"] = parsed
    try:
        reports = api_reports()["reports"]
    except Exception:  # noqa: BLE001
        reports = []
    out["outputs"] = run_outputs(w.cfg.output_dir, run["folder"], run.get("job") or "network",
                                 run.get("log"), reports)
    return out


@app.get("/api/history")
def api_history(project: str = "", job: str = "", status: str = "", date: str = "",
                limit: int = 50, offset: int = 0):
    w = get_watcher()
    if w.history is None:
        return {"total": 0, "runs": [], "projects": [], "unavailable": True}
    return w.history.list(project=project, job=job, status=status, date=date,
                          limit=max(1, min(limit, 500)), offset=max(0, offset))


@app.get("/api/history/{run_id}")
def api_history_run(run_id: str):
    w = get_watcher()
    run = w.history.get(run_id) if w.history is not None else None
    if not run:
        raise HTTPException(404, "No such run")
    return _run_detail(run)


@app.get("/api/system")
def api_system():
    return get_monitor().snapshot()


@app.get("/api/overview")
def api_overview():
    """Everything the dashboard landing view needs, in one request."""
    w = get_watcher()
    snap = w.snapshot()
    runs = snap.get("runs", [])
    running, attention = [], []
    stall_min = int(getattr(w.cfg, "stall_minutes", 120) or 0)      # 0: watchdog off
    stall_s = max(60, (stall_min or 120) * 60)
    hist = w.history
    for r in runs:
        rid = hist.current_run_id(r["path"]) if hist else None
        if r.get("status") == "running" and rid:
            d = _run_detail(hist.get(rid), light=True)
            running.append(d)
            age = d.get("last_output_age_s")
            if age is not None and age > stall_s / 2:
                attention.append({"level": "warn", "kind": "quiet", "run_id": rid,
                                  "project": d["project"], "date": d["date"], "job": d["job"],
                                  "text": f"No new log output for {age // 60} min — may be stuck"
                                          + (f" (stopped automatically after {stall_min} min)."
                                             if stall_min else ".")})
        elif r.get("status") == "failed":
            attention.append({"level": "bad", "kind": "failed", "run_id": rid,
                              "project": Path(r["folder"]).parent.name, "date": r["run"],
                              "job": r.get("job"),
                              "text": (r.get("error") or "Failed").splitlines()[0][:200]})
    sysw = (get_monitor().snapshot().get("warnings") or [])
    for x in sysw:
        attention.append({**x, "kind": "system"})
    recent = hist.list(status="done,failed,interrupted", limit=10)["runs"] if hist else []
    counts: dict[str, int] = {}
    for r in runs:
        counts[r.get("status") or "unknown"] = counts.get(r.get("status") or "unknown", 0) + 1
    return {"running": running, "attention": attention, "recent": recent, "counts": counts,
            "watching": snap.get("running"), "active_jobs": snap.get("active_jobs"),
            "limits": snap.get("limits")}


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
    if watcher.history is not None:
        watcher.history.close_open(payload.path, "cleared by hand")
    folder = payload.path.split("::")[0]
    watcher._prints.pop(folder, None)
    watcher._prints.pop(payload.path, None)   # tolerate a bare folder path
    return {"ok": True, "cleared_fingerprint_for": folder}


@app.post("/api/runs/hold")
def api_hold(payload: HoldPayload):
    """Take runs off the queue and keep them for later (status "held").

    Waiting runs leave the queue, running ones are stopped, interrupted ones
    are marked. A held run starts again only when its folder is queued again.
    """
    if not payload.paths:
        raise HTTPException(400, "Choose at least one run.")
    return {"ok": True, **get_watcher().hold(payload.paths)}


@app.post("/api/queue/reset")
def api_queue_reset():
    """Clear the queue: stop watching, stop running analyses, and put every
    unfinished run on hold. Finished results are not touched."""
    return {"ok": True, **get_watcher().reset_queue()}


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

    Restricted to the watcher's log directories and the logs of runs in the
    history. The UI is unauthenticated by
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

    # A run's own log stays readable after the output folder setting changes:
    # the history recorded exactly which file each run wrote.
    known = watcher.history is not None and watcher.history.knows_log(path, str(p))
    if not known and not any(p == r or r in p.parents for r in roots):
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
    if folder is not None:
        # The pipeline writes a date folder's wells to <output>/<project>/<date>
        # (and a staged run to <scratch>/<project>/<date>). Searching only
        # there turns a whole-disk walk — ~55 s with two projects on a busy
        # disk — into a read of one folder. Falls back to every root when
        # the layout is different.
        project, date = folder.parent.name, folder.name
        narrowed = []
        for r in roots:
            for cand in (r / project / date, r / project / date / project / date):
                if cand.is_dir():
                    narrowed.append(cand)
        if narrowed:
            roots = narrowed
    rows = read_checkpoints(roots, folder)
    return {"summary": summarise(rows), "wells": rows,
            "searched": [str(r) for r in roots]}


# --------------------------------------------------------------------------- #
# Queue
# --------------------------------------------------------------------------- #
LAST_HANDOFF: dict = {"state": "idle"}
HANDOFF_LOCK = threading.Lock()
# One package at a time: each runs the report builder, which takes a minute
# or so per date and reads every result file of those dates.
HANDOFF_BUILD = threading.Lock()
REPORT_SCRIPT = HERE / "report" / "make_report.py"


def _report_projects(folders: Optional[list[str]]) -> dict[Path, Optional[list[str]]]:
    """Project results folder -> dates to report (None: every finished date)."""
    cfg = get_watcher().cfg
    out = cfg.output_dir
    if not out or not Path(out).is_dir():
        raise ValueError("There is no results folder yet. Set 'Results go to' in Settings "
                         "and analyse something first.")
    plan: dict[Path, Optional[list[str]]] = {}
    if folders:
        for f in folders:
            plan.setdefault(cfg.project_dir(f), []).append(Path(f).name)
        plan = {p: sorted(set(d)) for p, d in plan.items() if p and p.is_dir()}
    else:
        plan = {p: None for p in sorted(Path(out).iterdir()) if make_report_is_project(p)}
    if not plan:
        raise ValueError("There are no results to report yet.")
    return plan


def make_report_is_project(path: Path) -> bool:
    """Same test as the report command (report/make_report.py: is_project_dir)."""
    import re
    date = re.compile(r"^\d{6}$")
    if not path.is_dir() or path.name in ("report_tools", "_report_tools", "ActivityScan"):
        return False
    try:
        if any(date.match(x.name) for x in path.iterdir() if x.is_dir()):
            return True
        act = path / "ActivityScan"
        return act.is_dir() and any(date.match(x.name) for x in act.iterdir() if x.is_dir())
    except OSError:
        return False


def _build_package(pdir: Path, dates: Optional[list[str]], requirements: str,
                   label: str = "") -> dict:
    """Run the standard report for one project, then write PROMPT.md into it."""
    import json as _json
    import subprocess
    cfg = get_watcher().cfg
    cmd = [cfg.resolve_driver_python(), str(REPORT_SCRIPT), "--project-dir", str(pdir)]
    # Dates named by a finished batch are reported as they are, even if one of
    # their analyses failed; "everything" leaves out dates still in progress.
    cmd += ["--dates", *dates, "--allow-unfinished"] if dates else ["--all"]
    if label:
        cmd += ["--label", label]
    if requirements.strip():
        req = WORK_DIR / "report_requirements.txt"
        req.write_text(requirements)
        cmd += ["--requirements", f"@{req}"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ), timeout=6 * 3600)
    out = r.stdout
    i = out.rfind("\n{")
    blob = out[i + 1:] if i >= 0 else (out if out.startswith("{") else "")
    try:
        res = _json.loads(blob)
    except ValueError:
        tail = (r.stderr or r.stdout).strip().splitlines()[-3:]
        raise RuntimeError(f"{pdir.name}: the report could not be made — " + " / ".join(tail))
    folder = Path(res["folder"])
    input_dir = ""
    try:
        man = _json.loads((folder / "MANIFEST.json").read_text())
        input_dir = man.get("input_dir_read_only") or ""
    except (OSError, ValueError):
        pass
    prompt = handoff.write_prompt(
        folder, project=pdir.name, dates=res["dates"], network_wells=res["network_wells"],
        activity_runs=res["activity_runs"], built=res["built"], results_dir=str(pdir),
        input_dir=input_dir or cfg.watch_dir)
    return {"project": pdir.name, "dates": res["dates"], "dir": str(folder),
            "prompt": str(prompt), "report": res["report"], "report_dir": str(folder / "report"),
            "built": res["built"], "network_wells": res["network_wells"],
            "activity_runs": res["activity_runs"],
            "instruction": f"cd {folder} && claude \"Read PROMPT.md and do what it says.\""}


def _make_handoff(folders: Optional[list[str]] = None, label: str = "",
                  requirements: Optional[str] = None) -> dict:
    """Build the standard report and a Claude package for these input folders
    (every finished date of every project, if None). One package per project."""
    cfg = get_watcher().cfg
    plan = _report_projects(folders)
    req = cfg.ai_requirements if requirements is None else requirements
    with HANDOFF_BUILD:
        with HANDOFF_LOCK:
            LAST_HANDOFF.clear()
            LAST_HANDOFF.update({"state": "running", "started": time.time(), "label": label,
                                 "projects": [p.name for p in plan]})
        packages, errors = [], []
        for pdir, dates in plan.items():
            try:
                packages.append(_build_package(pdir, dates, req, label))
                LOG.info("Report ready for %s: %s", pdir.name, packages[-1]["report"])
            except Exception as exc:  # noqa: BLE001
                LOG.error("Report for %s failed: %s", pdir.name, exc)
                errors.append(str(exc))
        res = {**(packages[0] if packages else {}), "packages": packages, "errors": errors,
               "network_wells": sum(p["network_wells"] for p in packages),
               "activity_runs": sum(p["activity_runs"] for p in packages)}
        with HANDOFF_LOCK:
            LAST_HANDOFF.update({"state": "done" if packages else "error",
                                 "error": "; ".join(errors) or None, **res,
                                 "finished": time.time()})
    if not packages:
        raise RuntimeError("; ".join(errors) or "Nothing was built.")
    return res


def _batch_handoff(batch: dict) -> None:
    """Report a finished batch. Runs on its own thread."""
    folders = sorted({k.split("::")[0] for k in batch.get("keys", [])})
    try:
        res = _make_handoff(folders)
        LOG.info("Batch %s: report and Claude package ready — %s", batch["id"], res["prompt"])
    except Exception:  # noqa: BLE001
        LOG.exception("Batch %s: could not make the report", batch["id"])


def _date_handoff(folder: str) -> None:
    """Report a date the watcher analysed on its own (not part of a batch)."""
    if not get_watcher().cfg.auto_handoff:
        return
    try:
        res = _make_handoff([folder])
        LOG.info("%s: report and Claude package ready — %s", Path(folder).name, res["prompt"])
    except Exception:  # noqa: BLE001
        LOG.exception("%s: could not make the report", Path(folder).name)


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
    """Start building reports and Claude packages; poll GET /api/handoff.

    In the background: a report takes a minute or so per date, and "every
    date" can be many minutes."""
    label = "".join(ch for ch in payload.label if ch.isalnum() or ch in "-_")[:40]
    folders = payload.folders or None
    try:
        _report_projects(folders)                 # fail now if there is nothing to do
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if HANDOFF_BUILD.locked():
        raise HTTPException(409, "A report is already being made. Wait for it to finish.")

    def run():
        try:
            _make_handoff(folders, label=label)
        except Exception:  # noqa: BLE001 — recorded in LAST_HANDOFF
            LOG.exception("Report package failed")
    with HANDOFF_LOCK:
        LAST_HANDOFF.clear()
        LAST_HANDOFF.update({"state": "running", "started": time.time(), "label": label})
    threading.Thread(target=run, name="mea-report", daemon=True).start()
    return {"state": "running"}


# --------------------------------------------------------------------------- #
# Finished reports (read-only)
# --------------------------------------------------------------------------- #
def _report_files() -> list[Path]:
    """report.html files written into handoff folders under the output dir."""
    out = get_watcher().cfg.output_dir
    if not out or not Path(out).is_dir():
        return []
    return sorted(Path(out).glob("*/AI_HANDOFF/*/report/report.html")) + \
        sorted(Path(out).glob("AI_HANDOFF/*/report/report.html"))


@app.get("/api/reports")
def api_reports():
    """The newest report for each recording folder, keyed project/date.

    Handoff folders are named <stamp>_<label>; the label is the date for
    per-date handoffs. Older handoffs for the same date are superseded.
    """
    latest: dict[str, dict] = {}
    for f in _report_files():
        hdir = f.parent.parent
        stamp, _, label = hdir.name.partition("_")
        stamp2, _, label2 = label.partition("_")
        if stamp2.isdigit():                      # <date>_<time>_<label>
            stamp, label = f"{stamp}_{stamp2}", label2
        project = hdir.parent.parent.name if hdir.parent.parent != Path(get_watcher().cfg.output_dir) else ""
        key = f"{project}/{label}"
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if key not in latest or mtime > latest[key]["mtime"]:
            latest[key] = {"project": project, "label": label, "path": str(f),
                           "built": datetime.fromtimestamp(mtime).isoformat(timespec="minutes"),
                           "mtime": mtime}
    return {"reports": sorted(latest.values(), key=lambda r: (r["project"], r["label"]))}


@app.get("/api/reports/view")
def api_report_view(path: str):
    """Serve one report.html — only files that _report_files() lists."""
    allowed = {str(f.resolve()) for f in _report_files()}
    try:
        p = Path(path).resolve(strict=True)
    except (OSError, RuntimeError):
        raise HTTPException(404, "Report not found")
    if str(p) not in allowed:
        raise HTTPException(403, "Not a report written by this tool")
    return FileResponse(p, media_type="text/html")


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
    # The report command asks this server whether a date has finished; the
    # report_tools launcher written into the results folder passes it on.
    os.environ["MEA_STATUS_URL"] = f"http://127.0.0.1:{a.port}/api/status"

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
