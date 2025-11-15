#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$REPO_ROOT/creation_codex_demo.log"

run_with_sudo_if_needed() {
  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    "$@"
  fi
}

ensure_node() {
  if command -v node >/dev/null 2>&1; then
    return
  fi

  if command -v pkg >/dev/null 2>&1; then
    echo "Node.js is missing. Attempting to install via 'pkg install nodejs'." >&2
    pkg install -y nodejs
    return
  fi

  if command -v apt-get >/dev/null 2>&1; then
    echo "Node.js is missing. Attempting to install via 'apt-get install nodejs'." >&2
    run_with_sudo_if_needed apt-get update
    run_with_sudo_if_needed apt-get install -y nodejs
    return
  fi

  cat <<'MSG' >&2
Node.js is required to run the Creation Codex simulation but was not found.
Please install Node.js 18+ using your package manager (for example: pkg install nodejs, apt install nodejs, brew install node).
MSG
  exit 1
}

ensure_node

cd "$REPO_ROOT"

nohup node run_creation_codex_simulation.mjs "$@" >"$LOG_FILE" 2>&1 &
PID=$!

echo "Creation Codex simulation started in the background (PID: $PID)."
echo "Logs are written to $LOG_FILE"
echo "Use 'tail -f $LOG_FILE' to stream the output."
