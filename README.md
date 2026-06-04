# pyExplorer

pyExplorer is being modernized from a legacy Flask/Jinja Bitcoin explorer into a professional FastAPI + React application.

The legacy Flask code is still kept in the repository during migration for rollback and parity checks. New development lives in `backend/` and `frontend/`.

## Modern stack

- **Backend:** FastAPI, Pydantic Settings, async `httpx`, provider fallback, TTL cache, SSE live transactions.
- **Frontend:** React, TypeScript, Vite, typed API client, responsive English dashboard UI.
- **Deployment:** Docker Compose with a FastAPI API container and an Nginx-served frontend container.

## Local development

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

- Web UI: `http://localhost:8080`
- API: `http://localhost:8000/api/v1`

## Quality gates

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
