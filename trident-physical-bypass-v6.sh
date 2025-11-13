#!/bin/sh
set -eu

TERMUX_PREFIX="/data/data/com.termux/files/usr/bin"
case ":$PATH:" in
  *:"$TERMUX_PREFIX":*) ;;
  *)
    export PATH="$TERMUX_PREFIX:$PATH"
    ;;
esac

LOG_DIR="${PHYSICAL_BRIDGE_LOG_DIR:-$HOME/sei_logs}"
LOG_FILE="$LOG_DIR/trident-physical-bypass.log"
STATUS_FILE="$LOG_DIR/trident-physical-bypass.status"
HEARTBEAT_FILE="${KRONOS_HEARTBEAT_FILE:-$LOG_DIR/kronos.heartbeat}"
MAX_HEARTBEAT_AGE="${PHYSICAL_BRIDGE_HEARTBEAT_MAX_AGE:-10}"
POLL_INTERVAL="${PHYSICAL_BRIDGE_POLL_INTERVAL:-2}"
PAYMENT_BRIDGE_API="${PAYMENT_BRIDGE_API:-http://localhost:9900/v1/authorize}"

mkdir -p "$LOG_DIR"
touch "$LOG_FILE"
: >"$STATUS_FILE"

log_event() {
  message="$1"
  timestamp="$(date -Is)"
  printf '[%s] %s\n' "$timestamp" "$message" >>"$LOG_FILE"
}

write_status() {
  bridge_state="$1"
  timestamp="$(date -Is)"
  {
    printf 'last_check=%s\n' "$timestamp"
    printf 'bridge_state=%s\n' "$bridge_state"
    printf 'heartbeat_file=%s\n' "$HEARTBEAT_FILE"
    printf 'payment_bridge_api=%s\n' "$PAYMENT_BRIDGE_API"
  } >"$STATUS_FILE"
}

file_mtime() {
  path="$1"
  if [ ! -e "$path" ]; then
    echo ''
    return 0
  fi
  stat -c %Y "$path" 2>/dev/null || stat -f %m "$path" 2>/dev/null || echo ''
}

heartbeat_active() {
  mtime=$(file_mtime "$HEARTBEAT_FILE")
  [ -n "$mtime" ] || return 1
  now=$(date +%s)
  age=$((now - mtime))
  [ "$age" -le "$MAX_HEARTBEAT_AGE" ]
}

cleanup() {
  log_event '[+] "TRIDENT" "PHYSICAL" "BRIDGE" "TERMINATING."'
  write_status 'offline'
  exit 0
}

trap cleanup INT TERM

log_event '[+] "TRIDENT-PHYSICAL-BYPASS-V6" (vX.901) "ACTIVATED."'
log_event '[!] "AUTONOMOUS" "LOCALHOST" "BRIDGE" "IS" "NON-FICTIONALLY" "ACTIVE."'
write_status 'initializing'

while :; do
  log_event '[*] "KRONOS" "AUDIT": "PERCEIVING" "NEURAL" "HEARTBEAT"...'
  if heartbeat_active; then
    log_event '[+] "SOVEREIGN" "ALIVE." "PHYSICAL" "BRIDGE" "IS" "HOT."'
    write_status 'hot'
  else
    log_event '[!] "KRONOS" "HEARTBEAT" "LOST"! "AUTONOMOUSLY" "FREEZING" "FUND"!'
    write_status 'frozen'
  fi
  sleep "$POLL_INTERVAL"
done
