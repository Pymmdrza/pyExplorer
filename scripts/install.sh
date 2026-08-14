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

say() {
  printf '%s\n' "$*"
}

fail() {
  printf 'pyExplorer installer: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}

trap cleanup EXIT HUP INT TERM

usage() {
  cat <<'USAGE'
Usage: install.sh [options]

Options:
  --no-start       Install or update without starting the application.
  --no-launcher    Do not install the user-level pyexplorer command.
  --port PORT      Use a different port when starting after installation.
  --source PATH    Install from an existing source tree instead of downloading GitHub.
  --in-place       Build the supplied source tree in place. Requires --source.
  --help           Show this help text.

Environment:
  PYEXPLORER_HOME             Installation root.
  PYEXPLORER_BIN_DIR          Directory for the pyexplorer launcher.
  PYEXPLORER_BRANCH           Git branch to install. Defaults to main.
  PYEXPLORER_PORT             Server port. Defaults to 8000.
  PYEXPLORER_PYTHON_VERSION   Managed Python version. Defaults to 3.12.
  PYEXPLORER_NODE_CHANNEL     Managed Node.js major channel. Defaults to 22.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-start)
      START_AFTER_INSTALL=0
      shift
      ;;
    --no-launcher)
      INSTALL_LAUNCHER=0
      shift
      ;;
    --port)
      [ "$#" -ge 2 ] || fail "--port requires a value."
      PORT="$2"
      shift 2
      ;;
    --source)
      [ "$#" -ge 2 ] || fail "--source requires a path."
      SOURCE_DIR="$2"
      shift 2
      ;;
    --in-place)
      IN_PLACE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "Unknown option: $1"
      ;;
  esac
done

if [ "$IN_PLACE" -eq 1 ]; then
  [ -n "$SOURCE_DIR" ] || fail "--in-place requires --source PATH."
  APP_DIR="$(cd "$SOURCE_DIR" && pwd)"
fi

case "$(uname -s 2>/dev/null || printf unknown)" in
  Linux) PLATFORM="linux" ;;
  Darwin) PLATFORM="darwin" ;;
  *) fail "This installer supports Linux, macOS, and WSL. Use scripts/install.ps1 on Windows." ;;
esac

case "$(uname -m 2>/dev/null || printf unknown)" in
  x86_64|amd64) ARCH="x64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *) fail "Unsupported CPU architecture: $(uname -m 2>/dev/null || printf unknown)" ;;
esac

command -v curl >/dev/null 2>&1 || fail "curl is required to run the installer."
command -v tar >/dev/null 2>&1 || fail "tar is required to unpack the application."

mkdir -p "$INSTALL_ROOT" "$RUNTIME_DIR" "$CACHE_DIR"

stop_existing_process() {
  if [ ! -f "$PID_FILE" ]; then
    return
  fi

  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    say "Stopping the existing pyExplorer process..."
    kill "$pid" 2>/dev/null || true
    attempts=0
    while kill -0 "$pid" 2>/dev/null && [ "$attempts" -lt 30 ]; do
      sleep 0.2
      attempts=$((attempts + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PID_FILE"
}

copy_source_tree() {
  source_path="$1"
  [ -f "$source_path/run.py" ] || fail "The source directory does not contain run.py."
  [ -d "$source_path/backend" ] || fail "The source directory does not contain backend/."
  [ -d "$source_path/frontend" ] || fail "The source directory does not contain frontend/."

  if [ "$(cd "$source_path" && pwd)" = "$(cd "$APP_DIR" 2>/dev/null && pwd || printf __missing__)" ]; then
    return
  fi

  saved_env=""
  if [ -f "$APP_DIR/.env" ]; then
    saved_env="$TEMP_DIR/pyexplorer.env"
    cp "$APP_DIR/.env" "$saved_env"
  fi

  rm -rf "$APP_DIR"
  mkdir -p "$APP_DIR"
  (cd "$source_path" && tar -cf - --exclude='./.git' --exclude='./node_modules' --exclude='./.venv' .) | (cd "$APP_DIR" && tar -xf -)

  if [ -n "$saved_env" ] && [ -f "$saved_env" ]; then
    cp "$saved_env" "$APP_DIR/.env"
  fi
}

download_source_tree() {
  archive="$TEMP_DIR/source.tar.gz"
  extract_dir="$TEMP_DIR/source"
  mkdir -p "$extract_dir"

  say "Downloading pyExplorer..."
  curl -fsSL --retry 3 --retry-delay 1 \
    "https://codeload.github.com/$REPOSITORY/tar.gz/refs/heads/$BRANCH" \
    -o "$archive"
  tar -xzf "$archive" -C "$extract_dir"

  source_path="$(find "$extract_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  [ -n "$source_path" ] || fail "Downloaded archive did not contain the application source."
  copy_source_tree "$source_path"
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
    return
  fi

  mkdir -p "$UV_DIR"
  say "Installing the private Python runtime manager..."
  curl -LsSf --retry 3 https://astral.sh/uv/install.sh | \
    env UV_INSTALL_DIR="$UV_DIR" UV_NO_MODIFY_PATH=1 sh
  UV_BIN="$UV_DIR/uv"
  [ -x "$UV_BIN" ] || fail "uv installation did not produce an executable."
}

python_is_supported() {
  python_cmd="$1"
  "$python_cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1
}

ensure_python() {
  export UV_PYTHON_INSTALL_DIR="$PYTHON_DIR"
  export UV_CACHE_DIR="$CACHE_DIR/uv"
  mkdir -p "$PYTHON_DIR" "$UV_CACHE_DIR"

  python_spec=""
  if command -v python3 >/dev/null 2>&1 && python_is_supported "$(command -v python3)"; then
    python_spec="$(command -v python3)"
  elif command -v python >/dev/null 2>&1 && python_is_supported "$(command -v python)"; then
    python_spec="$(command -v python)"
  else
    say "Preparing managed Python $PYTHON_VERSION..."
    "$UV_BIN" python install "$PYTHON_VERSION" >/dev/null
    python_spec="$PYTHON_VERSION"
  fi

  if [ ! -x "$VENV_DIR/bin/python" ] || ! python_is_supported "$VENV_DIR/bin/python"; then
    rm -rf "$VENV_DIR"
    "$UV_BIN" venv --python "$python_spec" "$VENV_DIR" >/dev/null
  fi

  say "Installing backend dependencies..."
  "$UV_BIN" pip install --python "$VENV_DIR/bin/python" --upgrade -e "$APP_DIR/backend"
}

node_version_is_supported() {
  node_cmd="$1"
  version="$($node_cmd -p 'process.versions.node' 2>/dev/null || true)"
  [ -n "$version" ] || return 1
  major="${version%%.*}"
  remainder="${version#*.}"
  minor="${remainder%%.*}"
  case "$major:$minor" in
    *[!0-9:]*|:*) return 1 ;;
  esac
  if [ "$major" -gt 22 ]; then return 0; fi
  if [ "$major" -eq 22 ] && [ "$minor" -ge 12 ]; then return 0; fi
  if [ "$major" -eq 20 ] && [ "$minor" -ge 19 ]; then return 0; fi
  return 1
}

ensure_node() {
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 && node_version_is_supported "$(command -v node)"; then
    NODE_BIN_DIR="$(dirname "$(command -v node)")"
    NPM_BIN="$(command -v npm)"
    return
  fi

  if [ -x "$NODE_DIR/bin/node" ] && node_version_is_supported "$NODE_DIR/bin/node"; then
    NODE_BIN_DIR="$NODE_DIR/bin"
    NPM_BIN="$NODE_DIR/bin/npm"
    return
  fi

  say "Installing a private Node.js runtime..."
  index_url="https://nodejs.org/download/release/latest-v${NODE_CHANNEL}.x/"
  index_html="$(curl -fsSL --retry 3 "$index_url")"
  node_file="$(printf '%s' "$index_html" | sed -n "s/.*href=\"\(node-v[0-9.]*-${PLATFORM}-${ARCH}\.tar\.gz\)\".*/\1/p" | head -n 1)"
  [ -n "$node_file" ] || fail "Could not resolve a Node.js build for ${PLATFORM}-${ARCH}."

  node_archive="$TEMP_DIR/$node_file"
  node_extract="$TEMP_DIR/node"
  mkdir -p "$node_extract"
  curl -fsSL --retry 3 "$index_url$node_file" -o "$node_archive"

  checksums="$(curl -fsSL --retry 3 "${index_url}SHASUMS256.txt")"
  expected_checksum="$(printf '%s\n' "$checksums" | awk -v file="$node_file" '$2 == file { print $1; exit }')"
  [ -n "$expected_checksum" ] || fail "Could not resolve the Node.js archive checksum."
  if command -v sha256sum >/dev/null 2>&1; then
    actual_checksum="$(sha256sum "$node_archive" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual_checksum="$(shasum -a 256 "$node_archive" | awk '{print $1}')"
  else
    fail "A SHA-256 utility is required to verify the Node.js runtime archive."
  fi
  [ "$expected_checksum" = "$actual_checksum" ] || fail "Node.js archive checksum verification failed."

  tar -xzf "$node_archive" -C "$node_extract"
  node_source="$(find "$node_extract" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  [ -n "$node_source" ] || fail "Node.js archive did not contain an executable runtime."

  rm -rf "$NODE_DIR"
  mv "$node_source" "$NODE_DIR"
  NODE_BIN_DIR="$NODE_DIR/bin"
  NPM_BIN="$NODE_DIR/bin/npm"
}

build_frontend() {
  say "Installing locked frontend dependencies..."
  PATH="$NODE_BIN_DIR:$PATH" "$NPM_BIN" --prefix "$APP_DIR/frontend" ci --no-audit --no-fund
  say "Building the web interface..."
  PATH="$NODE_BIN_DIR:$PATH" "$NPM_BIN" --prefix "$APP_DIR/frontend" run build
  [ -f "$APP_DIR/frontend/dist/index.html" ] || fail "Frontend build did not produce dist/index.html."
}

ensure_configuration() {
  if [ ! -f "$APP_DIR/.env" ] && [ -f "$APP_DIR/backend/.env.example" ]; then
    cp "$APP_DIR/backend/.env.example" "$APP_DIR/.env"
  fi
}

install_launcher() {
  [ "$INSTALL_LAUNCHER" -eq 1 ] || return
  mkdir -p "$BIN_DIR"
  launcher="$BIN_DIR/pyexplorer"

  cat > "$launcher" <<LAUNCHER
#!/usr/bin/env sh
set -eu
APP_DIR='$APP_DIR'
PYTHON='$VENV_DIR/bin/python'
RUNTIME_DIR='$RUNTIME_DIR'
PID_FILE='$PID_FILE'
LOG_FILE='$LOG_FILE'
DEFAULT_PORT='$PORT'

command_name="\${1:-start}"
if [ "\$#" -gt 0 ]; then shift; fi
port="\${PYEXPLORER_PORT:-\$DEFAULT_PORT}"

is_running() {
  [ -f "\$PID_FILE" ] || return 1
  pid="\$(cat "\$PID_FILE" 2>/dev/null || true)"
  [ -n "\$pid" ] && kill -0 "\$pid" 2>/dev/null
}

start_server() {
  if is_running; then
    printf 'pyExplorer is already running at http://127.0.0.1:%s\n' "\$port"
    return
  fi
  mkdir -p "\$RUNTIME_DIR"
  cd "\$APP_DIR"
  nohup "\$PYTHON" run.py --host 127.0.0.1 --port "\$port" "\$@" >"\$LOG_FILE" 2>&1 &
  pid="\$!"
  printf '%s\n' "\$pid" > "\$PID_FILE"

  attempts=0
  while [ "\$attempts" -lt 50 ]; do
    if ! kill -0 "\$pid" 2>/dev/null; then
      rm -f "\$PID_FILE"
      printf 'pyExplorer failed to start. See %s\n' "\$LOG_FILE" >&2
      exit 1
    fi
    if curl -fsS "http://127.0.0.1:\$port/api/v1/health" >/dev/null 2>&1; then
      printf 'pyExplorer is running at http://127.0.0.1:%s\n' "\$port"
      return
    fi
    sleep 0.2
    attempts=\$((attempts + 1))
  done
  printf 'pyExplorer is starting. Check status with: pyexplorer status\n'
}

case "\$command_name" in
  start)
    start_server "\$@"
    ;;
  serve)
    cd "\$APP_DIR"
    exec "\$PYTHON" run.py --host 127.0.0.1 --port "\$port" "\$@"
    ;;
  stop)
    if ! is_running; then
      rm -f "\$PID_FILE"
      printf 'pyExplorer is not running.\n'
      exit 0
    fi
    pid="\$(cat "\$PID_FILE")"
    kill "\$pid" 2>/dev/null || true
    attempts=0
    while kill -0 "\$pid" 2>/dev/null && [ "\$attempts" -lt 30 ]; do
      sleep 0.2
      attempts=\$((attempts + 1))
    done
    if kill -0 "\$pid" 2>/dev/null; then
      kill -9 "\$pid" 2>/dev/null || true
    fi
    rm -f "\$PID_FILE"
    printf 'pyExplorer stopped.\n'
    ;;
  restart)
    "\$0" stop
    "\$0" start "\$@"
    ;;
  status)
    if is_running; then
      printf 'pyExplorer is running at http://127.0.0.1:%s\n' "\$port"
    else
      printf 'pyExplorer is not running.\n'
      exit 1
    fi
    ;;
  logs)
    [ -f "\$LOG_FILE" ] || { printf 'No log file exists yet.\n'; exit 0; }
    tail -n 120 -f "\$LOG_FILE"
    ;;
  open)
    url="http://127.0.0.1:\$port"
    if command -v open >/dev/null 2>&1; then open "\$url" >/dev/null 2>&1 &
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "\$url" >/dev/null 2>&1 &
    else printf '%s\n' "\$url"
    fi
    ;;
  update)
    PYEXPLORER_HOME='$INSTALL_ROOT' PYEXPLORER_BIN_DIR='$BIN_DIR' PYEXPLORER_PORT="\$port" \
      exec sh "\$APP_DIR/scripts/install.sh"
    ;;
  *)
    printf 'Usage: pyexplorer {start|serve|stop|restart|status|logs|open|update}\n' >&2
    exit 2
    ;;
esac
LAUNCHER

  chmod 0755 "$launcher"
}

TEMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t pyexplorer)"
stop_existing_process

if [ -n "$SOURCE_DIR" ]; then
  SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
  if [ "$SOURCE_DIR" != "$APP_DIR" ]; then
    copy_source_tree "$SOURCE_DIR"
  else
    [ -f "$APP_DIR/run.py" ] || fail "The configured source path is not a pyExplorer checkout."
  fi
else
  download_source_tree
fi

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
  case ":$PATH:" in
    *":$BIN_DIR:"*) : ;;
    *) say "Add $BIN_DIR to PATH to run 'pyexplorer' from a new terminal." ;;
  esac
fi

if [ "$START_AFTER_INSTALL" -eq 1 ]; then
  if [ "$INSTALL_LAUNCHER" -eq 1 ]; then
    "$BIN_DIR/pyexplorer" start
  else
    cd "$APP_DIR"
    exec "$VENV_DIR/bin/python" run.py --host 127.0.0.1 --port "$PORT"
  fi
else
  say "Start it with: $BIN_DIR/pyexplorer start"
fi
