"""
Who is using the control page.

One server, one port, many people: everyone signs in with a name and an email
address (no password — this says who did something, it does not keep anyone
out). Each sign-in gets a random session token, kept in a browser cookie.

Also keeps the log of who did what: starting and pausing watching, queueing,
holding, stopping, resetting, changing settings.

A small SQLite file next to the run history. Standard library only.
"""

from __future__ import annotations

import re
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    last_login TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    last_seen  TEXT NOT NULL,
    ip         TEXT
);
CREATE TABLE IF NOT EXISTS audit (
    id      INTEGER PRIMARY KEY,
    time    TEXT NOT NULL,
    user_id INTEGER,
    name    TEXT,
    email   TEXT,
    action  TEXT NOT NULL,
    detail  TEXT
);
CREATE INDEX IF NOT EXISTS audit_time ON audit(time);
"""

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# A session nobody has used for this long is signed out.
SESSION_DAYS = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_login(name: str, email: str) -> tuple[str, str]:
    """Validated (name, email), or ValueError with a message for the person."""
    name = " ".join((name or "").split())
    email = (email or "").strip().lower()
    if not name:
        raise ValueError("Please enter your name.")
    if len(name) > 60:
        raise ValueError("Please use a shorter name (60 characters at most).")
    if not EMAIL.match(email) or len(email) > 200:
        raise ValueError("Please enter a valid email address, like name@ucdavis.edu.")
    return name, email


class Accounts:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.execute("PRAGMA foreign_keys=ON")
            self._db.executescript(SCHEMA)
            self._db.commit()

    # -------------------------------------------------------------- sessions
    def login(self, name: str, email: str, ip: str = "") -> tuple[str, dict]:
        """Sign in (creating the person on first use). The email identifies
        them; the name is updated to what they typed this time."""
        name, email = clean_login(name, email)
        now = _now()
        token = secrets.token_urlsafe(32)
        with self._lock:
            row = self._db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if row:
                uid = row["id"]
                self._db.execute("UPDATE users SET name=?, last_login=? WHERE id=?", (name, now, uid))
            else:
                uid = self._db.execute(
                    "INSERT INTO users(name, email, created_at, last_login) VALUES (?,?,?,?)",
                    (name, email, now, now)).lastrowid
            self._db.execute("INSERT INTO sessions(token, user_id, created_at, last_seen, ip) "
                             "VALUES (?,?,?,?,?)", (token, uid, now, now, ip))
            self._db.commit()
        return token, {"id": uid, "name": name, "email": email}

    def user_for(self, token: Optional[str]) -> Optional[dict]:
        """The signed-in person for a session token, or None."""
        if not token:
            return None
        with self._lock:
            r = self._db.execute(
                "SELECT u.id, u.name, u.email, s.last_seen FROM sessions s "
                "JOIN users u ON u.id = s.user_id WHERE s.token=?", (token,)).fetchone()
            if not r:
                return None
            seen = datetime.fromisoformat(r["last_seen"])
            now = datetime.now(timezone.utc)
            if now - seen > timedelta(days=SESSION_DAYS):
                self._db.execute("DELETE FROM sessions WHERE token=?", (token,))
                self._db.commit()
                return None
            # The page polls every few seconds; one write a minute is plenty.
            if now - seen > timedelta(minutes=1):
                self._db.execute("UPDATE sessions SET last_seen=? WHERE token=?", (_now(), token))
                self._db.commit()
            return {"id": r["id"], "name": r["name"], "email": r["email"]}

    def logout(self, token: Optional[str]) -> None:
        if not token:
            return
        with self._lock:
            self._db.execute("DELETE FROM sessions WHERE token=?", (token,))
            self._db.commit()

    # ------------------------------------------------------------ who did what
    def record(self, user: Optional[dict], action: str, detail: str = "") -> None:
        """Note an action. Never raises: the log must not break the action."""
        try:
            with self._lock:
                self._db.execute(
                    "INSERT INTO audit(time, user_id, name, email, action, detail) VALUES (?,?,?,?,?,?)",
                    (_now(), (user or {}).get("id"), (user or {}).get("name"),
                     (user or {}).get("email"), action, detail[:2000]))
                self._db.commit()
        except Exception:  # noqa: BLE001
            pass

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._db.execute(
                "SELECT time, name, email, action, detail FROM audit ORDER BY id DESC LIMIT ?",
                (limit,))]

    def users(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._db.execute(
                "SELECT name, email, created_at, last_login FROM users ORDER BY last_login DESC")]
