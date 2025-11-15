#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v node >/dev/null 2>&1; then
  cat <<'MSG' >&2
Node.js is required to run the Creation Codex simulation.
Install it with your package manager (for example: `pkg install nodejs`, `apt install nodejs`, or via https://nodejs.org/).
MSG
  exit 1
fi

cd "$REPO_ROOT"

node run_creation_codex_simulation.mjs "$@"
