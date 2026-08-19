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

# config.env is optional; flags and the environment still work without it.
if [[ -f "$HERE/config.env" ]]; then
  set -a; . "$HERE/config.env"; set +a
fi

# Interpreter that runs this tool. In shared mode this is the pipeline's own
# environment; in separate mode it is the local virtualenv.
PY_BIN="${PYTHON:-$HERE/.venv/bin/python}"
[[ -x "$PY_BIN" ]] || {
  echo "Interpreter not found: $PY_BIN" >&2
  echo "Run ./setup.sh first, or set PYTHON in config.env." >&2; exit 1; }

PORT="${UI_PORT:-8000}"
WORK="${WORK_DIR:-$HERE/.mea-watcher}"

# Bind to localhost by default: the UI is unauthenticated and can browse the
# filesystem, so it should be reached over an SSH tunnel rather than exposed.
#   ssh -N -L 8000:127.0.0.1:8000 user@server
HOST="${UI_HOST:-127.0.0.1}"

exec "$PY_BIN" orchestration/api.py \
  --host "$HOST" --port "$PORT" --work-dir "$WORK" \
  ${MEA_REPO:+--mea-repo "$MEA_REPO"} "$@"
