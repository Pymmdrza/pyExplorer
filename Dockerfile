FROM node:24-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYEXPLORER_ENVIRONMENT=production

WORKDIR /app
RUN useradd --create-home --uid 10001 appuser

COPY backend/pyproject.toml backend/README.md ./backend/
COPY backend/src ./backend/src
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

RUN python -m pip install --no-cache-dir ./backend

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)" || exit 1

CMD ["uvicorn", "pyexplorer_api.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
