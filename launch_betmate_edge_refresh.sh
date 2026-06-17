#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related"
cd "$PROJECT_ROOT"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
if [[ -z "${THE_ODDS_API_KEY:-}" ]]; then
  echo "THE_ODDS_API_KEY is not set" >&2
  exit 1
fi
export THE_ODDS_API_KEY
export CODEX_REFRESH_TOKEN="${CODEX_REFRESH_TOKEN:-$(cat "$PROJECT_ROOT/codex_refresh_token.txt" 2>/dev/null || true)}"

exec /opt/homebrew/bin/python3 "$PROJECT_ROOT/betmate_edge_refresh_server.py"
