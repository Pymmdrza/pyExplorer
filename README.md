# pyExplorer

pyExplorer is being modernized from a legacy Flask/Jinja Bitcoin explorer into a professional FastAPI + React application.

The legacy Flask code is still kept in the repository during migration for rollback and parity checks. New development lives in `backend/` and `frontend/`.

## Modern stack

- **Backend:** FastAPI, Pydantic Settings, async `httpx`, provider fallback, TTL cache, SSE live transactions.
- **Frontend:** React, TypeScript, Vite, typed API client, responsive English dashboard UI.
- **Deployment:** Docker Compose with a FastAPI API container and an Nginx-served frontend container.

## Local development

### One-command setup scripts

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\setup.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\windows\dev.ps1
```

Or double-click/run the wrappers:

```powershell
.\scripts\windows\setup.cmd
.\scripts\windows\dev.cmd
```

Linux/macOS:

```bash
chmod +x scripts/linux/*.sh
./scripts/linux/setup.sh
./scripts/linux/dev.sh
```

After startup:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/api/v1/health`

Stop local dev servers:

```powershell
.\scripts\windows\stop.cmd
```

```bash
./scripts/linux/stop.sh
```

### Backend

```powershell
cd backend
python -m pip install -e .[dev]
python -m uvicorn pyexplorer_api.asgi:app --reload --host 0.0.0.0 --port 8000
```

Health check: `http://localhost:8000/api/v1/health`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend dev server: `http://localhost:5173`

Vite proxies `/api/*` to `http://127.0.0.1:8000`.

## Docker demo

```powershell
docker compose up --build
```

Script alternatives:

```powershell
.\scripts\windows\docker-up.cmd
```

```bash
./scripts/linux/docker-up.sh
```

- Web UI: `http://localhost:8080`
- API: `http://localhost:8000/api/v1`

## Quality gates

Run all checks with scripts:

```powershell
.\scripts\windows\test.cmd
```

```bash
./scripts/linux/test.sh
```

### Backend

```powershell
cd backend
python -m pytest
python -m ruff check src tests
```

### Frontend

```powershell
cd frontend
npm run lint
npm run build
```

## Project layout

```text
backend/   FastAPI application package and tests
frontend/  React + TypeScript + Vite dashboard
app/       Legacy Flask application kept during migration
static/    Legacy static assets
templates/ Legacy Jinja templates
```

## Environment

A local `.env` can define `PYEXPLORER_` settings for the backend. Safe defaults are included for local/demo mode.

Important variables:

```text
PYEXPLORER_API_PREFIX=/api/v1
PYEXPLORER_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PYEXPLORER_REALTIME_ENABLED=true
PYEXPLORER_BLOCKCHAIN_WS_URL=wss://ws.blockchain.info/inv
```
