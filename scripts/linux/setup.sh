#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
ENV_FILE="$ROOT/.env"

echo "== pyExplorer setup =="

command -v python3 >/dev/null 2>&1 || {
  echo "Python 3.11 or newer is required."
  exit 1
}

command -v npm >/dev/null 2>&1 || {
  echo "Node.js and npm are required to build the web interface."
  exit 1
}

if [ ! -f "$ENV_FILE" ]; then
  cp "$BACKEND/.env.example" "$ENV_FILE"
fi

echo "Installing backend dependencies..."
python3 -m pip install -e "$BACKEND"

echo "Installing frontend dependencies..."
cd "$FRONTEND"
npm ci

echo "Building frontend..."
npm run build

echo ""
echo "Setup complete."
echo "Start pyExplorer with: python3 run.py"
