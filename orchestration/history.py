"""
Run history: every analysis run, kept.

The watcher's state file holds only the latest run per folder and job, and
forgets it on reset. This keeps a permanent record of each run — one row per
dispatch — with its timeline of status/detail changes and a snapshot of the
settings it ran with, in a small SQLite file next to the state file.

It is fed by StateStore.on_update: every state change for a key is mirrored
here. A run starts when a key is dispatched (or found in a dry run, or fails
before dispatch) and ends at a terminal status. Standard library only.
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# A run is open until one of these.
TERMINAL = {"done", "failed", "interrupted", "detected"}
# Statuses that begin a new run.
STARTS = {"dispatched", "detected"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            TEXT PRIMARY KEY,
    key           TEXT NOT NULL,
    folder        TEXT NOT NULL,
    project       TEXT,
    date          TEXT,
    job           TEXT,
    job_label     TEXT,
    status        TEXT,
    detail        TEXT,
    error         TEXT,
    command       TEXT,
    log           TEXT,
    returncode    INTEGER,
    dispatched_at TEXT,
    started_at    TEXT,
    completed_at  TEXT,
    duration_s    REAL,
    settings      TEXT,
    imported      INTEGER DEFAULT 0,
    created       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS runs_key ON runs(key);
CREATE INDEX IF NOT EXISTS runs_created ON runs(created);
CREATE TABLE IF NOT EXISTS events (
    run_id  TEXT NOT NULL,
    time    TEXT NOT NULL,
    status  TEXT,
    message TEXT
);
CREATE INDEX IF NOT EXISTS events_run ON events(run_id);
"""

# The watcher's once-a-minute "still running" note: kept as the run's current
# detail, but not a step worth a line in its timeline.
HEARTBEAT = re.compile(r"^running .+ · last log output .+ ago$")

RUN_FIELDS = ("status", "detail", "error", "command", "log", "returncode", "dispatched_at",
              "started_at", "completed_at", "duration_s", "job_label")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def split_key(key: str) -> tuple[str, str, str, str]:
    """'<folder>::<job>' -> (folder, job, project, date)."""
    folder, _, job = key.partition("::")
    p = Path(folder)
    return folder, job or "network", p.parent.name, p.name


class RunHistory:
    def __init__(self, path: Path, settings_snapshot=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(SCHEMA)
            self._db.commit()
        # Called at dispatch to record the settings a run used.
        self._settings_snapshot = settings_snapshot or (lambda: {})
        self._open: dict[str, str] = {}          # key -> open run id
        with self._lock:
            for r in self._db.execute(
                    "SELECT id, key FROM runs WHERE status NOT IN ({}) OR status IS NULL"
                    .format(",".join("?" * len(TERMINAL))), tuple(TERMINAL)):
                self._open[r["key"]] = r["id"]

    # ------------------------------------------------------------------ write
    def record(self, key: str, entry: dict, changed: dict) -> None:
        """Mirror one state update. `entry` is the merged state, `changed` the
        fields this update set. Never raises: history must not break a job."""
        try:
            self._record(key, entry, changed)
        except Exception:  # noqa: BLE001
            pass

    def _record(self, key: str, entry: dict, changed: dict) -> None:
        status = changed.get("status")
        with self._lock:
            run_id = self._open.get(key)
            if run_id is not None and not self._still_open(run_id):
                # Closed by another RunHistory on the same file (a watcher
                # replaced by a settings save keeps finishing its jobs).
                self._open.pop(key, None)
                run_id = None
            starts = status in STARTS or (status in TERMINAL and run_id is None
                                          and status != "interrupted")
            if starts and (run_id is None or status in STARTS):
                if run_id is not None and status in STARTS:
                    # A new dispatch while one is open: the old one was abandoned.
                    self._close(run_id, "interrupted", "superseded by a new run")
                run_id = self._new_run(key, entry)
            if run_id is None:
                return                      # waiting/queued before any dispatch: not a run yet
            sets = {f: entry.get(f) for f in RUN_FIELDS if f in changed or f == "status"}
            if sets:
                cols = ", ".join(f"{k}=?" for k in sets)
                self._db.execute(f"UPDATE runs SET {cols} WHERE id=?", (*sets.values(), run_id))
            msg = changed.get("error") if status == "failed" else changed.get("detail")
            if not status and msg and HEARTBEAT.match(msg):
                msg = None
            if status or msg:
                self._db.execute("INSERT INTO events(run_id, time, status, message) VALUES (?,?,?,?)",
                                 (run_id, _now(), status, msg))
            if status in TERMINAL:
                self._open.pop(key, None)
            self._db.commit()

    def _new_run(self, key: str, entry: dict) -> str:
        folder, job, project, date = split_key(key)
        run_id = uuid.uuid4().hex[:12]
        try:
            settings = json.dumps(self._settings_snapshot())
        except Exception:  # noqa: BLE001
            settings = "{}"
        self._db.execute(
            "INSERT INTO runs(id, key, folder, project, date, job, job_label, created, settings) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, key, folder, project, date, entry.get("job") or job, entry.get("job_label"),
             _now(), settings))
        self._open[key] = run_id
        return run_id

    def _still_open(self, run_id: str) -> bool:
        r = self._db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
        return bool(r) and r["status"] not in TERMINAL

    def _close(self, run_id: str, status: str, message: str) -> None:
        self._db.execute("UPDATE runs SET status=? WHERE id=?", (status, run_id))
        self._db.execute("INSERT INTO events(run_id, time, status, message) VALUES (?,?,?,?)",
                         (run_id, _now(), status, message))

    def close_open(self, key: str, message: str) -> None:
        """A key forgotten by hand: its open run, if any, will never finish."""
        try:
            with self._lock:
                run_id = self._open.pop(key, None)
                if run_id is not None and self._still_open(run_id):
                    self._close(run_id, "interrupted", message)
                    self._db.commit()
        except Exception:  # noqa: BLE001
            pass

    def import_state(self, state: dict[str, dict]) -> int:
        """One-time import of the state file's latest runs, so history is not
        empty on first use. Only when the history has no runs yet."""
        with self._lock:
            if self._db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]:
                return 0
            n = 0
            for key, e in state.items():
                if not e.get("status") or e.get("status") == "waiting":
                    continue
                folder, job, project, date = split_key(key)
                run_id = uuid.uuid4().hex[:12]
                self._db.execute(
                    "INSERT INTO runs(id, key, folder, project, date, job, job_label, status, detail, "
                    "error, command, log, returncode, dispatched_at, started_at, completed_at, "
                    "duration_s, settings, imported, created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)",
                    (run_id, key, folder, project, date, e.get("job") or job, e.get("job_label"),
                     e.get("status"), e.get("detail"), e.get("error"), e.get("command"), e.get("log"),
                     e.get("returncode"), e.get("dispatched_at"), e.get("started_at"),
                     e.get("completed_at"), e.get("duration_s"), "{}",
                     e.get("dispatched_at") or e.get("started_at") or _now()))
                if e.get("status") not in TERMINAL:
                    self._open[key] = run_id
                n += 1
            self._db.commit()
            return n

    # ------------------------------------------------------------------- read
    def current_run_id(self, key: str) -> Optional[str]:
        with self._lock:
            if key in self._open:
                return self._open[key]
            r = self._db.execute("SELECT id FROM runs WHERE key=? ORDER BY created DESC LIMIT 1",
                                 (key,)).fetchone()
            return r["id"] if r else None

    def knows_log(self, *paths: str) -> bool:
        """Whether a log file is one this tool wrote for a recorded run."""
        with self._lock:
            return any(self._db.execute("SELECT 1 FROM runs WHERE log=? LIMIT 1", (p,)).fetchone()
                       for p in paths if p)

    def get(self, run_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            r = self._db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not r:
                return None
            run = dict(r)
            run["settings"] = json.loads(run.get("settings") or "{}")
            run["events"] = [dict(e) for e in self._db.execute(
                "SELECT time, status, message FROM events WHERE run_id=? ORDER BY rowid", (run_id,))]
            run["attempt"] = self._db.execute(
                "SELECT COUNT(*) FROM runs WHERE key=? AND created<=?", (run["key"], run["created"])
            ).fetchone()[0]
            return run

    def list(self, *, project: str = "", job: str = "", status: str = "", date: str = "",
             limit: int = 50, offset: int = 0) -> dict[str, Any]:
        where, args = [], []
        for col, val in (("project", project), ("job", job), ("date", date)):
            if val:
                where.append(f"{col}=?")
                args.append(val)
        if status:
            where.append("status IN ({})".format(",".join("?" * len(status.split(",")))))
            args += status.split(",")
        sql = "FROM runs" + (" WHERE " + " AND ".join(where) if where else "")
        with self._lock:
            total = self._db.execute("SELECT COUNT(*) " + sql, args).fetchone()[0]
            rows = [dict(r) for r in self._db.execute(
                "SELECT id, key, folder, project, date, job, job_label, status, detail, error, log, "
                "dispatched_at, started_at, completed_at, duration_s, imported, created "
                + sql + " ORDER BY created DESC LIMIT ? OFFSET ?", (*args, limit, offset))]
            projects = [r[0] for r in self._db.execute(
                "SELECT DISTINCT project FROM runs WHERE project IS NOT NULL ORDER BY project")]
        return {"total": total, "runs": rows, "projects": projects}
