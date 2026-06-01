#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [[ -z "${THE_ODDS_API_KEY:-}" ]]; then
  echo "THE_ODDS_API_KEY is not set."
  echo 'Run: export THE_ODDS_API_KEY="YOUR_KEY_HERE"'
  exit 1
fi

cd "$ROOT/code"
./run_hosted_betmate_edge.sh

