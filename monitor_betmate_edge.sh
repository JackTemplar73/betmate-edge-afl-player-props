#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related"
LOG_DIR="$PROJECT_ROOT/monitor_logs"
REFRESH_LOG="$LOG_DIR/betmate_edge_refresh_server.log"
PUBLIC_LOG="$LOG_DIR/betmate_edge_public_server.log"
NGROK_LOG="$LOG_DIR/betmate_edge_ngrok.log"
MONITOR_LOG="$LOG_DIR/betmate_edge_monitor.log"
LATEST_TUNNEL_FILE="$LOG_DIR/latest_ngrok_url.txt"

PUBLIC_HEALTH_URL="https://gestureless-rancorously-zariah.ngrok-free.dev/health"
LOCAL_REFRESH_HEALTH_URL="http://127.0.0.1:8765/health"
LOCAL_PUBLIC_HEALTH_URL="http://127.0.0.1:8000/health"
NGROK_API_URL="http://127.0.0.1:4040/api/tunnels"

ODDS_API_KEY="${THE_ODDS_API_KEY:-026c34657c294b1af47274812988496e}"

mkdir -p "$LOG_DIR"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  echo "[$(timestamp)] $*" >> "$MONITOR_LOG"
}

within_schedule() {
  local weekday hour
  weekday="$(date +%u)"
  hour="$(date +%H)"

  case "$weekday" in
    3|4|5|6|7) ;;
    *)
      return 1
      ;;
  esac

  if [ "$hour" -lt 7 ] || [ "$hour" -gt 22 ]; then
    return 1
  fi

  return 0
}

http_code() {
  local url="$1"
  curl -s -o /dev/null -w '%{http_code}' "$url" || true
}

kill_matching() {
  local pattern="$1"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill >/dev/null 2>&1 || true
    sleep 2
  fi
}

start_refresh_server() {
  nohup env THE_ODDS_API_KEY="$ODDS_API_KEY" python3 "$PROJECT_ROOT/betmate_edge_refresh_server.py" >> "$REFRESH_LOG" 2>&1 &
}

start_public_server() {
  nohup python3 "$PROJECT_ROOT/betmate_edge_public_server.py" >> "$PUBLIC_LOG" 2>&1 &
}

start_ngrok() {
  nohup ngrok http 8000 >> "$NGROK_LOG" 2>&1 &
}

record_tunnel_url() {
  local payload url
  payload="$(curl -s "$NGROK_API_URL" || true)"
  url="$(PAYLOAD_JSON="$payload" python3 -c '
import json
import os

raw = os.environ.get("PAYLOAD_JSON", "").strip()
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
  kill_matching "python3 $PROJECT_ROOT/betmate_edge_refresh_server.py"
  kill_matching "python3 $PROJECT_ROOT/betmate_edge_public_server.py"
  kill_matching "ngrok http 8000"

  start_refresh_server
  start_public_server
  start_ngrok

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

  local public_code refresh_code local_public_code
  public_code="$(http_code "$PUBLIC_HEALTH_URL")"
  refresh_code="$(http_code "$LOCAL_REFRESH_HEALTH_URL")"
  local_public_code="$(http_code "$LOCAL_PUBLIC_HEALTH_URL")"

  log "Health check public=$public_code local_refresh=$refresh_code local_public=$local_public_code"

  if [ "$public_code" = "200" ] && [ "$refresh_code" = "200" ] && [ "$local_public_code" = "200" ]; then
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
