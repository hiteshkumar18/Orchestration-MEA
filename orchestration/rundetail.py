"""
What happened inside one run, for the dashboard's run detail page.

* parse_job_log  — per-well progress and outcomes, and NWB conversion steps,
  read from a Network job's log (the driver's format, which the NWB route
  writes too) or an activity-scan log.
* expected_wells — how many wells a date folder's recordings hold (progress and
  time-left estimates).
* outputs        — what a run produced: results, NWB files, scans, reports.

Read-only. Standard library + h5py (already a dependency).
"""

from __future__ import annotations

import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

TS = re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")
PROCESSING = re.compile(r"Processing : (\S+) recording : \S+ well_id : (well\d+)")
COMPLETE = re.compile(r"Processing Complete for (well\d+)")
FAILED = re.compile(r"Subprocess failed for (well\d+)")
CRITICAL = re.compile(r"CRITICAL FAILURE in (well\d+): (.*)")
SPIKES = re.compile(r"Detected (\d+) total spikes")
PHASE = re.compile(r"--- \[Phase ([^\]]+)\] (.+?) ---")
NWB_CONVERTED = re.compile(r"NWB: converted (\S+?)/(\S+?)/(well\d+) -> \S+ \(.*?, (\d+) s\)")
NWB_REUSED = re.compile(r"NWB: reused \S+/(\S+?)/Network/(\S+?)/(well\d+)\.nwb")
NWB_FAILED = re.compile(r"NWB: NWB conversion failed for (well\d+) in (\S+): (.*)")
NWB_DONE = re.compile(r"NWB: done in (\d+) s: (\d+) converted, (\d+) reused, (\d+) failed")
DRIVER_DONE = re.compile(r"Pipeline driver completed in ([\d.]+) seconds")
ACT_WROTE = re.compile(r"wrote (\S+/ActivityScan/\S+)")
ACT_DONE = re.compile(r"Done — (\d+) run\(s\), (\d+) well\(s\), (\d+) flagged")


def _ts(line: str) -> Optional[str]:
    m = TS.match(line)
    return m.group(1) if m else None


def _secs(a: Optional[str], b: Optional[str]) -> Optional[float]:
    if not a or not b:
        return None
    try:
        f = "%Y-%m-%d %H:%M:%S"
        return (datetime.strptime(b, f) - datetime.strptime(a, f)).total_seconds()
    except ValueError:
        return None


def _chip_run(path: str) -> tuple[str, str]:
    p = path.rstrip("/").split("/")
    return (p[-4], p[-2]) if len(p) >= 4 else ("", "")


def parse_job_log(text: str, finished: bool = False) -> dict[str, Any]:
    """Per-well rows and conversion steps from a Network job log.

    `finished`: the job has ended, so a well still marked running did not finish.
    """
    wells: dict[tuple, dict] = {}
    order: list[tuple] = []
    conv: list[dict] = []
    cur = None
    last_ts = None
    conv_summary = None
    driver_seconds = None
    route = "raw"
    for line in text.splitlines():
        t = _ts(line)
        if t:
            last_ts = t
        if "NWB route:" in line:
            route = "nwb"
        m = NWB_CONVERTED.search(line)
        if m:
            conv.append({"chip": m.group(1), "run": m.group(2), "well": m.group(3),
                         "outcome": "converted", "seconds": int(m.group(4)), "time": t})
            continue
        m = NWB_REUSED.search(line)
        if m:
            conv.append({"chip": m.group(1), "run": m.group(2), "well": m.group(3),
                         "outcome": "reused", "seconds": 0, "time": t})
            continue
        m = NWB_FAILED.search(line)
        if m:
            chip, run = _chip_run(m.group(2))
            conv.append({"chip": chip, "run": run, "well": m.group(1), "outcome": "failed",
                         "reason": m.group(3)[:300], "time": t})
            continue
        m = NWB_DONE.search(line)
        if m:
            conv_summary = {"seconds": int(m.group(1)), "converted": int(m.group(2)),
                            "reused": int(m.group(3)), "failed": int(m.group(4))}
            continue
        m = PROCESSING.search(line)
        if m:
            chip, run = _chip_run(m.group(1))
            cur = (chip, run, m.group(2))
            if cur not in wells:
                order.append(cur)
            wells[cur] = {"chip": chip, "run": run, "well": m.group(2), "started": t or last_ts,
                          "finished": None, "outcome": "running", "phase": "Starting",
                          "spikes": None, "reason": None, "recording": m.group(1)}
            continue
        if cur is None:
            m = DRIVER_DONE.search(line)
            if m:
                driver_seconds = float(m.group(1))
            continue
        w = wells[cur]
        m = PHASE.search(line)
        if m:
            w["phase"] = f"{m.group(2)}"
        m = SPIKES.search(line)
        if m:
            w["spikes"] = int(m.group(1))
            if w["spikes"] == 0:
                w["silent"] = True
        if "returned error: no_spikes" in line:
            w["silent"] = True
        m = CRITICAL.search(line)
        if m and m.group(1) == w["well"]:
            w["reason"] = m.group(2).strip()[:300]
        m = COMPLETE.search(line)
        if m and m.group(1) == w["well"]:
            w["finished"] = last_ts
            w["outcome"] = "silent" if w.get("silent") else "complete"
        m = FAILED.search(line)
        if m and m.group(1) == w["well"]:
            w["finished"] = last_ts
            why = w.get("reason") or ""
            w["outcome"] = "not_recorded" if re.search(r"stream_id well\d+ is not in", why) else "failed"
        m = DRIVER_DONE.search(line)
        if m:
            driver_seconds = float(m.group(1))
    rows = []
    for k in order:
        w = wells[k]
        if w["outcome"] == "running" and finished:
            w["outcome"] = "stopped"
            w["reason"] = w["reason"] or "stopped without an error message"
        w["seconds"] = _secs(w["started"], w["finished"])
        w.pop("silent", None)
        rows.append(w)
    for c in conv:
        if c["outcome"] == "failed" and re.search(r"stream_id|is not in", c.get("reason", "")):
            c["outcome"] = "not_recorded"
    counts: dict[str, int] = {}
    for w in rows:
        counts[w["outcome"]] = counts.get(w["outcome"], 0) + 1
    return {"route": route, "wells": rows, "counts": counts, "conversion": conv,
            "conversion_summary": conv_summary, "driver_seconds": driver_seconds}


def parse_activity_log(text: str) -> dict[str, Any]:
    wrote = [m.group(1) for m in ACT_WROTE.finditer(text)]
    m = ACT_DONE.search(text)
    return {"chips": [p.rstrip("/").split("/")[-2] for p in wrote],
            "summary": ({"runs": int(m.group(1)), "wells": int(m.group(2)), "flagged": int(m.group(3))}
                        if m else None)}


# --------------------------------------------------------------------------- #
# Expected wells
# --------------------------------------------------------------------------- #
_expected: dict[str, tuple[float, dict]] = {}
_exp_lock = threading.Lock()


def expected_wells(folder: str, assay: str = "Network", h5_glob: str = "data.raw.h5",
                   max_age: float = 3600) -> dict[str, Any]:
    """Wells the folder's recordings hold: {'total': n, 'by_recording': {...}}.

    Reads only each file's 'wells' group names. Cached: recordings do not
    change once analysed, and the NAS can be slow."""
    with _exp_lock:
        hit = _expected.get(folder)
        if hit and time.time() - hit[0] < max_age:
            return hit[1]
    import h5py
    by: dict[str, int] = {}
    base = len(Path(folder).parts)
    for cur, dirs, files in os.walk(folder):
        if len(Path(cur).parts) - base >= 6:
            dirs[:] = []
        if h5_glob in files and assay in Path(cur).parts:
            p = Path(cur) / h5_glob
            try:
                with h5py.File(p, "r") as f:
                    n = len(f["wells"].keys()) if "wells" in f else 1
            except Exception:  # noqa: BLE001
                n = 0
            by[f"{p.parts[-4]}/{p.parts[-2]}"] = n
    res = {"total": sum(by.values()), "by_recording": by}
    with _exp_lock:
        _expected[folder] = (time.time(), res)
    return res


_filling: set[str] = set()


def expected_wells_cached(folder: str, assay: str = "Network") -> Optional[dict]:
    """Cached answer, or None while a background read fills the cache."""
    with _exp_lock:
        hit = _expected.get(folder)
        if hit:
            return hit[1]
        if folder in _filling:
            return None
        _filling.add(folder)

    def fill():
        try:
            expected_wells(folder, assay)
        finally:
            with _exp_lock:
                _filling.discard(folder)
    threading.Thread(target=fill, daemon=True).start()
    return None


_parsed: dict[str, tuple[tuple, dict]] = {}


def parse_log_file(path: Optional[str], job: str, finished: bool) -> Optional[dict]:
    """Parse a job log, cached by (size, mtime, finished)."""
    if not path:
        return None
    try:
        st = Path(path).stat()
    except OSError:
        return None
    sig = (st.st_size, st.st_mtime_ns, finished)
    hit = _parsed.get(path)
    if hit and hit[0] == sig:
        return hit[1]
    text = Path(path).read_text(errors="ignore")
    res = parse_job_log(text, finished) if job == "network" else parse_activity_log(text)
    res["log_mtime"] = st.st_mtime
    if len(_parsed) > 500:
        _parsed.clear()
    _parsed[path] = (sig, res)
    return res


def estimate(parsed: dict, expected_total: int, elapsed: Optional[float]) -> dict[str, Any]:
    """Progress and a time-left estimate from wells finished so far."""
    done = sum(v for k, v in parsed["counts"].items() if k != "running")
    if not expected_total:
        return {"done": done, "total": None, "fraction": None, "seconds_left": None}
    frac = min(1.0, done / expected_total)
    left = None
    if elapsed and done and done < expected_total:
        left = elapsed / done * (expected_total - done)
    return {"done": done, "total": expected_total, "fraction": round(frac, 3),
            "seconds_left": round(left) if left is not None else None}


# --------------------------------------------------------------------------- #
# Outputs
# --------------------------------------------------------------------------- #
def _tree(path: Path, pattern: str, limit: int = 200000) -> tuple[int, int]:
    """(matching files, total bytes of the folder). Bounded walk."""
    n = size = seen = 0
    if not path.is_dir():
        return 0, 0
    for cur, _dirs, files in os.walk(path):
        for f in files:
            seen += 1
            if seen > limit:
                return n, size
            try:
                size += (Path(cur) / f).stat().st_size
            except OSError:
                continue
            if Path(f).match(pattern):
                n += 1
    return n, size


def outputs(output_dir: Optional[str], folder: str, job: str, log: Optional[str],
            reports: list[dict]) -> list[dict[str, Any]]:
    if not output_dir:
        return []
    project, date = Path(folder).parent.name, Path(folder).name
    root = Path(output_dir) / project
    items = []
    if job == "network":
        n, b = _tree(root / date, "network_results.json")
        items.append({"label": "Network results", "path": str(root / date), "count": n,
                      "unit": "wells", "bytes": b})
        nwb = root / "NWB" / project / date
        if nwb.is_dir():
            n, b = _tree(nwb, "well*.nwb")
            items.append({"label": "NWB files", "path": str(nwb), "count": n, "unit": "files", "bytes": b})
    else:
        n, b = _tree(root / "ActivityScan" / date, "summary.json")
        items.append({"label": "Activity scan results", "path": str(root / "ActivityScan" / date),
                      "count": n, "unit": "chips", "bytes": b})
    for r in reports:
        if r.get("project") == project and r.get("label") == date:
            items.append({"label": "Report", "path": r["path"], "count": 1, "unit": "report",
                          "bytes": None, "report": True})
    if log:
        try:
            items.append({"label": "Log", "path": log, "count": 1, "unit": "file",
                          "bytes": Path(log).stat().st_size, "log": True})
        except OSError:
            pass
    return items
