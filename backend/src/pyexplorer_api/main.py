"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pyexplorer_api import __version__
from pyexplorer_api.api.v1.router import api_router
from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.config import Settings, get_settings
from pyexplorer_api.core.logging import configure_logging
from pyexplorer_api.exceptions import AppError
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.realtime_transactions import RealtimeTransactionService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a FastAPI application instance."""
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = BlockchainClient(app_settings)
        cache = TTLCache()
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
            "Modern API for exploring Bitcoin transactions, addresses, blocks, "
            "and network data."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
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
