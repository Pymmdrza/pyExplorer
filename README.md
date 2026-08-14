# pyExplorer

pyExplorer is a lightweight Bitcoin blockchain explorer with a FastAPI service and a React interface. It provides transaction, address, block, network, export, and live mempool views while keeping the runtime footprint intentionally small.

## Features

- Transaction lookup with normalized inputs, outputs, fees, confirmations, and export support
- Address balances, transfer history, and pagination
- Block metadata and paginated transaction records
- Network overview with market, chain, mining, and mempool metrics
- Realtime unconfirmed transaction feed over Server-Sent Events
- Multi-provider fallback with bounded retries and temporary circuit breaking
- Bounded in-process TTL cache with concurrent request coalescing
- Responsive light and dark interfaces with keyboard and reduced-motion support
- Docker deployment with health checks, static asset caching, compression, and security headers

## Architecture

```text
Browser
  |
  v
Nginx / React
  |
  v
FastAPI
  |-- Network statistics endpoints
  |-- Bitcoin data providers with fallback
  `-- Blockchain websocket for realtime mempool events
```

The API uses asynchronous I/O end to end. The cache is process-local and bounded, which keeps the default deployment simple and avoids an external cache dependency. For multi-replica deployments, place a shared cache or gateway in front of the API if cross-instance cache coherence is required.

## Requirements

For local development:

- Python 3.13 or newer
- Node.js 24 LTS or newer
- npm 11 or newer

Docker users only need Docker Engine with Compose support.

## Quick start with Docker

```bash
docker compose up --build
```

Open:

- Web interface: `http://localhost:8080`
- API health: `http://localhost:8000/api/v1/health`
- OpenAPI documentation: `http://localhost:8000/docs`

Stop the stack with:

```bash
docker compose down
```

## Local development

### Backend

```bash
cd backend
python -m pip install -e '.[dev]'
python -m uvicorn pyexplorer_api.asgi:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The Vite development server proxies `/api` requests to `http://127.0.0.1:8000`.

## Configuration

Backend configuration uses environment variables prefixed with `PYEXPLORER_`. The defaults are suitable for local use. See `backend/.env.example` for the complete runtime configuration surface.

Frontend builds accept:

```text
VITE_API_BASE_URL=/api/v1
```

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

Interactive API documentation is exposed at `/docs`.

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

The repository CI executes backend linting and tests, frontend linting and production builds, and a final Docker Compose build.

## Project structure

```text
backend/          FastAPI application, services, schemas, and tests
frontend/         React and TypeScript application served by Nginx
scripts/          Local development helpers for Linux, macOS, and Windows
.github/workflows Continuous integration
```

## License

This project is distributed under the terms in [LICENSE](LICENSE).
