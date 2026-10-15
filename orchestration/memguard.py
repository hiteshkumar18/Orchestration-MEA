"""A memory ceiling for each analysis job.

One noisy well can detect hundreds of millions of spikes, and loading them for
network-burst analysis then uses all the RAM in the machine. On 2026-10-07 that
took down the server and the other date running beside it. The spike count is
only known inside the pipeline's per-well routine, which this tool does not
change, so the limit is applied from outside: the driver is started in its own
systemd scope with a memory ceiling.

When a job reaches the ceiling the kernel ends its largest process, which is
the well that is using the memory. The driver reports that well as failed and
carries on with the next one, so the rest of the date and every other job are
unaffected.

Nothing here is required: without systemd, or without the memory controller,
the job simply runs with no ceiling, exactly as before.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

LOG = logging.getLogger("mea.memguard")

# Left for the server, the desktop and the file cache when the ceiling is
# worked out automatically.
RESERVE_GB = 8.0
# Never set an automatic ceiling below this: a normal well needs room to work.
MIN_AUTO_GB = 4.0
# What the driver logs for a well that was killed (SIGKILL).
KILLED_MARK = "Exit Code: -9"

_available: Optional[bool] = None


def total_ram_gb(meminfo: Optional[str] = None) -> float:
    """Installed RAM in GB, or 0 when it cannot be read."""
    try:
        text = Path("/proc/meminfo").read_text() if meminfo is None else meminfo
        for line in text.splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) / 2**20
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def resolve_limit_gb(setting: float, total_gb: float, concurrent: int) -> Optional[float]:
    """The ceiling for one job, or None for no ceiling.

    setting > 0   use that many GB
    setting == 0  automatic: the RAM left after a reserve, shared between the
                  jobs allowed to run at once
    setting < 0   off
    """
    if setting is None or setting < 0:
        return None
    if setting > 0:
        return float(setting)
    if total_gb <= 0:
        return None
    share = (total_gb - RESERVE_GB) / max(1, int(concurrent or 1))
    return round(max(MIN_AUTO_GB, share), 1)


def own_service_unit(cgroup: Optional[str] = None) -> Optional[str]:
    """The systemd service this process runs in, if any.

    A job in its own scope is no longer stopped with the server's service, so
    the scope is tied back to it. Started from a terminal there is no service
    and nothing to tie to, which matches how jobs already behave there.
    """
    try:
        text = Path("/proc/self/cgroup").read_text() if cgroup is None else cgroup
    except OSError:
        return None
    for line in text.splitlines():
        last = line.rsplit("/", 1)[-1].strip()
        if last.endswith(".service") and not last.startswith("user@"):
            return last
    return None


def available(refresh: bool = False) -> bool:
    """Whether a memory-limited scope can be started here. Checked once."""
    global _available
    if _available is not None and not refresh:
        return _available
    ok = False
    if shutil.which("systemd-run"):
        try:
            res = subprocess.run(
                ["systemd-run", "--user", "--scope", "--quiet", "--collect",
                 "-p", "MemoryMax=1G", "--", "true"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            ok = res.returncode == 0
        except (OSError, subprocess.SubprocessError):
            ok = False
    _available = ok
    return ok


def wrap(cmd: list[str], limit_gb: float, bind_unit: Optional[str] = None) -> list[str]:
    """`cmd`, started inside a scope that may use at most `limit_gb` of memory.

    systemd-run replaces itself with the command, so the process id, the
    process group and the exit code are those of the command itself.
    """
    megabytes = max(1, int(round(limit_gb * 1024)))
    pre = ["systemd-run", "--user", "--scope", "--quiet", "--collect",
           "-p", f"MemoryMax={megabytes}M",
           # Without this a job at its ceiling spills into swap and drags the
           # whole machine down instead of stopping.
           "-p", "MemorySwapMax=0"]
    if bind_unit:
        pre += ["-p", f"BindsTo={bind_unit}", "-p", f"After={bind_unit}"]
    return pre + ["--"] + list(cmd)


def stop_orphans(bind_unit: Optional[str]) -> list[str]:
    """Stop jobs a previous run of this server left behind. Returns their units.

    A job runs in its own scope, tied to the server's service. Stopping the
    service, or the service crashing and being restarted, ends the scope too.
    A deliberate `systemctl restart` does not: systemd restarts the service
    and leaves the scope running. Before jobs had their own scope they lived
    inside the service and always ended with it, and everything here assumes
    that: the restarted server marks the job "interrupted", and resuming it
    would start a second copy writing into the same wells as the first.

    So when the server starts, scopes tied to its own service are leftovers
    and are stopped. Only scopes bound to this service: other servers' and
    other users' jobs are never touched.
    """
    if not bind_unit or not shutil.which("systemctl"):
        return []
    try:
        listed = subprocess.run(
            ["systemctl", "--user", "list-units", "--type=scope", "--state=active",
             "--no-legend", "--plain", "run-*.scope"],
            capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    stopped = []
    for line in listed.splitlines():
        unit = line.split()[0] if line.split() else ""
        if not unit.endswith(".scope"):
            continue
        try:
            bound = subprocess.run(
                ["systemctl", "--user", "show", unit, "-p", "BindsTo", "--value"],
                capture_output=True, text=True, timeout=20).stdout.split()
            if bind_unit in bound:
                subprocess.run(["systemctl", "--user", "stop", unit],
                               capture_output=True, timeout=120)
                stopped.append(unit)
        except (OSError, subprocess.SubprocessError):
            continue
    return stopped


def count_killed(log_path: Path) -> int:
    """How many wells the driver reported as killed in this job's log."""
    try:
        with open(log_path, errors="replace") as fh:
            return sum(1 for line in fh if KILLED_MARK in line)
    except OSError:
        return 0
