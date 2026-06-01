#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_ROOT="$(cd "$ROOT/.." && pwd)"
STATE_SEED_DIR="$BUNDLE_ROOT/state_seed"
TARGET_DIR="${1:-$ROOT}"

mkdir -p "$TARGET_DIR"

cp "$STATE_SEED_DIR/aflplayerprops_bet_history.csv" "$TARGET_DIR/aflplayerprops_bet_history.csv"
cp "$STATE_SEED_DIR/player_prop_settlement.csv" "$TARGET_DIR/player_prop_settlement.csv"
cp "$STATE_SEED_DIR/oddsapi_wheelo_ev_qi.csv" "$TARGET_DIR/oddsapi_wheelo_ev_qi.csv"
cp "$STATE_SEED_DIR/wheelo_today_player_pack.csv" "$TARGET_DIR/wheelo_today_player_pack.csv"
cp "$STATE_SEED_DIR/wheelo_today_team_context.csv" "$TARGET_DIR/wheelo_today_team_context.csv"
cp "$STATE_SEED_DIR/oddsapi_events.json" "$TARGET_DIR/oddsapi_events.json"
cp "$STATE_SEED_DIR/oddsapi_car_gee_props.json" "$TARGET_DIR/oddsapi_car_gee_props.json"
cp "$STATE_SEED_DIR/oddsapi_syd_rich_props.json" "$TARGET_DIR/oddsapi_syd_rich_props.json"
cp "$STATE_SEED_DIR/oddsapi_bris_fre_props.json" "$TARGET_DIR/oddsapi_bris_fre_props.json"
cp "$STATE_SEED_DIR/oddsapi_wb_coll_props.json" "$TARGET_DIR/oddsapi_wb_coll_props.json"
cp "$STATE_SEED_DIR/oddsapi_melb_gws_props.json" "$TARGET_DIR/oddsapi_melb_gws_props.json"
cp "$STATE_SEED_DIR/oddsapi_wce_ess_props.json" "$TARGET_DIR/oddsapi_wce_ess_props.json"
cp "$STATE_SEED_DIR/afl_match_mapping.csv" "$TARGET_DIR/afl_match_mapping.csv"
cp "$STATE_SEED_DIR/afl_round_mapping.csv" "$TARGET_DIR/afl_round_mapping.csv"

echo "Seeded runtime state into $TARGET_DIR"
