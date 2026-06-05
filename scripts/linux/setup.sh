#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
ENV_FILE="$ROOT/.env"

echo "== pyExplorer Linux setup =="

command -v python3 >/dev/null 2>&1 || {
  echo "Python 3 is not installed or not available in PATH."
  exit 1
}

command -v npm >/dev/null 2>&1 || {
  echo "Node.js/npm is not installed or not available in PATH."
  exit 1
}

if [ ! -f "$ENV_FILE" ]; then
  echo "Creating root .env with local defaults..."
  cat > "$ENV_FILE" <<'EOF'
PYEXPLORER_ENVIRONMENT=local
PYEXPLORER_LOG_LEVEL=INFO
PYEXPLORER_API_PREFIX=/api/v1
PYEXPLORER_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PYEXPLORER_REALTIME_ENABLED=true
PYEXPLORER_BLOCKCHAIN_WS_URL=wss://ws.blockchain.info/inv
EOF
fi

echo "Installing backend dependencies..."
cd "$BACKEND"
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"

echo "Installing frontend dependencies..."
cd "$FRONTEND"
npm install

echo ""
echo "Setup complete."
echo "Run: ./scripts/linux/dev.sh"