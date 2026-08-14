# pyExplorer

pyExplorer is a lightweight Bitcoin blockchain explorer built with FastAPI, Uvicorn, React, and TypeScript. A single Uvicorn process serves both the versioned API and the compiled web interface, keeping installation and runtime requirements small without requiring a reverse proxy.

## Features

- Transaction lookup with normalized inputs, outputs, fees, confirmations, and export support
- Address balances, transfer history, and pagination
- Block metadata and paginated transaction records
- Network overview with market, chain, mining, and mempool metrics
- Realtime unconfirmed transaction feed over Server-Sent Events
- Multi-provider fallback with bounded retries and temporary circuit breaking
- Bounded in-process TTL cache with concurrent request coalescing
- Responsive light and dark interfaces with keyboard and reduced-motion support
- Single-process production runtime with Uvicorn
- Optional Docker deployment with the same runtime architecture

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
  |-- Bitcoin data providers with fallback
  `-- Blockchain websocket for realtime mempool events
```

The default runtime uses asynchronous I/O end to end and one application process. The process-local cache and realtime service remain deterministic and resource-efficient without external infrastructure.

## Requirements

- Python 3.11 or newer
- Node.js 20.19+, 22.12+, or a newer supported release
- npm

Node.js is required to build the web interface. It is not required while the compiled application is running.

## Quick start

### Linux and macOS

```bash
./scripts/linux/setup.sh
python3 run.py
```

### Windows

```powershell
.\scripts\windows\setup.ps1
python run.py
```

Open `http://localhost:8000`.

The setup command installs the Python package, installs the locked frontend dependencies, and creates the production frontend build. Subsequent starts only require Python and the installed backend dependencies.

## Manual installation

Install the backend:

```bash
python -m pip install -e ./backend
```

Build the frontend:

```bash
cd frontend
npm ci
npm run build
cd ..
```

Start the application:

```bash
python run.py
```

The default server binds to `127.0.0.1:8000`. To make it available on the local network:

```bash
python run.py --host 0.0.0.0 --port 8000
```

## Development

Development mode keeps the backend and Vite server separate to provide hot module replacement.

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

Vite proxies `/api` requests to the local Uvicorn process.

## Docker

Docker is optional. The container uses a Node.js build stage for the frontend and runs the completed application with Uvicorn only.

```bash
docker compose up --build
```

Open `http://localhost:8000`.

Stop the container with:

```bash
docker compose down
```

## Configuration

Backend configuration uses environment variables prefixed with `PYEXPLORER_`. The defaults are suitable for local use. See `backend/.env.example` for the complete configuration surface.

Frontend builds accept:

```text
VITE_API_BASE_URL=/api/v1
```

The default relative API URL is recommended because the production frontend and API use the same origin.

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

The repository CI runs backend linting and tests, frontend linting and production builds, and an optional container build verification.

## Project structure

```text
backend/          FastAPI application, services, schemas, and tests
frontend/         React and TypeScript source
scripts/          Setup, development, run, and verification helpers
run.py            Cross-platform Uvicorn launcher
Dockerfile        Optional single-container production build
.github/workflows Continuous integration
```

## License

This project is distributed under the terms in [LICENSE](LICENSE).
