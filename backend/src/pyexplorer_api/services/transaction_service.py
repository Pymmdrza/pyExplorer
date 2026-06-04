"""Transaction business logic."""

from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.exceptions import NotFoundError
from pyexplorer_api.schemas.transaction import TransactionResponse
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.mappers import normalise_transaction
from pyexplorer_api.utils.validators import validate_tx_hash


class TransactionService:
    def __init__(self, client: BlockchainClient, cache: TTLCache) -> None:
        self.client = client
        self.cache = cache

    async def get_transaction(self, tx_hash: str) -> TransactionResponse:
        validated_hash = validate_tx_hash(tx_hash)

        async def load() -> TransactionResponse:
            raw = await self.client.get_transaction(validated_hash)
            if raw is None:
                raise NotFoundError(
                    "Transaction not found.", {"tx_hash": validated_hash}
                )
            return TransactionResponse(**normalise_transaction(raw))

        return await self.cache.get_or_set(
            f"transaction:{validated_hash}",
            self.client.settings.cache_resource_ttl_seconds,
            load,
        )
