# pyExplorer API

FastAPI service for pyExplorer.

## Development

```bash
python -m pip install -e '.[dev]'
python -m uvicorn pyexplorer_api.asgi:app --reload --host 127.0.0.1 --port 8000
```

## Verification

```bash
python -m ruff check src tests
python -m pytest --cov=pyexplorer_api --cov-report=term-missing
```

Runtime settings are documented in `.env.example`. All settings use the `PYEXPLORER_` prefix.
