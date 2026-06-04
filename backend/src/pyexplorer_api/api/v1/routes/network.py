"""Network routes."""

from fastapi import APIRouter

from pyexplorer_api.api.dependencies import BlockchainClientDep, CacheDep
from pyexplorer_api.schemas.network import NetworkOverview
from pyexplorer_api.services.network_service import NetworkService

router = APIRouter()


@router.get("/overview", response_model=NetworkOverview)
async def overview(
    client: BlockchainClientDep,
    cache: CacheDep,
) -> NetworkOverview:
    return await NetworkService(client, cache).get_overview()


@router.get("/metrics", response_model=NetworkOverview)
async def metrics(
    client: BlockchainClientDep,
    cache: CacheDep,
) -> NetworkOverview:
    return await NetworkService(client, cache).get_overview()
