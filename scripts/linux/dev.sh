#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo "== Starting pyExplorer dev stack =="

cleanup() {
  echo ""
  echo "Stopping servers..."
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

cd "$BACKEND"
PYTHONPATH=src python3 -m uvicorn pyexplorer_api.asgi:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

cd "$FRONTEND"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://localhost:8000/api/v1/health"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers."

wait