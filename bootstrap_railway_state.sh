#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
STATE_DIR="${BETMATE_STATE_DIR:-/data}"

mkdir -p "$STATE_DIR"

FILES=(
  "aflplayerprops_bet_history.csv"
  "afl_match_mapping.csv"
  "afl_round_mapping.csv"
  "player_prop_settlement.csv"
  "oddsapi_events.json"
  "oddsapi_wheelo_ev_qi.csv"
  "oddsapi_wheelo_ev_qi.md"
  "wheelo_today_player_pack.csv"
  "wheelo_today_player_pack.md"
  "wheelo_today_team_context.csv"
  "afl_player_props_walters_report.html"
  "afl_player_props_stk_haw_walters_report.html"
  "markov_bet_justifications.csv"
  "markov_bet_justifications.md"
  "wheelo_match_previews.html"
  "codex_refresh_token.txt"
)

DIRS=(
  "wheelo_snapshots"
  "official_afl_stats_json"
  "__pycache__"
)

link_path() {
  local source="$1"
  local target="$2"

  if [ -L "$target" ]; then
    return
  fi

  if [ -e "$target" ] && [ ! -e "$source" ]; then
    mv "$target" "$source"
  fi

  if [ ! -e "$source" ]; then
    if [ -d "$target" ]; then
      mkdir -p "$source"
    else
      : > "$source"
    fi
  fi

  rm -rf "$target"
  ln -s "$source" "$target"
}

for name in "${FILES[@]}"; do
  src="$STATE_DIR/$name"
  dst="$ROOT/$name"
  if [ ! -e "$src" ] && [ -e "$dst" ] && [ ! -L "$dst" ]; then
    cp "$dst" "$src"
  fi
  link_path "$src" "$dst"
done

for name in "${DIRS[@]}"; do
  src="$STATE_DIR/$name"
  dst="$ROOT/$name"
  mkdir -p "$src"
  link_path "$src" "$dst"
done

echo "Railway state bootstrapped from $STATE_DIR"
