#!/usr/bin/env bash
# One-time setup for Orchestration-MEA.
#
#   ./setup.sh                          # recommended: install into the pipeline's env
#   ./setup.sh --python /path/to/python # into a specific environment
#   ./setup.sh --separate               # own virtualenv (UI + activity scan only)
#   ./setup.sh --mea-repo /path/to/MEA-Analysis
#
# WHICH MODE?
#
#   Shared (default) — installs fastapi + uvicorn into the environment
#   MEA-Analysis already runs in. One environment, nothing to configure, and
#   the driver is launched with an interpreter that definitely has pandas,
#   torch, kilosort and spikeinterface. Adds ~2 packages, not ~10 GB.
#
#   Separate (--separate) — creates .venv here with its own numpy/h5py/
#   matplotlib. Use on a machine without the pipeline installed: the UI and the
#   activity scan work, spike sorting does not.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
CONFIG="$HERE/config.env"

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
info() { printf '  %s\n' "$*"; }
warn() { printf '\033[33m%s\033[0m\n' "$*" >&2; }
die()  { printf '\033[31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

MODE=""; TARGET_PY=""; MEA_REPO="${MEA_REPO:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --separate)  MODE="separate"; shift ;;
    --python)    TARGET_PY="${2:?--python needs a path}"; MODE="shared"; shift 2 ;;
    --mea-repo)  MEA_REPO="${2:?--mea-repo needs a path}"; shift 2 ;;
    -h|--help)   sed -n '2,20p' "$0"; exit 0 ;;
    *)           [[ -z "$MEA_REPO" ]] && MEA_REPO="$1" || die "Unexpected argument: $1"; shift ;;
  esac
done

# ── Locate MEA-Analysis ─────────────────────────────────────────────────────
if [[ -z "$MEA_REPO" ]]; then
  for c in "$HERE/../MEA-Analysis" "$HERE/../MEA_Analysis"; do
    [[ -f "$c/run_pipeline_driver.py" ]] && MEA_REPO="$(cd "$c" && pwd)" && break
  done
fi
if [[ -n "$MEA_REPO" && -f "$MEA_REPO/run_pipeline_driver.py" ]]; then
  MEA_REPO="$(cd "$MEA_REPO" && pwd)"
  say "MEA-Analysis: $MEA_REPO"
else
  warn "MEA-Analysis not found — the activity scan will work, spike sorting will not."
  MEA_REPO="${MEA_REPO:-/path/to/MEA-Analysis}"
fi

# ── Find the pipeline's interpreter ─────────────────────────────────────────
# The one that can already import the analysis stack.
probe() {  # $1 = interpreter
  "$1" - <<'PY' 2>/dev/null
import importlib, sys
need = ["pandas", "h5py", "numpy", "spikeinterface"]
missing = [m for m in need if importlib.util.find_spec(m) is None]
print(("OK " if not missing else "MISSING ") + ",".join(missing))
PY
}

if [[ -z "$TARGET_PY" && "$MODE" != "separate" ]]; then
  say "Looking for the environment MEA-Analysis runs in"
  for cand in "$MEA_REPO/.venv/bin/python" "$MEA_REPO/venv/bin/python" \
              "$(command -v python3 || true)" "$(command -v python || true)"; do
    [[ -x "${cand:-}" ]] || continue
    res="$(probe "$cand" || true)"
    case "$res" in
      OK*)      info "$cand  →  has the analysis stack"; TARGET_PY="$cand"; break ;;
      MISSING*) info "$cand  →  missing ${res#MISSING }" ;;
      *)        info "$cand  →  could not probe" ;;
    esac
  done
fi

# ── Decide the mode ─────────────────────────────────────────────────────────
if [[ -n "$TARGET_PY" && "$MODE" != "separate" ]]; then
  MODE="shared"
elif [[ "$MODE" != "separate" ]]; then
  warn ""
  warn "No environment found with the analysis stack installed."
  warn "Falling back to a separate virtualenv: the UI and activity scan will"
  warn "work, but spike sorting needs the pipeline's own environment."
  warn "Re-run with --python /path/to/that/env once you know it."
  warn ""
  MODE="separate"
fi

# ── Install ─────────────────────────────────────────────────────────────────
if [[ "$MODE" == "shared" ]]; then
  say "Installing into the pipeline's environment"
  info "$TARGET_PY"
  # Only fastapi + uvicorn: everything else is already present, and resolving
  # the full set here could move pinned versions the pipeline depends on.
  "$TARGET_PY" -m pip install --user --upgrade-strategy only-if-needed \
      -r "$HERE/requirements-web.txt" --quiet \
    || "$TARGET_PY" -m pip install --upgrade-strategy only-if-needed \
      -r "$HERE/requirements-web.txt" --quiet \
    || die "Could not install fastapi/uvicorn into $TARGET_PY"
  RUN_PY="$TARGET_PY"
else
  say "Creating a separate virtualenv at .venv"
  PY="${PYTHON:-python3}"
  command -v "$PY" >/dev/null || die "$PY not found. Install Python >= 3.9."
  "$PY" -c "import sys;sys.exit(0 if sys.version_info[:2]>=(3,9) else 1)" \
    || die "Python too old — need >= 3.9."
  [[ -d "$HERE/.venv" ]] || "$PY" -m venv "$HERE/.venv" \
    || die "Could not create the virtualenv. On Debian/Ubuntu: apt install python3-venv"
  "$HERE/.venv/bin/pip" install --upgrade pip --quiet
  "$HERE/.venv/bin/pip" install -r "$HERE/requirements.txt" --quiet
  RUN_PY="$HERE/.venv/bin/python"
fi

# ── Config ──────────────────────────────────────────────────────────────────
if [[ -f "$CONFIG" ]]; then
  say "Keeping existing config.env"
else
  say "Writing config.env"
  cat > "$CONFIG" <<EOF
# Orchestration-MEA — per-machine settings. Not committed.

MEA_REPO=$MEA_REPO

# Interpreter that runs this tool.
PYTHON=$RUN_PY

# Interpreter used to launch run_pipeline_driver.py. Blank = auto-detect.
# In shared mode this is the same environment, so blank is correct.
DRIVER_PYTHON=$([[ "$MODE" == "shared" ]] && echo "" || echo "# set me: the env MEA-Analysis runs in")

UI_PORT=8000
WORK_DIR=$HERE/.mea-watcher
EOF
fi
mkdir -p "$HERE/.mea-watcher/logs"

# ── Verify ──────────────────────────────────────────────────────────────────
say "Verifying"
MEA_REPO="$MEA_REPO" "$RUN_PY" - <<'PY'
import sys, logging
sys.path.insert(0, "orchestration")
logging.basicConfig(level=logging.INFO, format="  %(levelname)-7s %(message)s")
import driver_schema
from mea_repo import find_mea_repo, report, find_driver_python
print(f"  driver options mirrored: {len(driver_schema.FIELDS)}")
repo = find_mea_repo()
report(repo, strict=False)
res = find_driver_python(repo)
state = "OK" if res.get("ok") else f"MISSING {', '.join(res.get('missing') or ['?'])}"
print(f"  pipeline interpreter: {res.get('python')} [{res.get('source')}] — {state}")
if not res.get("ok"):
    print("  -> Spike sorting will fail. Set DRIVER_PYTHON in config.env, or")
    print("     re-run: ./setup.sh --python /path/to/the/pipeline/env")
PY

cat <<EOF

$(say "Setup complete — $MODE mode.")

  Start the UI:    ./run.sh
  Activity scan:   $RUN_PY orchestration/activity_scan.py <data-dir> --output-dir <out>
  Well status:     $RUN_PY orchestration/checkpoints.py <analysed-dir>
EOF
