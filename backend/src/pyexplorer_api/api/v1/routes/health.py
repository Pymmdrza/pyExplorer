"""Health and readiness routes."""

from fastapi import APIRouter

from pyexplorer_api import __version__
from pyexplorer_api.api.dependencies import SettingsDep
from pyexplorer_api.schemas.common import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(version=__version__, environment=settings.environment)


@router.get("/ready", response_model=ReadyResponse)
async def ready(settings: SettingsDep) -> ReadyResponse:
    return ReadyResponse(
        ready=bool(settings.providers),
        providers=len(settings.providers),
        realtime_enabled=settings.realtime_enabled,
    )
