#!/usr/bin/env sh
set -eu

REPOSITORY="Pymmdrza/pyExplorer"
BRANCH="${PYEXPLORER_BRANCH:-main}"
PYTHON_VERSION="${PYEXPLORER_PYTHON_VERSION:-3.12}"
NODE_CHANNEL="${PYEXPLORER_NODE_CHANNEL:-22}"
INSTALL_ROOT="${PYEXPLORER_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/pyexplorer}"
BIN_DIR="${PYEXPLORER_BIN_DIR:-$HOME/.local/bin}"
APP_DIR="$INSTALL_ROOT/app"
RUNTIME_DIR="$INSTALL_ROOT/runtime"
UV_DIR="$RUNTIME_DIR/uv"
PYTHON_DIR="$RUNTIME_DIR/python"
VENV_DIR="$RUNTIME_DIR/venv"
NODE_DIR="$RUNTIME_DIR/node"
CACHE_DIR="$RUNTIME_DIR/cache"
PID_FILE="$RUNTIME_DIR/pyexplorer.pid"
LOG_FILE="$RUNTIME_DIR/pyexplorer.log"
PORT="${PYEXPLORER_PORT:-8000}"
SOURCE_DIR="${PYEXPLORER_SOURCE_DIR:-}"
START_AFTER_INSTALL=1
INSTALL_LAUNCHER=1
IN_PLACE=0
TEMP_DIR=""

say() { printf '%s\n' "$*"; }
fail() { printf 'pyExplorer installer: %s\n' "$*" >&2; exit 1; }

cleanup() {
  [ -z "$TEMP_DIR" ] || [ ! -d "$TEMP_DIR" ] || rm -rf "$TEMP_DIR"
}
trap cleanup EXIT HUP INT TERM

usage() {
  cat <<'USAGE'
Usage: install.sh [options]

Options:
  --no-start       Install or update without starting pyExplorer.
  --no-launcher    Do not install the user-level pyexplorer command.
  --port PORT      Start on a different port. Default: 8000.
  --source PATH    Use an existing source tree.
  --in-place       Build the source tree in place. Requires --source.
  --help           Show this help text.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-start) START_AFTER_INSTALL=0; shift ;;
    --no-launcher) INSTALL_LAUNCHER=0; shift ;;
    --port) [ "$#" -ge 2 ] || fail "--port requires a value."; PORT="$2"; shift 2 ;;
    --source) [ "$#" -ge 2 ] || fail "--source requires a path."; SOURCE_DIR="$2"; shift 2 ;;
    --in-place) IN_PLACE=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
done

case "$(uname -s 2>/dev/null || printf unknown)" in
  Linux) PLATFORM="linux" ;;
  Darwin) PLATFORM="darwin" ;;
  *) fail "Use scripts/install.ps1 on Windows." ;;
esac

case "$(uname -m 2>/dev/null || printf unknown)" in
  x86_64|amd64) ARCH="x64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *) fail "Unsupported CPU architecture: $(uname -m 2>/dev/null || printf unknown)" ;;
esac

command -v curl >/dev/null 2>&1 || fail "curl is required."
command -v tar >/dev/null 2>&1 || fail "tar is required."

if [ "$IN_PLACE" -eq 1 ]; then
  [ -n "$SOURCE_DIR" ] || fail "--in-place requires --source PATH."
  APP_DIR="$(cd "$SOURCE_DIR" && pwd)"
fi

mkdir -p "$INSTALL_ROOT" "$RUNTIME_DIR" "$CACHE_DIR"
TEMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t pyexplorer)"

stop_existing_process() {
  [ -f "$PID_FILE" ] || return 0
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    say "Stopping the existing pyExplorer process..."
    kill "$pid" 2>/dev/null || true
    attempts=0
    while kill -0 "$pid" 2>/dev/null && [ "$attempts" -lt 30 ]; do
      sleep 0.2
      attempts=$((attempts + 1))
    done
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
}

install_source() {
  if [ -n "$SOURCE_DIR" ]; then
    source_path="$(cd "$SOURCE_DIR" && pwd)"
    [ -f "$source_path/run.py" ] || fail "The source directory is not a pyExplorer checkout."
    if [ "$source_path" = "$APP_DIR" ]; then
      return 0
    fi
  else
    archive="$TEMP_DIR/source.tar.gz"
    extract_dir="$TEMP_DIR/source"
    mkdir -p "$extract_dir"
    say "Downloading pyExplorer..."
    curl -fsSL --retry 3 --retry-delay 1 \
      "https://codeload.github.com/$REPOSITORY/tar.gz/refs/heads/$BRANCH" \
      -o "$archive" || fail "Could not download pyExplorer."
    tar -xzf "$archive" -C "$extract_dir"
    source_path="$(find "$extract_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    [ -n "$source_path" ] || fail "The downloaded archive is invalid."
  fi

  saved_env=""
  if [ -f "$APP_DIR/.env" ]; then
    saved_env="$TEMP_DIR/pyexplorer.env"
    cp "$APP_DIR/.env" "$saved_env"
  fi

  rm -rf "$APP_DIR"
  mkdir -p "$APP_DIR"
  (cd "$source_path" && tar -cf - --exclude='./.git' --exclude='./node_modules' --exclude='./.pyexplorer-runtime' .) | (cd "$APP_DIR" && tar -xf -)

  if [ -n "$saved_env" ] && [ -f "$saved_env" ]; then
    cp "$saved_env" "$APP_DIR/.env"
  fi
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
    return
  fi

  mkdir -p "$UV_DIR"
  say "Preparing the Python runtime manager..."
  curl -LsSf --retry 3 https://astral.sh/uv/install.sh | \
    env UV_INSTALL_DIR="$UV_DIR" UV_NO_MODIFY_PATH=1 sh
  UV_BIN="$UV_DIR/uv"
  [ -x "$UV_BIN" ] || fail "Could not install the Python runtime manager."
}

python_supported() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1
}

ensure_python() {
  export UV_PYTHON_INSTALL_DIR="$PYTHON_DIR"
  export UV_CACHE_DIR="$CACHE_DIR/uv"
  mkdir -p "$PYTHON_DIR" "$UV_CACHE_DIR"

  python_spec=""
  if command -v python3 >/dev/null 2>&1 && python_supported "$(command -v python3)"; then
    python_spec="$(command -v python3)"
  elif command -v python >/dev/null 2>&1 && python_supported "$(command -v python)"; then
    python_spec="$(command -v python)"
  else
    say "Preparing managed Python $PYTHON_VERSION..."
    "$UV_BIN" python install "$PYTHON_VERSION" >/dev/null || fail "Could not install Python $PYTHON_VERSION."
    python_spec="$PYTHON_VERSION"
  fi

  if [ ! -x "$VENV_DIR/bin/python" ] || ! python_supported "$VENV_DIR/bin/python"; then
    rm -rf "$VENV_DIR"
    "$UV_BIN" venv --python "$python_spec" "$VENV_DIR" >/dev/null || fail "Could not create the Python environment."
  fi

  say "Installing backend dependencies..."
  "$UV_BIN" pip install --python "$VENV_DIR/bin/python" --upgrade -e "$APP_DIR/backend" || \
    fail "Backend dependency installation failed."
}

node_supported() {
  "$1" -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit(((a===20&&b>=19)||(a===22&&b>=12)||a>22)?0:1)' >/dev/null 2>&1
}

ensure_node() {
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 && node_supported "$(command -v node)"; then
    NODE_BIN_DIR="$(dirname "$(command -v node)")"
    NPM_BIN="$(command -v npm)"
    return
  fi

  if [ -x "$NODE_DIR/bin/node" ] && node_supported "$NODE_DIR/bin/node"; then
    NODE_BIN_DIR="$NODE_DIR/bin"
    NPM_BIN="$NODE_DIR/bin/npm"
    return
  fi

  say "Installing a private Node.js runtime..."
  index_url="https://nodejs.org/dist/latest-v${NODE_CHANNEL}.x/"
  checksums="$(curl -fsSL --retry 3 --retry-delay 1 "${index_url}SHASUMS256.txt")" || \
    fail "Could not download the Node.js release manifest."

  node_file="$(printf '%s\n' "$checksums" | awk -v platform="$PLATFORM" -v arch="$ARCH" '
    $2 ~ ("^node-v[0-9.]+-" platform "-" arch "\\.tar\\.gz$") { print $2; exit }
  ')"
  [ -n "$node_file" ] || fail "Could not resolve a Node.js build for ${PLATFORM}-${ARCH}."
  expected="$(printf '%s\n' "$checksums" | awk -v file="$node_file" '$2 == file { print $1; exit }')"
  [ -n "$expected" ] || fail "Could not resolve the Node.js checksum."

  archive="$TEMP_DIR/$node_file"
  extract_dir="$TEMP_DIR/node"
  mkdir -p "$extract_dir"
  curl -fsSL --retry 3 --retry-delay 1 "$index_url$node_file" -o "$archive" || \
    fail "Could not download the Node.js runtime."

  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$archive" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$archive" | awk '{print $1}')"
  else
    fail "A SHA-256 utility is required."
  fi
  [ "$expected" = "$actual" ] || fail "Node.js checksum verification failed."

  tar -xzf "$archive" -C "$extract_dir"
  node_source="$(find "$extract_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  [ -n "$node_source" ] || fail "The Node.js archive is invalid."
  rm -rf "$NODE_DIR"
  mv "$node_source" "$NODE_DIR"
  NODE_BIN_DIR="$NODE_DIR/bin"
  NPM_BIN="$NODE_DIR/bin/npm"
}

install_frontend_dependencies() {
  export NPM_CONFIG_AUDIT=false
  export NPM_CONFIG_FUND=false
  export NPM_CONFIG_UPDATE_NOTIFIER=false
  say "Installing frontend dependencies..."

  if PATH="$NODE_BIN_DIR:$PATH" "$NPM_BIN" --prefix "$APP_DIR/frontend" install \
      --no-audit --no-fund --package-lock=false --progress=false --prefer-online --fetch-retries=3; then
    return 0
  fi

  say "Retrying frontend dependency installation..."
  PATH="$NODE_BIN_DIR:$PATH" "$NPM_BIN" cache verify >/dev/null 2>&1 || true
  PATH="$NODE_BIN_DIR:$PATH" "$NPM_BIN" --prefix "$APP_DIR/frontend" install \
    --no-audit --no-fund --package-lock=false --progress=false --prefer-online --fetch-retries=3 || \
    fail "Frontend dependency installation failed."
}

build_frontend() {
  install_frontend_dependencies
  say "Building the web interface..."
  PATH="$NODE_BIN_DIR:$PATH" "$NPM_BIN" --prefix "$APP_DIR/frontend" run build || \
    fail "Frontend build failed."
  [ -f "$APP_DIR/frontend/dist/index.html" ] || fail "Frontend build did not produce dist/index.html."
}

ensure_configuration() {
  if [ ! -f "$APP_DIR/.env" ] && [ -f "$APP_DIR/backend/.env.example" ]; then
    cp "$APP_DIR/backend/.env.example" "$APP_DIR/.env"
  fi
}

install_launcher() {
  [ "$INSTALL_LAUNCHER" -eq 1 ] || return 0
  mkdir -p "$BIN_DIR"
  launcher="$BIN_DIR/pyexplorer"

  cat > "$launcher" <<LAUNCHER
#!/usr/bin/env sh
set -eu
APP_DIR='$APP_DIR'
PYTHON='$VENV_DIR/bin/python'
PID_FILE='$PID_FILE'
LOG_FILE='$LOG_FILE'
DEFAULT_PORT='$PORT'
RAW_INSTALLER='https://raw.githubusercontent.com/$REPOSITORY/main/scripts/install.sh'
command_name="\${1:-start}"
[ "\$#" -eq 0 ] || shift
port="\${PYEXPLORER_PORT:-\$DEFAULT_PORT}"

is_running() {
  [ -f "\$PID_FILE" ] || return 1
  pid="\$(cat "\$PID_FILE" 2>/dev/null || true)"
  [ -n "\$pid" ] && kill -0 "\$pid" 2>/dev/null
}

case "\$command_name" in
  start)
    if is_running; then
      printf 'pyExplorer is already running at http://127.0.0.1:%s\n' "\$port"
      exit 0
    fi
    cd "\$APP_DIR"
    nohup "\$PYTHON" run.py --host 127.0.0.1 --port "\$port" "\$@" >"\$LOG_FILE" 2>&1 &
    pid="\$!"
    printf '%s\n' "\$pid" >"\$PID_FILE"
    attempts=0
    while [ "\$attempts" -lt 50 ]; do
      if ! kill -0 "\$pid" 2>/dev/null; then
        rm -f "\$PID_FILE"
        printf 'pyExplorer failed to start. See %s\n' "\$LOG_FILE" >&2
        exit 1
      fi
      if curl -fsS "http://127.0.0.1:\$port/api/v1/health" >/dev/null 2>&1; then
        printf 'pyExplorer is running at http://127.0.0.1:%s\n' "\$port"
        exit 0
      fi
      sleep 0.2
      attempts=\$((attempts + 1))
    done
    printf 'pyExplorer is starting. Check status with: pyexplorer status\n'
    ;;
  serve)
    cd "\$APP_DIR"
    exec "\$PYTHON" run.py --host 127.0.0.1 --port "\$port" "\$@"
    ;;
  stop)
    if ! is_running; then rm -f "\$PID_FILE"; printf 'pyExplorer is not running.\n'; exit 0; fi
    pid="\$(cat "\$PID_FILE")"
    kill "\$pid" 2>/dev/null || true
    attempts=0
    while kill -0 "\$pid" 2>/dev/null && [ "\$attempts" -lt 30 ]; do sleep 0.2; attempts=\$((attempts + 1)); done
    kill -0 "\$pid" 2>/dev/null && kill -9 "\$pid" 2>/dev/null || true
    rm -f "\$PID_FILE"
    printf 'pyExplorer stopped.\n'
    ;;
  restart) "\$0" stop; "\$0" start "\$@" ;;
  status)
    if is_running; then printf 'pyExplorer is running at http://127.0.0.1:%s\n' "\$port"; else printf 'pyExplorer is not running.\n'; exit 1; fi
    ;;
  logs) [ -f "\$LOG_FILE" ] && tail -n 120 -f "\$LOG_FILE" || printf 'No log file exists yet.\n' ;;
  open)
    url="http://127.0.0.1:\$port"
    if command -v open >/dev/null 2>&1; then open "\$url" >/dev/null 2>&1 &
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "\$url" >/dev/null 2>&1 &
    else printf '%s\n' "\$url"; fi
    ;;
  update) curl -fsSL "\$RAW_INSTALLER" | sh ;;
  *) printf 'Usage: pyexplorer {start|serve|stop|restart|status|logs|open|update}\n' >&2; exit 2 ;;
esac
LAUNCHER
  chmod 0755 "$launcher"
}

stop_existing_process
install_source
ensure_configuration
ensure_uv
ensure_python
ensure_node
build_frontend
install_launcher

say ""
say "pyExplorer installation completed successfully."
say "Application: $APP_DIR"
if [ "$INSTALL_LAUNCHER" -eq 1 ]; then
  say "Launcher:    $BIN_DIR/pyexplorer"
fi

if [ "$START_AFTER_INSTALL" -eq 1 ]; then
  if [ "$INSTALL_LAUNCHER" -eq 1 ]; then
    "$BIN_DIR/pyexplorer" start
  else
    cd "$APP_DIR"
    exec "$VENV_DIR/bin/python" run.py --host 127.0.0.1 --port "$PORT"
  fi
fi
