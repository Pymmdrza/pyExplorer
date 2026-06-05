#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo "== Running backend checks =="
cd "$BACKEND"
python3 -m ruff check .
python3 -m pytest
python3 -m compileall src tests

echo "== Running frontend checks =="
cd "$FRONTEND"
npm run lint
npm run build

echo ""
echo "All checks passed."