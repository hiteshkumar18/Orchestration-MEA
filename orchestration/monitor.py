"""
System health for the dashboard: CPU, memory, GPU, disks and analysis processes.

A background sampler refreshes everything every few seconds, so a dashboard
request only reads a cached snapshot and never waits on a slow disk or
nvidia-smi. Linux /proc and nvidia-smi only; no extra packages.
"""

from __future__ import annotations

import os
import pwd
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

PIPELINE_MARKERS = {
    "run_pipeline_driver.py": "Network driver",
    "mea_analysis_routine.py": "Network well",
    "nwb_job.py": "NWB job",
    "convert_date.py": "NWB conversion",
    "convert_maxone_to_nwb.py": "NWB conversion",
    "split_maxtwo_by_well.py": "NWB split",
    "routine_shim.py": "Network well (NWB)",
    "activity_scan.py": "Activity scan",
    "build_report.py": "Report",
}
CLK = os.sysconf("SC_CLK_TCK")


# --------------------------------------------------------------------------- #
# Parsers (pure functions: unit-tested with fixture text)
# --------------------------------------------------------------------------- #
def parse_cpu_times(stat_text: str) -> tuple[int, int]:
    """(busy, total) jiffies from the first line of /proc/stat."""
    parts = stat_text.splitlines()[0].split()[1:]
    vals = [int(x) for x in parts[:8]]
    idle = vals[3] + (vals[4] if len(vals) > 4 else 0)        # idle + iowait
    total = sum(vals)
    return total - idle, total


def parse_iowait(stat_text: str) -> tuple[int, int]:
    parts = [int(x) for x in stat_text.splitlines()[0].split()[1:9]]
    return parts[4], sum(parts)


def parse_meminfo(text: str) -> dict[str, int]:
    out = {}
    for line in text.splitlines():
        k, _, rest = line.partition(":")
        v = rest.strip().split()
        if v and v[0].isdigit():
            out[k] = int(v[0]) * 1024
    return out


def parse_nvidia_smi(text: str) -> dict[str, Any]:
    """CSV from --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu."""
    text = text.strip()
    if not text:
        return {"ok": False, "error": "no output"}
    if "mismatch" in text.lower() or "failed" in text.lower() or "error" in text.lower():
        return {"ok": False, "error": text.splitlines()[0][:200]}
    gpus = []
    for line in text.splitlines():
        f = [x.strip() for x in line.split(",")]
        if len(f) < 5:
            continue
        try:
            gpus.append({"name": f[0], "util": float(f[1]), "mem_used_mb": float(f[2]),
                         "mem_total_mb": float(f[3]), "temp_c": float(f[4])})
        except ValueError:
            continue
    return {"ok": bool(gpus), "gpus": gpus} if gpus else {"ok": False, "error": text[:200]}


# --------------------------------------------------------------------------- #
# Sampler
# --------------------------------------------------------------------------- #
class SystemMonitor:
    def __init__(self, paths: Callable[[], dict[str, str]], interval: float = 5.0,
                 own_pids: Callable[[], set[int]] = lambda: set()):
        self.paths = paths                 # label -> path to report disk space for
        self.interval = interval
        self.own_pids = own_pids
        self._snap: dict[str, Any] = {"ready": False}
        self._lock = threading.Lock()
        self._prev_cpu: Optional[tuple[int, int]] = None
        self._prev_io: Optional[tuple[int, int]] = None
        self._prev_proc: dict[int, tuple[int, float]] = {}
        self._gpu: dict[str, Any] = {"ok": False, "error": "not checked yet"}
        self._gpu_at = 0.0
        self._disks: dict[str, Any] = {}
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="system-monitor", daemon=True)
        self._thread.start()

    def snapshot(self) -> dict[str, Any]:
        self.start()
        with self._lock:
            return dict(self._snap)

    def _loop(self) -> None:
        while True:
            try:
                self.sample()
            except Exception:  # noqa: BLE001
                pass
            time.sleep(self.interval)

    def sample(self) -> dict[str, Any]:
        stat = Path("/proc/stat").read_text()
        busy, total = parse_cpu_times(stat)
        io, io_total = parse_iowait(stat)
        cpu_pct = io_pct = None
        if self._prev_cpu:
            db, dt = busy - self._prev_cpu[0], total - self._prev_cpu[1]
            cpu_pct = round(100 * db / dt, 1) if dt else None
        if self._prev_io:
            di, dt = io - self._prev_io[0], io_total - self._prev_io[1]
            io_pct = round(100 * di / dt, 1) if dt else None
        self._prev_cpu, self._prev_io = (busy, total), (io, io_total)
        load = os.getloadavg()
        mem = parse_meminfo(Path("/proc/meminfo").read_text())
        if time.time() - self._gpu_at > 15:
            self._gpu = self._read_gpu()
            self._gpu_at = time.time()
        self._refresh_disks()
        procs = self._processes()
        snap = {
            "ready": True, "time": time.time(),
            "cpu": {"cores": os.cpu_count(), "percent": cpu_pct, "iowait_percent": io_pct,
                    "load": [round(x, 2) for x in load]},
            "memory": {"total": mem.get("MemTotal"), "available": mem.get("MemAvailable"),
                       "used": (mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)),
                       "swap_total": mem.get("SwapTotal"), "swap_free": mem.get("SwapFree")},
            "gpu": self._gpu,
            "disks": dict(self._disks),
            "processes": procs,
        }
        snap["warnings"] = warnings(snap)
        with self._lock:
            self._snap = snap
        return snap

    def _read_gpu(self) -> dict[str, Any]:
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,"
                                "memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=20)
            return parse_nvidia_smi(r.stdout + r.stderr)
        except FileNotFoundError:
            return {"ok": False, "error": "nvidia-smi not installed"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "nvidia-smi did not answer within 20 s"}

    def _refresh_disks(self) -> None:
        """Each path checked in its own short-lived thread: a hung network mount
        must not stall the sampler."""
        for label, path in (self.paths() or {}).items():
            if not path:
                continue
            res: dict[str, Any] = {}

            def probe(p=path, out=res):
                try:
                    u = shutil.disk_usage(p)
                    out.update(total=u.total, used=u.used, free=u.free)
                except OSError as exc:
                    out.update(error=str(exc))
            t = threading.Thread(target=probe, daemon=True)
            t.start()
            t.join(5)
            entry = {"path": path, **res} if res else {"path": path, "error": "did not answer within 5 s"}
            self._disks[label] = entry

    def _processes(self) -> list[dict[str, Any]]:
        out, now_proc = [], {}
        own = self.own_pids()
        uptime = float(Path("/proc/uptime").read_text().split()[0])
        me = os.getuid()
        for pid_s in os.listdir("/proc"):
            if not pid_s.isdigit():
                continue
            pid = int(pid_s)
            try:
                cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="ignore")
            except OSError:
                continue
            kind = next((v for k, v in PIPELINE_MARKERS.items() if k in cmd), None)
            if not kind:
                continue
            try:
                st = Path(f"/proc/{pid}/stat").read_text()
                fields = st[st.rfind(")") + 2:].split()
                ppid = int(fields[1])
                cpu_ticks = int(fields[11]) + int(fields[12])
                start = int(fields[19]) / CLK
                uid = os.stat(f"/proc/{pid}").st_uid
                rss = 0
                for line in Path(f"/proc/{pid}/status").read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        rss = int(line.split()[1]) * 1024
            except (OSError, ValueError, IndexError):
                continue
            prev = self._prev_proc.get(pid)
            now = time.time()
            cpu = None
            if prev:
                cpu = round(100 * (cpu_ticks - prev[0]) / CLK / max(now - prev[1], 1e-6), 1)
            now_proc[pid] = (cpu_ticks, now)
            try:
                user = pwd.getpwuid(uid).pw_name
            except KeyError:
                user = str(uid)
            out.append({"pid": pid, "ppid": ppid, "kind": kind, "user": user, "mine": uid == me,
                        "ours": pid in own, "cpu_percent": cpu, "rss": rss,
                        "elapsed_s": round(uptime - start),
                        "target": _target(cmd)})
        self._prev_proc = now_proc
        out.sort(key=lambda p: (not p["mine"], p["kind"], p["pid"]))
        return out


def _target(cmd: str) -> str:
    """The date/chip/run/well a pipeline process is working on, from its
    command line: '260821/M07036/000023/well002', or just the date for a
    process working on a whole date folder."""
    import re
    m = re.search(r"--well[ =](well\d+)", cmd)
    well = m.group(1) if m else ""
    for tok in cmd.replace("'", " ").replace('"', " ").split():
        p = tok.rstrip("/").split("/")
        dates = [i for i, part in enumerate(p) if len(part) == 6 and part.isdigit() and i > 0]
        if not dates:
            continue
        rest = [x for x in p[dates[0]:] if x not in ("Network", "ActivityScan")]
        if rest[-1].endswith((".h5", ".nwb")) or rest[-1].startswith("well"):
            name = rest.pop()
            well = well or (name.split(".")[0] if name.startswith("well") else "")
        return "/".join(rest[:3] + ([well] if well else []))
    return well


def warnings(s: dict[str, Any]) -> list[dict[str, str]]:
    """Plain-language warnings, most serious first."""
    out = []
    g = s.get("gpu") or {}
    if not g.get("ok"):
        err = g.get("error", "")
        if "mismatch" in err.lower():
            out.append({"level": "bad", "text": "The graphics card driver needs a restart of the computer "
                        "(driver/library version mismatch). Spike sorting would hang; detection-only "
                        "analysis is unaffected."})
        elif err and "not installed" not in err:
            out.append({"level": "warn", "text": f"The graphics card could not be checked: {err}"})
    m = s.get("memory") or {}
    if m.get("total") and m.get("available") is not None:
        free = m["available"] / m["total"]
        if free < 0.08:
            out.append({"level": "bad", "text": f"Memory is almost full ({free:.0%} free). Analyses may be "
                        "stopped by the system; consider running fewer at once."})
        elif free < 0.15:
            out.append({"level": "warn", "text": f"Memory is getting low ({free:.0%} free)."})
    for label, d in (s.get("disks") or {}).items():
        if d.get("error"):
            out.append({"level": "warn", "text": f"{label}: {d['error']}"})
        elif d.get("total"):
            frac = d["free"] / d["total"]
            if (label == "Fast disk" and d["free"] < 200 * 2**30) or frac < 0.03:
                out.append({"level": "bad" if frac < 0.03 else "warn",
                            "text": f"{label} is nearly full: {d['free'] / 2**30:.0f} GB free ({frac:.0%})."})
    c = s.get("cpu") or {}
    if c.get("iowait_percent") and c["iowait_percent"] > 40:
        out.append({"level": "warn", "text": f"Processors are waiting on disks {c['iowait_percent']:.0f}% of "
                    "the time — analyses are slowed by disk speed."})
    return out
