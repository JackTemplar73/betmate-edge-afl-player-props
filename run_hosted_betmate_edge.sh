#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

export BETMATE_REFRESH_HOST="${BETMATE_REFRESH_HOST:-127.0.0.1}"
export BETMATE_REFRESH_PORT="${BETMATE_REFRESH_PORT:-8765}"
export BETMATE_PUBLIC_HOST="${BETMATE_PUBLIC_HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"
export BETMATE_STATE_DIR="${BETMATE_STATE_DIR:-/data}"

cd "$ROOT"

if [ -n "${RAILWAY_ENVIRONMENT:-}" ] || [ -d "${BETMATE_STATE_DIR}" ]; then
  "$ROOT/bootstrap_railway_state.sh"
fi

python3 betmate_edge_refresh_server.py &
refresh_pid=$!

cleanup() {
  kill "$refresh_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

python3 betmate_edge_public_server.py
