"""
Copy every project's activity-scan results to OneDrive, as well as keeping them
in the results folder.

The copy is made with rclone (``rclone copy``): it only adds files and replaces
changed ones at the destination. Nothing is ever deleted or moved, on either
side, and the results folder is only read. Running it again copies only what is
new, so it is safe to run after every finished scan and on a timer, which also
picks up older dates and anything a failed copy missed.

The OneDrive login lives in rclone's own config (``rclone config``, remote
``onedrive``); this module never sees or stores it.

Layout at the destination mirrors the results folder:
    <dest>/<project>/ActivityScan/<date>/<chip>/<run>/...
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

LOG = logging.getLogger("mea.onedrive")

RCLONE = shutil.which("rclone") or "rclone"
EVERY_SECONDS = 30 * 60            # regular sweep
COPY_TIMEOUT = 4 * 3600            # one project, worst case
CHECK_TIMEOUT = 60
EXCLUDE = ("*.log", "*.tmp", "*.partial")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sources(cfg) -> list[tuple[Path, str]]:
    """(folder on disk, path under the destination) for every activity-scan
    folder there is: <output>/<project>/ActivityScan, or the one configured
    activity output folder."""
    if getattr(cfg, "activity_output_dir", ""):
        p = Path(cfg.activity_output_dir)
        return [(p, "ActivityScan")] if p.is_dir() else []
    out = cfg.output_dir
    if not out or not Path(out).is_dir():
        return []
    return [(d, f"{d.parent.name}/ActivityScan")
            for d in sorted(Path(out).glob("*/ActivityScan")) if d.is_dir()]


def join(dest: str, rel: str) -> str:
    return dest.rstrip("/") + "/" + rel if not dest.endswith(":") else dest + rel


def copy_command(src: Path, dest: str) -> list[str]:
    # "copy", never "sync" or "move": nothing at the destination is deleted and
    # nothing is taken away from the results folder.
    cmd = [RCLONE, "copy", str(src), dest, "--transfers", "4", "--checkers", "8",
           "--retries", "3", "--low-level-retries", "10", "--use-json-log", "-v", "--stats", "0"]
    for x in EXCLUDE:
        cmd += ["--exclude", x]
    return cmd


def count_copied(log_text: str) -> int:
    n = 0
    for line in log_text.splitlines():
        try:
            msg = json.loads(line).get("msg", "")
        except ValueError:
            msg = line
        if msg.startswith("Copied (new)") or msg.startswith("Copied (replaced"):
            n += 1
    return n


def last_error(log_text: str) -> str:
    for line in reversed(log_text.splitlines()):
        try:
            j = json.loads(line)
        except ValueError:
            if line.strip():
                return line.strip()[:300]
            continue
        if j.get("level") in ("error", "critical"):
            return (j.get("msg") or "").strip()[:300]
    return ""


def check(dest: str, run=subprocess.run) -> dict[str, Any]:
    """Is rclone there, is the OneDrive login set up, and can we see the folder?"""
    if not dest or ":" not in dest:
        return {"ok": False, "say": "Give the destination as <remote>:<folder>, for example "
                                    "onedrive:Ben-Shalom Lab/MEA activity scans."}
    if not shutil.which(RCLONE) and not Path(RCLONE).exists():
        return {"ok": False, "say": "rclone is not installed on this computer."}
    remote = dest.split(":", 1)[0] + ":"
    try:
        r = run([RCLONE, "listremotes"], capture_output=True, text=True, timeout=CHECK_TIMEOUT)
        if remote not in r.stdout.split():
            return {"ok": False, "say": f"There is no OneDrive login called {remote[:-1]} yet. "
                                        "Set it up once with: rclone config (see docs/ONEDRIVE.md)."}
        r = run([RCLONE, "lsf", "--max-depth", "1", "--dirs-only", dest],
                capture_output=True, text=True, timeout=CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ok": False, "say": "OneDrive did not answer within a minute."}
    if r.returncode == 0:
        n = len([x for x in r.stdout.splitlines() if x.strip()])
        return {"ok": True, "say": f"Connected. The folder is there ({n} folder{'' if n == 1 else 's'} in it)."}
    err = (r.stderr or "").strip().splitlines()
    msg = err[-1] if err else "unknown error"
    if "directory not found" in msg.lower():
        return {"ok": True, "say": "Connected. The folder does not exist yet; it is made on the first copy."}
    return {"ok": False, "say": f"Could not reach OneDrive: {msg[:300]}"}


class OneDriveCopier:
    """Runs one copy at a time in the background. A request that arrives while
    a copy is running is remembered and runs once right after it."""

    def __init__(self, get_cfg: Callable[[], Any], state_path: Path, run=subprocess.Popen):
        self.get_cfg, self.state_path, self._popen = get_cfg, Path(state_path), run
        self._lock = threading.Lock()
        self._busy = False
        self._again: Optional[str] = None
        self._stop = threading.Event()
        self._timer: Optional[threading.Thread] = None
        try:
            self.last: dict[str, Any] = json.loads(self.state_path.read_text())
        except (OSError, ValueError):
            self.last = {}

    # -- public -------------------------------------------------------------- #
    def enabled(self) -> bool:
        cfg = self.get_cfg()
        return bool(getattr(cfg, "onedrive_copy", False) and getattr(cfg, "onedrive_dest", ""))

    def status(self) -> dict[str, Any]:
        cfg = self.get_cfg()
        return {"enabled": bool(getattr(cfg, "onedrive_copy", False)),
                "dest": getattr(cfg, "onedrive_dest", ""),
                "copying": self._busy, "last": self.last}

    def trigger(self, reason: str, wait: bool = False) -> bool:
        """Start a copy (or queue one behind the running copy). False when off."""
        if not self.enabled():
            return False
        with self._lock:
            if self._busy:
                self._again = reason
                return True
            self._busy = True
        t = threading.Thread(target=self._loop, args=(reason,), name="mea-onedrive", daemon=True)
        t.start()
        if wait:
            t.join()
        return True

    def start_timer(self) -> None:
        if self._timer:
            return
        def tick():
            while not self._stop.wait(EVERY_SECONDS):
                self.trigger("regular check")
        self._timer = threading.Thread(target=tick, name="mea-onedrive-timer", daemon=True)
        self._timer.start()

    def stop(self) -> None:
        self._stop.set()

    # -- work ---------------------------------------------------------------- #
    def _loop(self, reason: str) -> None:
        try:
            while True:
                self._copy_all(reason)
                with self._lock:
                    if not self._again or not self.enabled():
                        self._again = None
                        self._busy = False
                        return
                    reason, self._again = self._again, None
        except Exception:  # noqa: BLE001 — never let a copy take the bench down
            LOG.exception("OneDrive copy crashed")
            with self._lock:
                self._busy = False

    def _copy_all(self, reason: str) -> None:
        cfg = self.get_cfg()
        dest = cfg.onedrive_dest
        started, t0 = _now(), time.time()
        copied, errors, done = 0, [], []
        for src, rel in sources(cfg):
            try:
                p = self._popen(copy_command(src, join(dest, rel)), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
                out, _ = p.communicate(timeout=COPY_TIMEOUT)
            except subprocess.TimeoutExpired:
                p.kill()
                p.communicate()
                errors.append(f"{rel}: took longer than {COPY_TIMEOUT // 3600} h")
                continue
            except OSError as exc:
                errors.append(f"{rel}: {exc}")
                break
            n = count_copied(out or "")
            copied += n
            if p.returncode == 0:
                done.append(rel.split("/")[0])
            else:
                errors.append(f"{rel}: {last_error(out or '') or 'rclone exit code ' + str(p.returncode)}")
        self.last = {"started": started, "finished": _now(), "seconds": round(time.time() - t0, 1),
                     "reason": reason, "dest": dest, "ok": not errors, "copied": copied,
                     "projects": done, "errors": errors[:5]}
        (LOG.info if not errors else LOG.warning)(
            "OneDrive copy (%s): %d file(s) copied to %s%s", reason, copied, dest,
            f"; problems: {'; '.join(errors[:3])}" if errors else "")
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.last, indent=1))
            tmp.replace(self.state_path)
        except OSError:
            LOG.warning("Could not save the OneDrive copy status to %s", self.state_path)
