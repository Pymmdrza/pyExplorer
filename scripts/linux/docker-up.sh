#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "== Starting pyExplorer Docker demo =="

command -v docker >/dev/null 2>&1 || {
  echo "Docker is not installed or not available in PATH."
  exit 1
}

cd "$ROOT"
docker compose up --build