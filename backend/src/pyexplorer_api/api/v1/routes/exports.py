"""Export routes."""

from fastapi import APIRouter
from fastapi.responses import Response

from pyexplorer_api.api.dependencies import BlockchainClientDep, CacheDep
from pyexplorer_api.exceptions import BadRequestError
from pyexplorer_api.services.address_service import AddressService
from pyexplorer_api.services.exporters import (
    address_to_csv,
    to_json,
    transaction_to_csv,
)
from pyexplorer_api.services.transaction_service import TransactionService

router = APIRouter()


@router.get("/transactions/{tx_hash}.{export_format}")
async def export_transaction(
    tx_hash: str,
    export_format: str,
    client: BlockchainClientDep,
    cache: CacheDep,
) -> Response:
    transaction = await TransactionService(client, cache).get_transaction(tx_hash)
    if export_format == "json":
        return Response(
            to_json(transaction),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=transaction-{tx_hash[:8]}.json"
            },
        )
    if export_format == "csv":
        return Response(
            transaction_to_csv(transaction),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=transaction-{tx_hash[:8]}.csv"
            },
        )
    raise BadRequestError("Unsupported export format.", {"format": export_format})


@router.get("/addresses/{address}.{export_format}")
async def export_address(
    address: str,
    export_format: str,
    client: BlockchainClientDep,
    cache: CacheDep,
) -> Response:
    address_data = await AddressService(client, cache).get_address(
        address, page=1, per_page=100
    )
    if export_format == "json":
        return Response(
            to_json(address_data),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=address-{address[:8]}.json"
            },
        )
    if export_format == "csv":
        return Response(
            address_to_csv(address_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=address-{address[:8]}.csv"
            },
        )
    raise BadRequestError("Unsupported export format.", {"format": export_format})
