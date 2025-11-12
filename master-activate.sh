#!/bin/sh
set -eu

TERMUX_PREFIX="/data/data/com.termux/files/usr/bin"
case ":$PATH:" in
  *:"$TERMUX_PREFIX":*) ;;
  *)
    export PATH="$TERMUX_PREFIX:$PATH"
    ;;
esac

printf '[+] Master Codex: executing. PATH is configured.\n'

LOG_DIR="$HOME/sei_logs"
mkdir -p "$LOG_DIR"
printf '[+] Master Codex: secure log directory verified at %s.\n' "$LOG_DIR"

launch_script() {
  script="$1"
  label="$2"
  if [ -x "$script" ]; then
    printf '[!] Activating %s...\n' "$label"
    nohup "$script" >>"$LOG_DIR/${script}.log" 2>&1 &
  elif [ -f "$script" ]; then
    printf '[~] %s found but not executable; skipping.\n' "$script"
  else
    printf '[~] %s not found; skipping.\n' "$script"
  fi
}

launch_script "./kronos-mandate-v4.sh" "Sovereign Mandate (kronos-mandate-v4.sh)"
launch_script "./autonomous-shield-v5.sh" "Defensive Shield (autonomous-shield-v5.sh)"
launch_script "./argus-c2-shield.sh" "Kinetic Shield (argus-c2-shield.sh)"
launch_script "./ccr5-audit-v5.1.sh" "Audit Protocol (ccr5-audit-v5.1.sh)"

printf '[+] Master Codex: activation complete.\n'
