"""Network and block data services."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.constants import SATOSHI
from pyexplorer_api.exceptions import NotFoundError
from pyexplorer_api.schemas.block import BlockResponse, BlockTransaction
from pyexplorer_api.schemas.network import NetworkOverview, ProviderStatus
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.mappers import (
    extract_satoshis,
    parse_timestamp,
    to_float,
    to_int,
)
from pyexplorer_api.utils.pagination import paginate
from pyexplorer_api.utils.validators import validate_block_height


class NetworkService:
    def __init__(self, client: BlockchainClient, cache: TTLCache) -> None:
        self.client = client
        self.cache = cache

    async def get_overview(self) -> NetworkOverview:
        async def load() -> NetworkOverview:
            settings = self.client.settings
            stats_task = self.client.get_json_url(str(settings.blockchain_stats_url))
            difficulty_task = self.client.get_text_url(
                settings.blockchain_url("difficulty")
            )
            tx_count_task = self.client.get_text_url(
                settings.blockchain_url("tx_count_24h")
            )
            mempool_task = self.client.get_text_url(
                settings.blockchain_url("mempool_size")
            )
            blockcount_task = self.client.get_text_url(
                settings.blockchain_url("blockcount")
            )

            stats, difficulty, tx_count_24h, mempool_size, latest_height = (
                await asyncio.gather(
                    stats_task,
                    difficulty_task,
                    tx_count_task,
                    mempool_task,
                    blockcount_task,
                )
            )
            stats = stats or {}

            return NetworkOverview(
                market_price_usd=to_float(stats.get("market_price_usd")),
                hash_rate=to_float(stats.get("hash_rate")),
                total_fees_btc=to_float(stats.get("total_fees_btc")) / SATOSHI,
                total_blocks=to_int(stats.get("n_blocks_total") or latest_height),
                blocks_mined=to_int(stats.get("n_blocks_mined")),
                minutes_between_blocks=to_float(stats.get("minutes_between_blocks")),
                difficulty=to_float(difficulty),
                tx_count_24h=to_int(tx_count_24h),
                mempool_size=to_int(mempool_size),
                latest_block_height=to_int(latest_height),
                providers=[
                    ProviderStatus(name=provider.name, base_url=str(provider.base_url))
                    for provider in settings.providers
                ],
            )

        return await self.cache.get_or_set(
            "network:overview", self.client.settings.cache_stats_ttl_seconds, load
        )

    async def get_block(
        self, height: int | str, page: int = 1, per_page: int = 10
    ) -> BlockResponse:
        validated_height = validate_block_height(height)
        cache_key = f"block:{validated_height}:page:{page}:per_page:{per_page}"

        async def load() -> BlockResponse:
            raw = await self.client.get_block(validated_height)
            if raw is None:
                raise NotFoundError("Block not found.", {"height": validated_height})
            return self._normalise_block(raw, page, per_page)

        return await self.cache.get_or_set(
            cache_key, self.client.settings.cache_resource_ttl_seconds, load
        )

    def _normalise_block(
        self, raw: dict[str, Any], page: int, per_page: int
    ) -> BlockResponse:
        raw_transactions = raw.get("txs", []) or raw.get("transactions", []) or []
        if not isinstance(raw_transactions, list):
            raw_transactions = []
        transactions = [
            self._normalise_block_transaction(tx) for tx in raw_transactions
        ]
        paginated, meta = paginate(transactions, page, per_page)

        return BlockResponse(
            hash=raw.get("hash", ""),
            height=to_int(raw.get("height")),
            version=raw.get("version"),
            timestamp=parse_timestamp(raw, ("time", "timestamp", "blockTime"))
            or datetime.fromtimestamp(0, tz=UTC),
            tx_count=len(raw_transactions),
            size=to_int(raw.get("size")),
            merkle_root=raw.get("merkleRoot") or raw.get("merkleroot") or "",
            nonce=to_int(raw.get("nonce")),
            bits=raw.get("bits"),
            difficulty=to_float(raw.get("difficulty")),
            transactions=paginated,
            pagination=meta,
        )

    def _normalise_block_transaction(self, tx: dict[str, Any]) -> BlockTransaction:
        return BlockTransaction(
            hash=tx.get("txid") or tx.get("hash", ""),
            time=parse_timestamp(tx, ("blockTime", "time", "timestamp")),
            value_btc=extract_satoshis(tx, ("valueSat", "value")) / SATOSHI,
        )
