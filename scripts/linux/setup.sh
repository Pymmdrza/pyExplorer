#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="$ROOT/.pyexplorer-runtime"
PYEXPLORER_SOURCE_DIR="$ROOT" \
PYEXPLORER_HOME="$RUNTIME" \
PYEXPLORER_BIN_DIR="$RUNTIME/bin" \
"$ROOT/scripts/install.sh" --source "$ROOT" --in-place --no-start --no-launcher

echo "Setup complete."
echo "Start pyExplorer with: ./scripts/linux/run.sh"
