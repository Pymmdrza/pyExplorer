"""Transaction routes."""

from fastapi import APIRouter

from pyexplorer_api.api.dependencies import BlockchainClientDep, CacheDep
from pyexplorer_api.schemas.transaction import TransactionResponse
from pyexplorer_api.services.transaction_service import TransactionService

router = APIRouter()


@router.get("/{tx_hash}", response_model=TransactionResponse)
async def transaction_detail(
    tx_hash: str,
    client: BlockchainClientDep,
    cache: CacheDep,
) -> TransactionResponse:
    return await TransactionService(client, cache).get_transaction(tx_hash)
