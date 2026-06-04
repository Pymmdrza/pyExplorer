"""Address routes."""

from fastapi import APIRouter, Query

from pyexplorer_api.api.dependencies import BlockchainClientDep, CacheDep
from pyexplorer_api.schemas.address import AddressResponse
from pyexplorer_api.services.address_service import AddressService

router = APIRouter()


@router.get("/{address}", response_model=AddressResponse)
async def address_detail(
    address: str,
    client: BlockchainClientDep,
    cache: CacheDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
) -> AddressResponse:
    return await AddressService(client, cache).get_address(address, page, per_page)
