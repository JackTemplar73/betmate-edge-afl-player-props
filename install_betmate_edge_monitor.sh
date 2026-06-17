#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related"
TARGET_DIR="$HOME/Library/LaunchAgents"
PLISTS=(
  "com.merlin.betmate-edge-refresh.plist"
  "com.merlin.betmate-edge-public.plist"
  "com.merlin.betmate-edge-ngrok.plist"
  "com.merlin.betmate-edge-monitor.plist"
)
SCRIPTS=(
  "monitor_betmate_edge.sh"
  "launch_betmate_edge_refresh.sh"
  "launch_betmate_edge_public.sh"
  "launch_betmate_edge_ngrok.sh"
)

mkdir -p "$TARGET_DIR"

for script_name in "${SCRIPTS[@]}"; do
  chmod +x "$PROJECT_ROOT/$script_name"
done

for plist_name in "${PLISTS[@]}"; do
  source_plist="$PROJECT_ROOT/$plist_name"
  target_plist="$TARGET_DIR/$plist_name"
  cp "$source_plist" "$target_plist"
  chmod 644 "$target_plist"
  launchctl bootout "gui/$(id -u)" "$target_plist" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$target_plist"
done

for label in \
  "com.merlin.betmate-edge-refresh" \
  "com.merlin.betmate-edge-public" \
  "com.merlin.betmate-edge-ngrok" \
  "com.merlin.betmate-edge-monitor"
do
  launchctl enable "gui/$(id -u)/$label"
  launchctl kickstart -k "gui/$(id -u)/$label"
done

echo "Installed and started BetMate Edge service agents and monitor"
