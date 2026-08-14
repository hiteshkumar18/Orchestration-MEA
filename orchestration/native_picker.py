"""
Open the desktop's own folder chooser (Nautilus/GTK, KDE, or Tk).

When this helps
---------------
Only when the browser and this server are the **same machine**. The dialog opens
on the server's display, so if you are reaching the UI over an SSH tunnel from a
laptop it would appear on the lab machine's screen, not yours.

The browser's own ``showDirectoryPicker`` is not an alternative: it selects
folders on the *client*, and the watcher needs paths that exist on the server.

So this is offered opportunistically — the UI shows a "Use file manager" button
only when a display and a dialog tool are both present, and the built-in browser
remains the path that always works.

Tools tried, in order
---------------------
``zenity``   GTK/GNOME — the dialog Nautilus itself uses
``kdialog``  KDE
``tkinter``  bundled with Python, as a last resort
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

LOG = logging.getLogger("mea.picker")

DIALOG_TIMEOUT = 300  # a person has to actually click something


def has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def available_tool() -> Optional[str]:
    """Which chooser we can use here, if any."""
    if not has_display():
        return None
    for tool in ("zenity", "kdialog"):
        if shutil.which(tool):
            return tool
    try:
        import tkinter  # noqa: F401
        return "tkinter"
    except Exception:  # noqa: BLE001
        return None


def describe() -> dict:
    """What the UI needs to decide whether to offer the button."""
    tool = available_tool()
    return {
        "available": tool is not None,
        "tool": tool,
        "display": os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or None,
        "reason": None if tool else (
            "No display on this machine — the file manager can only be used when "
            "the browser and the server are the same computer."
            if not has_display() else
            "No folder chooser found. Install zenity (GNOME/Nautilus) or kdialog (KDE)."
        ),
    }


def _run(cmd: list[str]) -> Optional[str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=DIALOG_TIMEOUT)
    except subprocess.TimeoutExpired:
        LOG.warning("Folder chooser timed out after %ss", DIALOG_TIMEOUT)
        return None
    except OSError as exc:
        LOG.warning("Could not launch folder chooser: %s", exc)
        return None
    # Non-zero simply means the user cancelled.
    if proc.returncode != 0:
        return None
    path = proc.stdout.strip()
    return path or None


def choose_directory(start: str = "", title: str = "Select folder") -> Optional[str]:
    """Open the desktop folder chooser and return the selection, or None."""
    tool = available_tool()
    if tool is None:
        return None

    start_dir = start if start and Path(start).is_dir() else str(Path.home())

    if tool == "zenity":
        # Trailing separator makes zenity open *inside* start_dir.
        return _run(["zenity", "--file-selection", "--directory",
                     f"--title={title}", f"--filename={start_dir.rstrip('/')}/"])

    if tool == "kdialog":
        return _run(["kdialog", "--getexistingdirectory", start_dir, "--title", title])

    if tool == "tkinter":
        # Run in a subprocess: Tk must own the main thread, which the API server
        # already does, and a stray Tk root would wedge the event loop.
        code = (
            "import tkinter as tk;from tkinter import filedialog;"
            "r=tk.Tk();r.withdraw();r.attributes('-topmost',True);"
            f"p=filedialog.askdirectory(initialdir={start_dir!r},title={title!r});"
            "print(p or '')"
        )
        import sys
        return _run([sys.executable, "-c", code])

    return None
