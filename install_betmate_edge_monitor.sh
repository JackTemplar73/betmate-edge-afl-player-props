#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related"
PLIST_NAME="com.merlin.betmate-edge-monitor.plist"
SOURCE_PLIST="$PROJECT_ROOT/$PLIST_NAME"
TARGET_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$TARGET_DIR/$PLIST_NAME"

mkdir -p "$TARGET_DIR"
cp "$SOURCE_PLIST" "$TARGET_PLIST"
chmod 644 "$TARGET_PLIST"
chmod +x "$PROJECT_ROOT/monitor_betmate_edge.sh"

launchctl bootout "gui/$(id -u)" "$TARGET_PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$TARGET_PLIST"
launchctl enable "gui/$(id -u)/com.merlin.betmate-edge-monitor"
launchctl kickstart -k "gui/$(id -u)/com.merlin.betmate-edge-monitor"

echo "Installed and started $TARGET_PLIST"
