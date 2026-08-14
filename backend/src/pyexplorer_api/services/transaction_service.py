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
            normalized = normalise_transaction(raw)
            if normalized["confirmations"] == 0 and normalized["block_height"] > 0:
                try:
                    latest_height = await self.client.get_text_url(
                        self.client.settings.blockchain_url("blockcount")
                    )
                    if latest_height:
                        normalized["confirmations"] = max(
                            int(latest_height) - int(normalized["block_height"]) + 1, 0
                        )
                except Exception:
                    pass
            return TransactionResponse(**normalized)

        return await self.cache.get_or_set(
            f"transaction:{validated_hash}",
            self.client.settings.cache_resource_ttl_seconds,
            load,
        )
