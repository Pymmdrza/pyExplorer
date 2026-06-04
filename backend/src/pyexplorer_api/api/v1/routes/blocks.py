"""Block routes."""

from fastapi import APIRouter, Query

from pyexplorer_api.api.dependencies import BlockchainClientDep, CacheDep
from pyexplorer_api.schemas.block import BlockResponse
from pyexplorer_api.services.network_service import NetworkService

router = APIRouter()


@router.get("/{height}", response_model=BlockResponse)
async def block_detail(
    height: int,
    client: BlockchainClientDep,
    cache: CacheDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
) -> BlockResponse:
    return await NetworkService(client, cache).get_block(height, page, per_page)
