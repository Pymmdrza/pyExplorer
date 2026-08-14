# pyExplorer API

FastAPI application powering pyExplorer and serving the compiled web interface in production.

## Install

```bash
python -m pip install -e .
```

## Development

```bash
python -m uvicorn pyexplorer_api.asgi:app --reload --host 127.0.0.1 --port 8000
```

When `frontend/dist` exists in the repository, the same application also serves the compiled frontend. During frontend development, Vite should be used separately for hot module replacement.

## Verification

```bash
python -m pip install -e '.[dev]'
python -m ruff check src tests
python -m pytest --cov=pyexplorer_api --cov-report=term-missing
```

Runtime settings are documented in `.env.example`. All application settings use the `PYEXPLORER_` prefix.
