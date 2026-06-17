#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date '+%Y%m%d_%H%M%S')"
OUT_DIR="$ROOT/wheelo_snapshots/$STAMP"
mkdir -p "$OUT_DIR"

curl -L "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/2026.json" \
  -o "$OUT_DIR/wheelo_player_stats_2026.json"
curl -L "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last5.json" \
  -o "$OUT_DIR/wheelo_player_stats_last5.json"
curl -L "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last10.json" \
  -o "$OUT_DIR/wheelo_player_stats_last10.json"
curl -L "https://www.wheeloratings.com/src/afl_stats/team_stats/afl/2026.json" \
  -o "$OUT_DIR/wheelo_team_stats_2026.json"
curl -L "https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last5.json" \
  -o "$OUT_DIR/wheelo_team_stats_last5.json"
curl -L "https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last10.json" \
  -o "$OUT_DIR/wheelo_team_stats_last10.json"

cat > "$OUT_DIR/SOURCE.txt" <<EOF
Captured: $STAMP
Sources:
- https://www.wheeloratings.com/src/afl_stats/player_stats/afl/2026.json
- https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last5.json
- https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last10.json
- https://www.wheeloratings.com/src/afl_stats/team_stats/afl/2026.json
- https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last5.json
- https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last10.json
EOF

echo "$OUT_DIR"
