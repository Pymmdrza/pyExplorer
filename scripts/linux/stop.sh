#!/usr/bin/env bash
set -euo pipefail

echo "== Stopping pyExplorer local dev ports =="

if command -v lsof >/dev/null 2>&1; then
  for port in 8000 5173; do
    pids="$(lsof -ti tcp:"$port" || true)"
    if [ -n "$pids" ]; then
      echo "Stopping processes on port $port: $pids"
      kill $pids 2>/dev/null || true
    fi
  done
elif command -v fuser >/dev/null 2>&1; then
  fuser -k 8000/tcp 2>/dev/null || true
  fuser -k 5173/tcp 2>/dev/null || true
else
  echo "Install lsof or psmisc/fuser, or stop the dev processes manually."
fi

echo "Done."