#!/bin/sh
set -eu

TERMUX_PREFIX="/data/data/com.termux/files/usr/bin"
case ":$PATH:" in
  *:"$TERMUX_PREFIX":*) ;;
  *)
    export PATH="$TERMUX_PREFIX:$PATH"
    ;;
esac

LOGDIR="${HOME}/trident_logs"
LOGFILE="${LOGDIR}/trident-shield.log"
PIDFILE="${LOGDIR}/trident-shield.pid"
SLEEP_MS="${SLEEP_MS:-1000}"
MAX_LOG_BYTES="${MAX_LOG_BYTES:-1048576}"

mkdir -p "$LOGDIR"
touch "$LOGFILE"

echo "$$" > "$PIDFILE"

cleanup() {
  printf '[+] TRIDENT SHUTDOWN requested at %s\n' "$(date -Is)" >>"$LOGFILE"
  rm -f "$PIDFILE"
  exit 0
}

trap cleanup INT TERM

sleep_interval() {
  awk -v ms="$SLEEP_MS" 'BEGIN { if (ms <= 0) ms = 1000; printf "%.3f", ms/1000 }'
}

get_filesize() {
  size=$( { stat -c %s "$LOGFILE" 2>/dev/null || stat -f %z "$LOGFILE" 2>/dev/null || wc -c <"$LOGFILE"; } 2>/dev/null ) || size=0
  printf '%s' "$size" | tr -d '[:space:]'
}

rotate_log_if_needed() {
  size=$(get_filesize)
  [ "${size:-0}" -ge "$MAX_LOG_BYTES" ] || return 0
  stamp=$(date +%Y%m%d-%H%M%S)
  mv "$LOGFILE" "${LOGFILE}.${stamp}"
  printf '[+] Log rotated at %s\n' "$(date -Is)" >"$LOGFILE"
}

log_line() {
  message="$1"
  stamp="$(date -Is)"
  formatted="[$stamp] $message"
  printf '%s\n' "$formatted" | tee -a "$LOGFILE" >/dev/null
}

log_line '[+] TRIDENT-SHIELD-V3 CODEX ACTIVATED (vX.501).'

MESSAGE='[+] TRIDENT FUND: QGE AUDIT NOMINAL.'
SLEEP_SEC=$(sleep_interval)

while :; do
  rotate_log_if_needed
  log_line "$MESSAGE"
  sleep "$SLEEP_SEC"
done
