# pyExplorer

pyExplorer is a lightweight Bitcoin blockchain explorer built with FastAPI, Uvicorn, React, and TypeScript. The production application runs as a single Uvicorn process that serves both the API and the compiled web interface.

## Quick install

The installer is designed for a clean machine. Docker is not required, and an existing Python or Node.js installation is not required. When a compatible runtime is already present, it is reused. Otherwise, the installer creates private user-level runtimes without modifying the system Python installation.

### Linux and macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Pymmdrza/pyExplorer/main/scripts/install.sh | sh
```

The same installer can be used with `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/Pymmdrza/pyExplorer/main/scripts/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/Pymmdrza/pyExplorer/main/scripts/install.ps1 | iex
```

The installer downloads the current release branch, prepares isolated runtime dependencies, builds the web interface, creates the local configuration when needed, installs a launcher, and starts pyExplorer on `http://127.0.0.1:8000`.

Running the install command again updates the application in place while preserving the local `.env` configuration.

## Application control

After installation, the launcher supports:

```text
pyexplorer start
pyexplorer stop
pyexplorer restart
pyexplorer status
pyexplorer logs
pyexplorer open
pyexplorer update
pyexplorer serve
```

On Linux and macOS, the launcher is installed to `~/.local/bin/pyexplorer`. If that directory is not already on `PATH`, it can be called directly with its full path. On Windows, the installer adds its launcher directory to the user `PATH`; a newly opened terminal can use `pyexplorer` directly.

To install without automatically starting the server:

```bash
curl -fsSL https://raw.githubusercontent.com/Pymmdrza/pyExplorer/main/scripts/install.sh | sh -s -- --no-start
```

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Pymmdrza/pyExplorer/main/scripts/install.ps1))) -NoStart
```

## Install from a downloaded source tree

A cloned repository or extracted source archive can bootstrap itself with the same managed runtime approach.

### Linux and macOS

```bash
./scripts/linux/setup.sh
./scripts/linux/run.sh
```

### Windows

Double-click `scripts\windows\setup.cmd`, or run:

```powershell
.\scripts\windows\setup.ps1
.\scripts\windows\run.ps1
```

The setup scripts build the current checkout in place and place their managed runtime under `.pyexplorer-runtime`.

## Features

- Transaction lookup with normalized inputs, outputs, fees, confirmations, and export support
- Address balances, transfer history, and pagination
- Block metadata and paginated transaction records
- Network overview with market, chain, mining, and mempool metrics
- Realtime unconfirmed transaction feed over Server-Sent Events
- Bounded retries and resilient network error handling
- Bounded in-process TTL cache with concurrent request coalescing
- Responsive light and dark interfaces with keyboard and reduced-motion support
- Single-process production runtime with Uvicorn
- Optional Docker deployment using the same application runtime

## Architecture

```text
Browser
  |
  v
Uvicorn / FastAPI
  |-- React production build
  |-- Versioned REST API
  |-- Realtime SSE stream
  |-- Network statistics endpoints
  |-- Bitcoin network data endpoints
  `-- Blockchain websocket for realtime mempool events
```

The default runtime uses asynchronous I/O end to end and one application process. Process-local caching and realtime services keep the deployment compact without requiring a reverse proxy or external cache.

## Installer behavior

The remote installers are intentionally user-scoped and idempotent.

Linux and macOS use `${XDG_DATA_HOME:-~/.local/share}/pyexplorer` by default. Windows uses `%LOCALAPPDATA%\pyExplorer`. The following environment variables can override installer behavior:

| Variable | Purpose |
| --- | --- |
| `PYEXPLORER_HOME` | Installation root |
| `PYEXPLORER_BIN_DIR` | Launcher directory |
| `PYEXPLORER_BRANCH` | Git branch to install; defaults to `main` |
| `PYEXPLORER_PORT` | Default server port; defaults to `8000` |
| `PYEXPLORER_PYTHON_VERSION` | Managed Python version; defaults to `3.12` |
| `PYEXPLORER_NODE_CHANNEL` | Managed Node.js major channel; defaults to `22` |

The installer uses the official `uv` standalone bootstrap when a compatible local Python toolchain is not sufficient, and downloads a private Node.js runtime only when a compatible Node.js installation is unavailable. Downloaded Node.js archives are verified against the official SHA-256 manifest before extraction.

## Manual installation

For environments where runtime management is handled externally, install the backend and build the frontend manually:

```bash
python -m pip install -e ./backend
cd frontend
npm ci
npm run build
cd ..
python run.py
```

The default server binds to `127.0.0.1:8000`. To expose it on the local network:

```bash
python run.py --host 0.0.0.0 --port 8000
```

## Development

Development mode keeps the backend and Vite server separate for hot module replacement.

### Linux and macOS

```bash
./scripts/linux/dev.sh
```

### Windows

```powershell
.\scripts\windows\dev.ps1
```

Development endpoints:

- Web interface: `http://localhost:5173`
- API: `http://localhost:8000/api/v1`
- OpenAPI documentation: `http://localhost:8000/docs`

## Docker

Docker remains optional:

```bash
docker compose up --build
```

The container exposes the application on `http://localhost:8000`.

## Configuration

Backend configuration uses environment variables prefixed with `PYEXPLORER_`. Defaults are suitable for local use. See `backend/.env.example` for the complete configuration surface.

The frontend defaults to the relative API path `/api/v1`, allowing the production interface and API to use the same origin.

## API

The versioned API is available under `/api/v1`.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Process health |
| `GET /ready` | Runtime readiness summary |
| `GET /search?q=` | Resolve a transaction, address, or block identifier |
| `GET /network/overview` | Network and market overview |
| `GET /network/mempool/recent` | Recent unconfirmed transactions |
| `GET /transactions/{tx_hash}` | Transaction details |
| `GET /addresses/{address}` | Address details and activity |
| `GET /blocks/{height}` | Block details and transactions |
| `GET /stream/transactions` | Realtime transaction SSE stream |
| `GET /exports/...` | JSON and CSV exports |

Interactive API documentation is available at `/docs`.

## Quality checks

Backend:

```bash
cd backend
python -m ruff check src tests
python -m pytest --cov=pyexplorer_api --cov-report=term-missing
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Project structure

```text
backend/          FastAPI application, services, schemas, and tests
frontend/         React and TypeScript source
scripts/          Installation, setup, run, development, and verification helpers
run.py            Cross-platform Uvicorn launcher
Dockerfile        Optional container build
.github/workflows Continuous integration
```

## License

This project is distributed under the terms in [LICENSE](LICENSE).
