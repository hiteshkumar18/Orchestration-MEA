#!/usr/bin/env bash
# Start the Orchestration-MEA control UI.
#
#   ./run.sh                 # foreground, using config.env
#   ./run.sh --port 8080     # override any api.py flag
#   ./run.sh --strict        # refuse to start if the driver options have drifted
#
# To keep it running after you log out, use tmux:
#   tmux new -s mea './run.sh'      then detach with Ctrl-b d
# or install the systemd user service — see docs/DEPLOYMENT.md.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# ── Read config.env safely ──────────────────────────────────────────────────
# Deliberately parsed, not sourced. Sourcing runs arbitrary shell: a stray line
# such as `DRIVER_PYTHON=# set me: ...` is read by bash as the `set` builtin and
# silently replaces this script's positional parameters, which then get passed
# to api.py as unrecognised arguments. Only known keys are accepted, and only
# as literal values.
CFG_MEA_REPO=""; CFG_PYTHON=""; CFG_DRIVER_PYTHON=""
CFG_UI_PORT=""; CFG_UI_HOST=""; CFG_WORK_DIR=""

if [[ -f "$HERE/config.env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"                       # tolerate CRLF
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]] || continue
    key="${BASH_REMATCH[1]}"; val="${BASH_REMATCH[2]}"
    val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
    # A value that starts with '#' is a leftover placeholder, not a setting.
    [[ "$val" =~ ^# ]] && val=""
    case "$key" in
      MEA_REPO)      CFG_MEA_REPO="$val" ;;
      PYTHON)        CFG_PYTHON="$val" ;;
      DRIVER_PYTHON) CFG_DRIVER_PYTHON="$val" ;;
      UI_PORT)       CFG_UI_PORT="$val" ;;
      UI_HOST)       CFG_UI_HOST="$val" ;;
      WORK_DIR)      CFG_WORK_DIR="$val" ;;
      *) printf 'Ignoring unknown setting in config.env: %s\n' "$key" >&2 ;;
    esac
  done < "$HERE/config.env"
fi

# Environment wins over config.env; command-line flags win over both.
MEA_REPO="${MEA_REPO:-$CFG_MEA_REPO}"
DRIVER_PYTHON="${DRIVER_PYTHON:-$CFG_DRIVER_PYTHON}"
PORT="${UI_PORT:-${CFG_UI_PORT:-8000}}"
WORK="${WORK_DIR:-${CFG_WORK_DIR:-$HERE/.mea-watcher}}"

# Bind to localhost by default: the UI is unauthenticated and can browse the
# filesystem, so it should be reached over an SSH tunnel rather than exposed.
#   ssh -N -L 8000:127.0.0.1:8000 user@server
HOST="${UI_HOST:-${CFG_UI_HOST:-127.0.0.1}}"

# Interpreter that runs this tool. In shared mode this is the pipeline's own
# environment; in separate mode it is the local virtualenv.
PY_BIN="${PYTHON:-${CFG_PYTHON:-$HERE/.venv/bin/python}}"
if [[ ! -x "$PY_BIN" ]]; then
  echo "Interpreter not found: $PY_BIN" >&2
  echo "Run ./setup.sh first, or set PYTHON in config.env." >&2
  exit 1
fi

[[ -n "$MEA_REPO" ]] && export MEA_REPO
[[ -n "$DRIVER_PYTHON" ]] && export MEA_DRIVER_PYTHON="$DRIVER_PYTHON"

exec "$PY_BIN" orchestration/api.py \
  --host "$HOST" --port "$PORT" --work-dir "$WORK" \
  ${MEA_REPO:+--mea-repo "$MEA_REPO"} "$@"
