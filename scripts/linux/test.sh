#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="$ROOT/.pyexplorer-runtime"
PYTHON="$RUNTIME/runtime/venv/bin/python"
LOCAL_UV="$RUNTIME/runtime/uv/uv"
MANAGED_NODE="$RUNTIME/runtime/node/bin"

if [[ ! -x "$PYTHON" || ! -d "$ROOT/frontend/node_modules" ]]; then
  "$ROOT/scripts/linux/setup.sh"
fi

if [[ -x "$LOCAL_UV" ]]; then
  UV="$LOCAL_UV"
else
  UV="$(command -v uv || true)"
fi
[[ -n "$UV" ]] || { echo "uv is unavailable. Run ./scripts/linux/setup.sh." >&2; exit 1; }

if [[ -x "$MANAGED_NODE/npm" ]]; then
  export PATH="$MANAGED_NODE:$PATH"
  NPM="$MANAGED_NODE/npm"
else
  NPM="$(command -v npm || true)"
fi
[[ -n "$NPM" ]] || { echo "npm runtime is unavailable. Run ./scripts/linux/setup.sh." >&2; exit 1; }

"$UV" pip install --python "$PYTHON" --upgrade -e "$ROOT/backend[dev]"
"$PYTHON" -m ruff check "$ROOT/backend/src" "$ROOT/backend/tests"
"$PYTHON" -m pytest "$ROOT/backend"
"$PYTHON" -m compileall "$ROOT/backend/src" "$ROOT/backend/tests"

cd "$ROOT/frontend"
"$NPM" install --prefer-offline --fetch-retries=3
"$NPM" run lint
"$NPM" run build

printf 'All checks passed.\n'
