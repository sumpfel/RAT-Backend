#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# RAT-Backend launcher (Linux / macOS)
#   - creates a Python virtual environment (.venv) if missing
#   - installs/updates the dependencies from src/requirements.txt
#   - starts the FastAPI server with uvicorn
#
# Usage:
#   ./run.sh                 # http://127.0.0.1:8000
#   HOST=0.0.0.0 PORT=8080 ./run.sh   # bind on all interfaces, custom port
#   RELOAD=1 ./run.sh        # auto-reload on code changes (development)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# always run relative to this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
REQ="src/requirements.txt"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

# pick a python: prefer python3, fall back to python
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "ERROR: Python 3 is not installed or not on PATH." >&2
    exit 1
fi

# 1) virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo ">> Creating virtual environment in $VENV_DIR ..."
    "$PY" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 2) dependencies
echo ">> Installing dependencies from $REQ ..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r "$REQ"

# 3) run (uvicorn imports main:app from src/, so host/port are configurable here)
RELOAD_FLAG=""
if [ "${RELOAD:-0}" = "1" ]; then RELOAD_FLAG="--reload"; fi

echo ">> Starting RAT-Backend on http://$HOST:$PORT  (Swagger UI at /docs)"
cd src
exec python -m uvicorn main:app --host "$HOST" --port "$PORT" $RELOAD_FLAG
