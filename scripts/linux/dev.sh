#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="$ROOT/.pyexplorer-runtime"
PYTHON="$RUNTIME/runtime/venv/bin/python"
MANAGED_NODE="$RUNTIME/runtime/node/bin"

if [[ ! -x "$PYTHON" || ! -d "$ROOT/frontend/node_modules" ]]; then
  "$ROOT/scripts/linux/setup.sh"
fi

if [[ -x "$MANAGED_NODE/npm" ]]; then
  export PATH="$MANAGED_NODE:$PATH"
  NPM="$MANAGED_NODE/npm"
else
  NPM="$(command -v npm || true)"
fi
[[ -n "$NPM" ]] || { echo "npm runtime is unavailable. Run ./scripts/linux/setup.sh." >&2; exit 1; }

cleanup() {
  [[ -z "${BACKEND_PID:-}" ]] || kill "$BACKEND_PID" 2>/dev/null || true
  [[ -z "${FRONTEND_PID:-}" ]] || kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$ROOT/backend"
"$PYTHON" -m uvicorn pyexplorer_api.asgi:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd "$ROOT/frontend"
"$NPM" install --prefer-offline --fetch-retries=3
"$NPM" run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

printf 'Backend:  http://localhost:8000/api/v1/health\n'
printf 'Frontend: http://localhost:5173\n'
printf 'Press Ctrl+C to stop both servers.\n'
wait
