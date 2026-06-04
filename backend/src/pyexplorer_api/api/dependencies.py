"""FastAPI dependencies for shared app state."""

from typing import Annotated

from fastapi import Depends, Request

from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.config import Settings
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.realtime_transactions import RealtimeTransactionService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_blockchain_client(request: Request) -> BlockchainClient:
    return request.app.state.blockchain_client


def get_cache(request: Request) -> TTLCache:
    return request.app.state.cache


def get_realtime_service(request: Request) -> RealtimeTransactionService:
    return request.app.state.realtime


SettingsDep = Annotated[Settings, Depends(get_settings)]
BlockchainClientDep = Annotated[BlockchainClient, Depends(get_blockchain_client)]
CacheDep = Annotated[TTLCache, Depends(get_cache)]
RealtimeServiceDep = Annotated[
    RealtimeTransactionService, Depends(get_realtime_service)
]
