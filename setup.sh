#!/usr/bin/env bash
# One-time setup for Orchestration-MEA.
#
#   ./setup.sh                          # auto-detect ../MEA-Analysis
#   ./setup.sh /path/to/MEA-Analysis    # or point at it explicitly
#
# Creates a virtualenv, installs dependencies, and writes config.env.
# Everything stays inside this directory — nothing is installed system-wide and
# no root access is needed.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

VENV="$HERE/.venv"
CONFIG="$HERE/config.env"
MIN_PY="3.9"

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m%s\033[0m\n' "$*" >&2; }
die()  { printf '\033[31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# ── Python ──────────────────────────────────────────────────────────────────
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null || die "$PY not found. Install Python >= $MIN_PY."
PY_VER="$("$PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
"$PY" -c "import sys;sys.exit(0 if sys.version_info[:2]>=(3,9) else 1)" \
  || die "Python $PY_VER is too old — need >= $MIN_PY."
say "Python $PY_VER  ($(command -v "$PY"))"

# ── Virtualenv ──────────────────────────────────────────────────────────────
if [[ -d "$VENV" ]]; then
  say "Reusing existing virtualenv at .venv"
else
  say "Creating virtualenv at .venv"
  "$PY" -m venv "$VENV" || die "Could not create the virtualenv. On Debian/Ubuntu: apt install python3-venv"
fi

say "Installing dependencies"
"$VENV/bin/pip" install --upgrade pip --quiet
"$VENV/bin/pip" install -r "$HERE/requirements.txt" --quiet
say "  installed: $("$VENV/bin/pip" list --format=freeze | wc -l) packages"

# ── Locate MEA-Analysis ─────────────────────────────────────────────────────
MEA_REPO="${1:-${MEA_REPO:-}}"
if [[ -z "$MEA_REPO" ]]; then
  for c in "$HERE/../MEA-Analysis" "$HERE/../MEA_Analysis"; do
    [[ -f "$c/run_pipeline_driver.py" ]] && MEA_REPO="$(cd "$c" && pwd)" && break
  done
fi

if [[ -n "$MEA_REPO" && -f "$MEA_REPO/run_pipeline_driver.py" ]]; then
  MEA_REPO="$(cd "$MEA_REPO" && pwd)"
  say "MEA-Analysis: $MEA_REPO"
else
  warn "MEA-Analysis not found."
  warn "  The activity scan works without it; the Network analysis does not."
  warn "  Set MEA_REPO in config.env once you have a checkout."
  MEA_REPO="${MEA_REPO:-/path/to/MEA-Analysis}"
fi

# ── Config ──────────────────────────────────────────────────────────────────
if [[ -f "$CONFIG" ]]; then
  say "Keeping existing config.env"
else
  say "Writing config.env"
  cat > "$CONFIG" <<EOF
# Orchestration-MEA — per-machine settings. Not committed.

# Checkout of the analysis repo this orchestrator drives.
MEA_REPO=$MEA_REPO

# UI port (reach it over an SSH tunnel; the UI is unauthenticated).
UI_PORT=8000

# Watcher state, job config, and per-run logs. Keep this persistent or the
# watcher forgets which runs it has already processed.
WORK_DIR=$HERE/.mea-watcher

# Needed only if you run the MEA pipeline natively from this shell: MaxWell's
# HDF5 compression plugin, for reading raw traces. The activity scan does not
# need it — it reads only uncompressed spike data.
# HDF5_PLUGIN_PATH=$HOME/hdf5/plugins
EOF
fi

mkdir -p "$HERE/.mea-watcher/logs"

# ── Verify ──────────────────────────────────────────────────────────────────
say "Verifying"
MEA_REPO="$MEA_REPO" "$VENV/bin/python" - <<'PY'
import sys, logging
sys.path.insert(0, "orchestration")
logging.basicConfig(level=logging.INFO, format="  %(levelname)-7s %(message)s")
import driver_schema
from mea_repo import find_mea_repo, report
print(f"  driver options mirrored: {len(driver_schema.FIELDS)}")
report(find_mea_repo(), strict=False)
PY

cat <<EOF

$(say "Setup complete.")

  Start the UI:      ./run.sh
  Activity scan:     .venv/bin/python orchestration/activity_scan.py <data-dir> --output-dir <out>
  Per-well status:   .venv/bin/python orchestration/checkpoints.py <analysed-dir>

  Edit config.env to change the MEA repo path, port, or work directory.
EOF
