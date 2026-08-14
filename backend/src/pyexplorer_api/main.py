"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from pyexplorer_api import __version__
from pyexplorer_api.api.v1.router import api_router
from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.config import Settings, get_settings
from pyexplorer_api.core.logging import configure_logging
from pyexplorer_api.exceptions import AppError
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.realtime_transactions import RealtimeTransactionService

logger = logging.getLogger(__name__)


class ResponseHeadersMiddleware(BaseHTTPMiddleware):
    """Attach lightweight security and request-correlation headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a FastAPI application instance."""
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = BlockchainClient(app_settings)
        cache: TTLCache[object] = TTLCache(max_entries=app_settings.cache_max_entries)
        realtime = RealtimeTransactionService(app_settings)

        app.state.settings = app_settings
        app.state.blockchain_client = client
        app.state.cache = cache
        app.state.realtime = realtime

        if app_settings.realtime_enabled:
            await realtime.start()

        logger.info("pyExplorer API started", extra={"version": __version__})
        try:
            yield
        finally:
            logger.info("pyExplorer API shutting down")
            await realtime.stop()
            await client.aclose()

    app = FastAPI(
        title="pyExplorer API",
        description=(
            "Bitcoin blockchain explorer API for transactions, addresses, blocks, "
            "and network data."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
        openapi_url=f"{app_settings.api_prefix}/openapi.json",
    )

    app.add_middleware(ResponseHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "The request payload or parameters are invalid.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": None,
            },
        )

    app.include_router(api_router, prefix=app_settings.api_prefix)
    return app
