#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="$ROOT/.pyexplorer-runtime/runtime/venv/bin/python"
if [[ ! -x "$PYTHON" || ! -f "$ROOT/frontend/dist/index.html" ]]; then
  "$ROOT/scripts/linux/setup.sh"
fi
cd "$ROOT"
exec "$PYTHON" run.py "$@"
