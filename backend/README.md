# pyExplorer API

Modern FastAPI backend for the pyExplorer Bitcoin blockchain explorer. The legacy Flask app remains in the repository during migration for rollback and parity checks.

## Local development

Install dependencies from this folder:

```powershell
python -m pip install -e .[dev]
python -m uvicorn pyexplorer_api.asgi:app --reload --host 0.0.0.0 --port 8000
```

Health check: `http://localhost:8000/api/v1/health`

## Configuration

Settings use the `PYEXPLORER_` prefix and can be supplied through environment variables or `.env` files.

Useful defaults:

```text
PYEXPLORER_API_PREFIX=/api/v1
PYEXPLORER_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PYEXPLORER_REALTIME_ENABLED=true
```

## Quality gates

```powershell
python -m pytest
python -m ruff check src tests
```
