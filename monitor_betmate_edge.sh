#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related"
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
PYTHON_BIN="/opt/homebrew/bin/python3"
CURL_BIN="/usr/bin/curl"
LAUNCHCTL_BIN="/bin/launchctl"
USER_ID="$(id -u)"
REFRESH_LABEL="com.merlin.betmate-edge-refresh"
PUBLIC_LABEL="com.merlin.betmate-edge-public"
NGROK_LABEL="com.merlin.betmate-edge-ngrok"
LOG_DIR="$PROJECT_ROOT/monitor_logs"
MONITOR_LOG="$LOG_DIR/betmate_edge_monitor.log"
LATEST_TUNNEL_FILE="$LOG_DIR/latest_ngrok_url.txt"

PUBLIC_HEALTH_URL="https://gestureless-rancorously-zariah.ngrok-free.dev/health"
PUBLIC_REFRESH_URL="https://gestureless-rancorously-zariah.ngrok-free.dev/refresh"
LOCAL_REFRESH_HEALTH_URL="http://127.0.0.1:8765/health"
LOCAL_PUBLIC_HEALTH_URL="http://127.0.0.1:8000/health"
NGROK_API_URL="http://127.0.0.1:4040/api/tunnels"

ODDS_API_KEY="${THE_ODDS_API_KEY:-}"
if [[ -z "$ODDS_API_KEY" ]]; then
  echo "THE_ODDS_API_KEY is not set; monitor cannot verify live refresh." >&2
  exit 1
fi
REFRESH_TOKEN="${CODEX_REFRESH_TOKEN:-$(cat "$PROJECT_ROOT/codex_refresh_token.txt" 2>/dev/null || true)}"

mkdir -p "$LOG_DIR"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  echo "[$(timestamp)] $*" >> "$MONITOR_LOG"
}

within_schedule() {
  local hour
  hour="$(date +%H)"

  if [ "$hour" -lt 8 ] || [ "$hour" -gt 21 ]; then
    return 1
  fi

  return 0
}

http_code() {
  local url="$1"
  "$CURL_BIN" -s -o /dev/null -w '%{http_code}' "$url" || true
}

refresh_endpoint_code() {
  "$CURL_BIN" -s -o /dev/null -w '%{http_code}' \
    -X POST "$PUBLIC_REFRESH_URL" \
    -H "Authorization: Bearer $REFRESH_TOKEN" \
    -H 'Content-Type: application/json' \
    -d '{}' || true
}

kickstart_agent() {
  local label="$1"
  "$LAUNCHCTL_BIN" enable "gui/$USER_ID/$label" >/dev/null 2>&1 || true
  "$LAUNCHCTL_BIN" kickstart -k "gui/$USER_ID/$label" >/dev/null 2>&1 || true
}

restart_agents() {
  kickstart_agent "$REFRESH_LABEL"
  kickstart_agent "$PUBLIC_LABEL"
  kickstart_agent "$NGROK_LABEL"
}

record_tunnel_url() {
  local payload url
  payload="$("$CURL_BIN" -s "$NGROK_API_URL" || true)"
  url="$(printf '%s' "$payload" | "$PYTHON_BIN" -c '
import json
import sys

raw = sys.stdin.read().strip()
if not raw:
    raise SystemExit(0)

try:
    payload = json.loads(raw)
except Exception:
    raise SystemExit(0)

for tunnel in payload.get("tunnels") or []:
    public_url = tunnel.get("public_url", "")
    if public_url.startswith("https://"):
        print(public_url)
        break
')"
  if [ -n "$url" ]; then
    printf '%s\n' "$url" > "$LATEST_TUNNEL_FILE"
  fi
}

wait_for_local_services() {
  local tries=0 refresh_code public_code
  while [ "$tries" -lt 30 ]; do
    refresh_code="$(http_code "$LOCAL_REFRESH_HEALTH_URL")"
    public_code="$(http_code "$LOCAL_PUBLIC_HEALTH_URL")"
    if [ "$refresh_code" = "200" ] && [ "$public_code" = "200" ]; then
      return 0
    fi
    tries=$((tries + 1))
    sleep 2
  done
  return 1
}

wait_for_public_health() {
  local tries=0 code
  while [ "$tries" -lt 30 ]; do
    code="$(http_code "$PUBLIC_HEALTH_URL")"
    if [ "$code" = "200" ]; then
      return 0
    fi
    tries=$((tries + 1))
    sleep 2
  done
  return 1
}

restart_stack() {
  log "Restarting BetMate Edge stack"
  restart_agents

  if ! wait_for_local_services; then
    log "Local services failed health checks after restart"
    return 1
  fi

  record_tunnel_url

  if ! wait_for_public_health; then
    log "Public health endpoint failed after restart"
    return 1
  fi

  log "Restart successful"
  return 0
}

main() {
  if ! within_schedule; then
    log "Outside schedule window, skipping check"
    exit 0
  fi

  local public_code refresh_code local_public_code public_refresh_code
  public_code="$(http_code "$PUBLIC_HEALTH_URL")"
  refresh_code="$(http_code "$LOCAL_REFRESH_HEALTH_URL")"
  local_public_code="$(http_code "$LOCAL_PUBLIC_HEALTH_URL")"
  public_refresh_code="$(refresh_endpoint_code)"

  log "Health check public=$public_code local_refresh=$refresh_code local_public=$local_public_code public_refresh=$public_refresh_code"

  if [ "$public_code" = "200" ] && [ "$refresh_code" = "200" ] && [ "$local_public_code" = "200" ] && { [ "$public_refresh_code" = "200" ] || [ "$public_refresh_code" = "409" ]; }; then
    record_tunnel_url
    log "Stack healthy, no action needed"
    exit 0
  fi

  if restart_stack; then
    exit 0
  fi

  exit 1
}

main "$@"
