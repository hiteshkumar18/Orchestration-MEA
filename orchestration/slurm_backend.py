"""Running Network analyses on the lab's Slurm cluster.

The lab's three computers form one Slurm queue ("mea"). Jobs run as the shared
compute account lab-jobs, submitted through the lab's narrow client
(/usr/local/bin/mea-slurm), which answers in JSON. See the lab's handoff in
mea-lab-docs/HITESH-HANDOFF.md.

One date is one job. Everything that touches the recordings or scratch happens
inside the job, on whichever computer Slurm picked:

  1. pick that computer's analysis Python, MEA-Analysis folder and NAS mount
     (the NAS is mounted at different paths on different computers);
  2. copy the date's recordings from the NAS to that computer's fast disk
     (read only), plus any earlier results the server left in the job's
     shared folder, so finished wells are not redone;
  3. run the pipeline there;
  4. copy the results to the shared results folder, check the copy, and only
     then delete the scratch copy. If the copy does not match, scratch is
     kept and the job says where.

This server then copies the results from the shared folder into the real
results folder, checks that copy too, and only then deletes the shared copy.
The job writes its exit code into the shared folder last, so the outcome is
known even after Slurm has forgotten the job (it keeps finished jobs for about
a day).
"""
from __future__ import annotations

import json
import logging
import re
import shlex
import subprocess
from pathlib import PurePosixPath
from typing import Optional

LOG = logging.getLogger("mea.slurm")

DEFAULT_CLIENT = "/usr/local/bin/mea-slurm"
NODE_NAMES = ("BenShalomLabServer", "benshalom-labtower1", "benshalom-labtower2")

PENDING = {"PENDING", "REQUEUED", "REQUEUE_HOLD", "REQUEUE_FED", "RESV_DEL_HOLD", "SUSPENDED",
           "CONFIGURING"}
RUNNING = {"RUNNING", "COMPLETING", "STAGE_OUT", "SIGNALING", "RESIZING"}
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL",
            "PREEMPTED", "BOOT_FAIL", "DEADLINE", "SPECIAL_EXIT", "REVOKED"}

# Exit codes the job script uses for its own steps.
EXIT_NO_NODE_SETTINGS = 97
EXIT_SETUP = 96
EXIT_COPY_INPUT = 95
EXIT_COPY_RESULTS = 94
EXIT_SAY = {
    EXIT_NO_NODE_SETTINGS: "the cluster ran it on a computer this server has no settings for "
                           "(Settings → Where analyses run)",
    EXIT_SETUP: "the job could not prepare its folders on the cluster computer",
    EXIT_COPY_INPUT: "the job could not copy the recordings from the NAS to the cluster computer",
    EXIT_COPY_RESULTS: "the results could not be copied off the cluster computer; they are kept "
                       "in its scratch folder (see the log)",
}
SAY_STATE = {
    "TIMEOUT": "it reached the cluster's time limit",
    "OUT_OF_MEMORY": "it used more memory than it asked the cluster for",
    "NODE_FAIL": "the cluster computer running it failed",
    "PREEMPTED": "the cluster stopped it for other work",
    "BOOT_FAIL": "the cluster computer could not start it",
    "DEADLINE": "it missed its deadline in the cluster queue",
}


class SlurmError(RuntimeError):
    """The client said no. `uncertain` when it may have happened anyway."""

    def __init__(self, msg: str, uncertain: bool = False):
        super().__init__(msg)
        self.uncertain = uncertain


class SlurmClient:
    """The lab's mea-slurm client: submit, status, logs, cancel."""

    def __init__(self, path: str = DEFAULT_CLIENT, timeout: float = 60):
        self.path = path
        self.timeout = timeout

    def _call(self, args: list, script: Optional[str] = None) -> dict:
        try:
            r = subprocess.run([self.path, *map(str, args)], input=script, text=True,
                               capture_output=True, timeout=self.timeout, check=False)
        except subprocess.TimeoutExpired:
            raise SlurmError(f"the cluster did not answer within {self.timeout:g}s", uncertain=True)
        except OSError as exc:
            raise SlurmError(f"could not run {self.path}: {exc}")
        if r.returncode:
            err = r.stderr.strip()
            try:
                err = json.loads(err).get("error") or err
            except ValueError:
                pass
            raise SlurmError(err or f"{self.path} failed")
        try:
            return json.loads(r.stdout)
        except ValueError:
            raise SlurmError(f"{self.path} answered with something that is not JSON", uncertain=True)

    def submit(self, script: str, *, cpus: int, mem_mib: int, minutes: int, gpu: bool,
               node: Optional[str], name: str) -> dict:
        args = ["submit", "--cpus", cpus, "--mem-mib", mem_mib, "--minutes", minutes, "--name", name]
        if gpu:
            args.append("--gpu")
        if node:
            args += ["--node", node]
        return self._call(args, script)

    def status(self, job_id: str) -> dict:
        return self._call(["status", job_id])

    def logs(self, job_id: str) -> dict:
        return self._call(["logs", job_id])

    def cancel(self, job_id: str) -> dict:
        return self._call(["cancel", job_id])


def clean_node(raw: dict) -> dict:
    out = {}
    for k in ("node", "python", "mea_repo", "nas"):
        v = str(raw.get(k) or "").strip()
        out[k] = v.rstrip("/") if len(v) > 1 else v
    return out


def node_problems(nodes: list[dict]) -> list[str]:
    errs = []
    if not nodes:
        errs.append("Add the cluster's computers under Settings → Where analyses run.")
    seen = set()
    for n in nodes:
        name = n.get("node") or ""
        if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
            errs.append(f"“{name}” is not a computer name.")
            continue
        if name in seen:
            errs.append(f"{name} is listed twice.")
        seen.add(name)
        for k, what in (("python", "analysis Python"), ("mea_repo", "MEA-Analysis folder"),
                        ("nas", "NAS folder")):
            v = n.get(k) or ""
            if not v.startswith("/") or "'" in v or "\n" in v:
                errs.append(f"{name}: give its {what} as a full path.")
    return errs


def token_for(project: str, date: str, unique: str) -> str:
    t = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{project}-{date}-{unique}")
    return t[:120]


def _q(s: str) -> str:
    return shlex.quote(str(s))


def job_script(*, token: str, project: str, date: str, nodes: list[dict], nas_rel: str,
               recordings: list[str], args: list, scratch_root: str, results_root: str,
               hdf5_plugin_path: str, target_rel: str = "") -> str:
    """The batch script for one date. `args` are the pipeline's arguments
    after the input folder; the special value OUT stands for the job's output
    folder on the cluster computer. Every value is quoted for bash."""
    for p in (scratch_root, results_root):
        if not p.startswith("/") or len(PurePosixPath(p).parts) < 3:
            raise ValueError(f"{p} is not a safe folder for cluster jobs")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", token):
        raise ValueError(f"bad job token {token!r}")
    cases = "".join(
        f"  {_q(n['node'])}) PY={_q(n['python'])}; REPO={_q(n['mea_repo'])}; NAS={_q(n['nas'])} ;;\n"
        for n in nodes)
    argv = " ".join('"$W/out"' if a is OUT else _q(a) for a in args)
    target = '"$W/.input/$P/$D"' + (f"/{_q(target_rel)}" if target_rel else "")
    recs = " ".join(_q(r) for r in recordings)
    return f"""#!/bin/bash
# MEA Bench job for {project} {date}. Written by MEA Bench; do not edit.
set -u
umask 002
TOKEN={_q(token)}; P={_q(project)}; D={_q(date)}
NODE=$(hostname)
case "$NODE" in
{cases}  *) echo "MEA-BENCH: no settings for this computer ($NODE)"; exit {EXIT_NO_NODE_SETTINGS} ;;
esac
SCRATCH={_q(scratch_root)}
W="$SCRATCH/$TOKEN"
OUT={_q(results_root)}/"$TOKEN"
SRC="$NAS"/{_q(nas_rel)}
export HDF5_PLUGIN_PATH={_q(hdf5_plugin_path)}
echo "MEA-BENCH node=$NODE job=${{SLURM_JOB_ID:-?}} cpus=${{SLURM_CPUS_PER_TASK:-?}} gpu=${{CUDA_VISIBLE_DEVICES:-none}}"
echo "MEA-BENCH python=$PY repo=$REPO recordings=$SRC"

# Every way out goes through here, and the scratch copy goes with it. The one
# exception is a results copy that did not check out (KEEP=1): then the
# scratch copy is the only whole one.
KEEP=0
finish() {{
  if [ "$KEEP" != 1 ] && [ -d "$W" ]; then rm -rf -- "$W"; echo "MEA-BENCH scratch deleted"; fi
  printf '%s\\n' "$1" > "$OUT/exit_code.tmp" && mv -f "$OUT/exit_code.tmp" "$OUT/exit_code"
  echo "MEA-BENCH finished exit=$1"
  exit "$1"
}}
# Only ever this job's own folder inside the scratch folder.
case "$W" in "$SCRATCH"/?*) ;; *) echo "MEA-BENCH: refusing scratch folder $W"; exit {EXIT_SETUP} ;; esac
# Stopped while copying, before the analysis starts. Slurm stops the copy
# too, so this runs at once.
trap 'echo "MEA-BENCH: stop requested"; finish 143' TERM INT
mkdir -p "$OUT" || exit {EXIT_SETUP}
rm -rf -- "$W"
mkdir -p "$W/out" "$W/.input/$P/$D" "$W/.shim" || finish {EXIT_SETUP}
if [ -d "$OUT/seed" ]; then
  cp -a "$OUT/seed/." "$W/out/" || finish {EXIT_SETUP}
  echo "MEA-BENCH earlier results copied in"
fi

# The recordings, read from the NAS and never written there.
for rel in {recs}; do
  dst="$W/.input/$P/$D/$rel"
  mkdir -p "$(dirname "$dst")" || finish {EXIT_SETUP}
  cp -- "$SRC/$rel" "$dst" || {{ echo "MEA-BENCH: could not copy $SRC/$rel"; finish {EXIT_COPY_INPUT}; }}
  meta="$(dirname "$SRC/$rel")/.metadata"
  if [ -f "$meta" ]; then cp -- "$meta" "$(dirname "$dst")/" || true; fi
done
echo "MEA-BENCH recordings copied to $NODE:$W"

# The pipeline starts each well with a bare python3: make that this Python.
cat > "$W/.shim/python3" <<MEA_SHIM
#!/bin/sh
exec "$PY" "\\$@"
MEA_SHIM
chmod +x "$W/.shim/python3"
export PATH="$W/.shim:$PATH" PYTORCH_ALLOC_CONF=expandable_segments:True
VENV=$(dirname "$(dirname "$PY")")
if [ -f "$VENV/pyvenv.cfg" ]; then export VIRTUAL_ENV="$VENV"; unset PYTHONHOME; fi
echo "------------------------------------------------------------------------"

# In its own process group, so a cancel reaches every well it started.
setsid "$PY" "$REPO/run_pipeline_driver.py" {target} {argv} &
child=$!
stopping=0
trap 'stopping=1; echo "MEA-BENCH: stop requested"; kill -TERM -- -"$child" 2>/dev/null || kill -TERM "$child" 2>/dev/null' TERM INT
wait "$child"; rc=$?
while kill -0 "$child" 2>/dev/null; do wait "$child"; rc=$?; done
echo "------------------------------------------------------------------------"
if [ "$stopping" = 1 ]; then
  # Slurm kills the job 30 s after asking it to stop. Bring back what fits
  # in that time (finished wells), then delete the scratch copy regardless.
  mkdir -p "$OUT/results" && timeout 15 rsync -a --exclude=binary/ "$W/out/" "$OUT/results/"
  finish 143
fi
echo "MEA-BENCH analysis exit=$rc"

# Results to the shared folder; scratch goes only once the copy is checked.
listing() {{ (cd "$1" && find . -name binary -prune -o -type f -printf '%P %s\\n' | LC_ALL=C sort); }}
mkdir -p "$OUT/results" && rsync -a --exclude=binary/ "$W/out/" "$OUT/results/"
if [ -n "$(listing "$W/out")" ] && [ "$(listing "$W/out")" = "$(listing "$OUT/results")" ] \\
   || [ -z "$(listing "$W/out")" ]; then
  rm -rf -- "$W"
  echo "MEA-BENCH results copied and checked; scratch deleted"
else
  echo "MEA-BENCH: the results copy did not match; scratch kept at $NODE:$W"
  KEEP=1
  finish {EXIT_COPY_RESULTS}
fi
finish "$rc"
"""


OUT = object()      # stands for the job's output folder in job_script(args=...)


def cleanup_script(*, token: str, scratch_root: str) -> str:
    """A job that deletes one date's scratch folder on the computer it ran
    on, for a job that was killed before it could do so itself."""
    if not scratch_root.startswith("/") or len(PurePosixPath(scratch_root).parts) < 3:
        raise ValueError(f"{scratch_root} is not a safe folder for cluster jobs")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", token) or token in (".", ".."):
        raise ValueError(f"bad job token {token!r}")
    return f"""#!/bin/bash
# MEA Bench scratch clean-up. Written by MEA Bench; do not edit.
set -u
W={_q(scratch_root)}/{_q(token)}
if [ -d "$W" ]; then rm -rf -- "$W" && echo "MEA-BENCH scratch deleted: $(hostname):$W"
else echo "MEA-BENCH nothing left at $(hostname):$W"; fi
"""


def listing(root) -> dict[str, int]:
    """{relative path: size} of the files under root, without binary/."""
    from pathlib import Path
    root = Path(root)
    out: dict[str, int] = {}
    if not root.is_dir():
        return out
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if "binary" in rel.parts or not p.is_file():
            continue
        out[str(rel)] = p.stat().st_size
    return out


def check_script(*, nodes: list[dict], sample_rel: str, results_root: str, scratch_root: str,
                 hdf5_plugin_path: str, sorting: bool, imports: list[str]) -> str:
    """A job that checks one cluster computer can run a date, as lab-jobs.
    Only reads, apart from one empty test folder it makes and removes in
    each of the shared results folder and the scratch folder. Prints one
    "CHECK <what> ok|FAIL <detail>" line per check."""
    cases = "".join(
        f"  {_q(n['node'])}) PY={_q(n['python'])}; REPO={_q(n['mea_repo'])}; NAS={_q(n['nas'])} ;;\n"
        for n in nodes)
    mods = " ".join(_q(m) for m in imports)
    probe = (
        "import importlib, json, sys\n"
        "bad = []\n"
        "for m in sys.argv[2:]:\n"
        "    try: importlib.import_module(m)\n"
        "    except Exception as e: bad.append(f'{m} ({type(e).__name__})')\n"
        "print('CHECK python', 'FAIL missing ' + ', '.join(bad) if bad else 'ok ' + sys.version.split()[0])\n"
        "if sys.argv[1] == '1':\n"
        "    try:\n"
        "        import torch\n"
        "        ok = torch.cuda.is_available()\n"
        "        if ok:\n"
        "            torch.zeros(8, device='cuda').sum().item()\n"
        "            f, t = torch.cuda.mem_get_info(0)\n"
        "            print('CHECK gpu ok', torch.cuda.get_device_name(0), f'{t/2**30:.0f} GB')\n"
        "        else: print('CHECK gpu FAIL torch sees no GPU')\n"
        "    except Exception as e: print('CHECK gpu FAIL', type(e).__name__, e)\n")
    decode = (
        "import sys\n"
        "try:\n"
        "    import h5py\n"
        "    with h5py.File(sys.argv[1], 'r') as f:\n"
        "        found = []\n"
        "        f.visititems(lambda n, o: found.append(n) if isinstance(o, h5py.Dataset) and n.endswith('raw') else None)\n"
        "        f[found[0]][:2, :100]\n"
        "    print('CHECK recording ok decoded', sys.argv[1].rsplit('/', 5)[-5])\n"
        "except Exception as e: print('CHECK recording FAIL', type(e).__name__, str(e)[:200])\n")
    return f"""#!/bin/bash
# MEA Bench: can this computer run a date? Only reads, apart from two test folders.
set -u
umask 002
NODE=$(hostname)
case "$NODE" in
{cases}  *) echo "CHECK settings FAIL no MEA Bench settings for $NODE"; exit 0 ;;
esac
echo "CHECK identity ok $(id -un) on $NODE"
export HDF5_PLUGIN_PATH={_q(hdf5_plugin_path)}
[ -x "$PY" ] && echo "CHECK python-path ok $PY" || echo "CHECK python-path FAIL no Python at $PY"
[ -f "$REPO/run_pipeline_driver.py" ] && echo "CHECK mea-analysis ok $REPO" || echo "CHECK mea-analysis FAIL no run_pipeline_driver.py in $REPO"
[ -d "$NAS" ] && [ -r "$NAS" ] && echo "CHECK nas ok $NAS" || echo "CHECK nas FAIL cannot read $NAS"
ls "$HDF5_PLUGIN_PATH"/libcompression.so >/dev/null 2>&1 && echo "CHECK hdf5-plugin ok" || echo "CHECK hdf5-plugin FAIL no MaxWell plugin in $HDF5_PLUGIN_PATH"
command -v rsync >/dev/null && echo "CHECK rsync ok" || echo "CHECK rsync FAIL rsync is not installed"
for d in {_q(results_root)} {_q(scratch_root)}; do
  t="$d/.check-$NODE-$$"
  if mkdir -p "$t" 2>/dev/null && rmdir "$t"; then echo "CHECK write ok $d"; else echo "CHECK write FAIL cannot write in $d"; fi
done
if [ -x "$PY" ]; then
  "$PY" -c {_q(probe)} {'1' if sorting else '0'} {mods} 2>&1 | grep '^CHECK'
  if [ -n {_q(sample_rel)} ]; then "$PY" -c {_q(decode)} "$NAS"/{_q(sample_rel)} 2>&1 | grep '^CHECK'; fi
fi
echo "CHECK done"
"""


def parse_check(text: str) -> list[dict]:
    out = []
    for line in (text or "").splitlines():
        if not line.startswith("CHECK ") or line == "CHECK done":
            continue
        parts = line.split(" ", 3)
        what = parts[1] if len(parts) > 1 else "?"
        verdict = parts[2] if len(parts) > 2 else ""
        out.append({"what": what, "ok": verdict == "ok", "say": parts[3] if len(parts) > 3 else ""})
    return out
