"""Network and block data services."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.constants import SATOSHI
from pyexplorer_api.exceptions import NotFoundError
from pyexplorer_api.schemas.block import BlockResponse, BlockTransaction
from pyexplorer_api.schemas.common import PaginationMeta
from pyexplorer_api.schemas.network import NetworkOverview, ProviderStatus
from pyexplorer_api.schemas.transaction import LiveTransaction
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.mappers import (
    extract_satoshis,
    parse_timestamp,
    to_float,
    to_int,
)
from pyexplorer_api.utils.pagination import paginate
from pyexplorer_api.utils.validators import validate_block_height

logger = logging.getLogger(__name__)


class NetworkService:
    def __init__(self, client: BlockchainClient, cache: TTLCache) -> None:
        self.client = client
        self.cache = cache

    async def get_overview(self) -> NetworkOverview:
        async def load() -> NetworkOverview:
            settings = self.client.settings
            stats_task = self._safe_json_url(str(settings.blockchain_stats_url))
            difficulty_task = self._safe_text_url(settings.blockchain_url("difficulty"))
            tx_count_task = self._safe_text_url(settings.blockchain_url("tx_count_24h"))
            mempool_count_task = self._safe_text_url(
                settings.blockchain_url("mempool_size")
            )
            mempool_stats_task = self._safe_json_url(str(settings.mempool_stats_url))
            blockcount_task = self._safe_text_url(settings.blockchain_url("blockcount"))

            (
                stats,
                difficulty,
                tx_count_24h,
                mempool_count,
                mempool_stats,
                latest_height,
            ) = await asyncio.gather(
                stats_task,
                difficulty_task,
                tx_count_task,
                mempool_count_task,
                mempool_stats_task,
                blockcount_task,
            )
            stats = stats or {}
            mempool_stats = mempool_stats or {}
            mempool_size = mempool_stats.get("count") or mempool_count

            return NetworkOverview(
                market_price_usd=to_float(stats.get("market_price_usd")),
                hash_rate=to_float(stats.get("hash_rate")),
                total_fees_btc=max(to_float(stats.get("total_fees_btc")) / SATOSHI, 0),
                total_blocks=to_int(stats.get("n_blocks_total") or latest_height),
                blocks_mined=to_int(stats.get("n_blocks_mined")),
                minutes_between_blocks=to_float(stats.get("minutes_between_blocks")),
                difficulty=to_float(difficulty),
                tx_count_24h=to_int(tx_count_24h),
                mempool_size=to_int(mempool_size),
                latest_block_height=to_int(latest_height),
                providers=[
                    ProviderStatus(
                        name=provider.name,
                        base_url=str(provider.base_url),
                        status=(
                            self.client.provider_status(provider.name)
                            if hasattr(self.client, "provider_status")
                            else "unknown"
                        ),
                    )
                    for provider in settings.providers
                ],
            )

        return await self.cache.get_or_set(
            "network:overview", self.client.settings.cache_stats_ttl_seconds, load
        )

    async def get_recent_mempool_transactions(
        self, limit: int = 20
    ) -> list[LiveTransaction]:
        bounded_limit = min(max(limit, 1), 50)
        cache_key = f"network:mempool:recent:{bounded_limit}"

        async def load() -> list[LiveTransaction]:
            raw = await self._safe_json_url(
                str(self.client.settings.unconfirmed_transactions_url)
            )
            if not raw:
                return []
            raw_transactions = raw.get("txs", [])
            if not isinstance(raw_transactions, list):
                return []
            return [
                self._normalise_live_transaction(tx)
                for tx in raw_transactions[:bounded_limit]
                if isinstance(tx, dict)
            ]

        return await self.cache.get_or_set(cache_key, 15, load)

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
        tx_count_source = raw.get("txCount")
        if tx_count_source is None:
            tx_count_source = (
                raw.get("txs")
                if isinstance(raw.get("txs"), int)
                else len(raw_transactions)
            )
        transactions = [
            self._normalise_block_transaction(tx) for tx in raw_transactions
        ]
        paginated, meta = paginate(transactions, page, per_page)
        tx_count = to_int(tx_count_source)
        if tx_count > len(raw_transactions):
            meta = PaginationMeta(
                current_page=page,
                per_page=per_page,
                total_items=tx_count,
                total_pages=max((tx_count + per_page - 1) // per_page, 1),
            )

        return BlockResponse(
            hash=raw.get("hash", ""),
            height=to_int(raw.get("height")),
            version=raw.get("version"),
            timestamp=parse_timestamp(raw, ("time", "timestamp", "blockTime"))
            or datetime.fromtimestamp(0, tz=UTC),
            tx_count=tx_count,
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

    def _normalise_live_transaction(self, tx: dict[str, Any]) -> LiveTransaction:
        outputs = tx.get("out", []) or []
        inputs = tx.get("inputs", []) or []
        if not isinstance(outputs, list):
            outputs = []
        if not isinstance(inputs, list):
            inputs = []

        return LiveTransaction(
            hash=str(tx.get("hash", "")),
            time=to_int(tx.get("time")) or None,
            amount_btc=sum(
                extract_satoshis(output, ("value", "valueSat")) for output in outputs
            )
            / SATOSHI,
            from_addresses=[
                previous.get("addr") or previous.get("address")
                for item in inputs
                if isinstance((previous := item.get("prev_out", {})), dict)
                and (previous.get("addr") or previous.get("address"))
            ],
            to_addresses=[
                address
                for output in outputs
                if isinstance(
                    (address := output.get("addr") or output.get("address")), str
                )
                and address
            ],
        )

    async def _safe_json_url(self, url: str) -> dict[str, Any] | None:
        try:
            return await self.client.get_json_url(url)
        except (
            Exception
        ) as exc:  # noqa: BLE001 - keep overview resilient to partial source outages.
            logger.warning(
                "Optional JSON source unavailable",
                extra={"url": url, "error": str(exc)},
            )
            return None

    async def _safe_text_url(self, url: str) -> str | None:
        try:
            return await self.client.get_text_url(url)
        except (
            Exception
        ) as exc:  # noqa: BLE001 - keep overview resilient to partial source outages.
            logger.warning(
                "Optional text source unavailable",
                extra={"url": url, "error": str(exc)},
            )
            return None
