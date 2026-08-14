# pyExplorer Web

React and TypeScript interface for pyExplorer.

## Install

```bash
npm install
```

## Development

```bash
npm run dev
```

The development server proxies `/api` to `http://127.0.0.1:8000`.

## Production build

```bash
npm run build
```

The generated `dist` directory is served directly by the FastAPI application under Uvicorn. No standalone web server is required.

## Verification

```bash
npm run lint
npm run build
```

Set `VITE_API_BASE_URL` only when the API is hosted at a different path or origin. The default is `/api/v1`.
