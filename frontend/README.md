# pyExplorer Frontend

Modern React + TypeScript + Vite dashboard for the new pyExplorer FastAPI backend.
The app uses React Router for client-side dashboard and detail pages.

## Local development

1. Start the backend on `http://127.0.0.1:8000`.
2. Install dependencies with `npm install`.
3. Start the frontend with `npm run dev`.

The Vite dev server runs on `http://localhost:5173` and proxies `/api/*` to the backend.

## Environment

Copy `.env.example` to `.env.local` if you need to override the API base path:

```text
VITE_API_BASE_URL=/api/v1
```

## Quality gates

- `npm run lint` — ESLint checks.
- `npm run build` — TypeScript project build and production bundle.

## Structure

- `src/api/` — typed API client and response contracts.
- `src/hooks/` — network overview and SSE transaction stream hooks.
- `src/components/` — reusable dashboard components.
- `src/pages/` — dashboard plus transaction, address, block, and 404 pages.
- `src/App.tsx` — client-side route composition.
