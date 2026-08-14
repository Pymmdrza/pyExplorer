"""Address business logic."""

from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.constants import SATOSHI
from pyexplorer_api.exceptions import NotFoundError
from pyexplorer_api.schemas.address import AddressResponse, AddressTransaction
from pyexplorer_api.schemas.common import PaginationMeta
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.mappers import extract_satoshis, parse_timestamp, to_float, to_int
from pyexplorer_api.utils.validators import validate_address


class AddressService:
    def __init__(self, client: BlockchainClient, cache: TTLCache) -> None:
        self.client = client
        self.cache = cache

    async def get_address(self, address: str, page: int = 1, per_page: int = 10) -> AddressResponse:
        validated_address = validate_address(address)
        bounded_per_page = min(per_page, 50)
        cache_key = f"address:{validated_address}:page:{page}:per_page:{bounded_per_page}"

        async def load() -> AddressResponse:
            raw = await self.client.get_address(
                validated_address, page=page, per_page=bounded_per_page
            )
            if raw is None:
                raise NotFoundError("Address not found.", {"address": validated_address})

            all_transactions = raw.get("transactions") or raw.get("txs") or []
            if not isinstance(all_transactions, list):
                all_transactions = []

            transactions = [
                self._normalise_address_transaction(tx, validated_address)
                for tx in all_transactions
                if isinstance(tx, dict)
            ]
            tx_count = to_int(raw.get("n_tx") or raw.get("txCount") or len(transactions))
            meta = PaginationMeta(
                current_page=page,
                per_page=bounded_per_page,
                total_items=tx_count,
                total_pages=max((tx_count + bounded_per_page - 1) // bounded_per_page, 1),
            )

            final_balance = raw.get("final_balance", raw.get("balance"))
            total_received = raw.get("total_received", raw.get("totalReceived"))
            total_sent = raw.get("total_sent", raw.get("totalSent"))

            return AddressResponse(
                address=str(raw.get("address") or validated_address),
                final_balance_btc=to_float(final_balance) / SATOSHI,
                total_received_btc=to_float(total_received) / SATOSHI,
                total_sent_btc=to_float(total_sent) / SATOSHI,
                tx_count=tx_count,
                transactions=transactions[:bounded_per_page],
                pagination=meta,
            )

        return await self.cache.get_or_set(
            cache_key, self.client.settings.cache_resource_ttl_seconds, load
        )

    def _normalise_address_transaction(self, tx: dict, address: str) -> AddressTransaction:
        balance_change_sat = 0
        outputs = tx.get("vout") or tx.get("out") or []
        inputs = tx.get("vin") or tx.get("inputs") or []

        for output in outputs if isinstance(outputs, list) else []:
            if not isinstance(output, dict):
                continue
            candidate = output.get("addr") or output.get("address")
            addresses = output.get("addresses", [])
            if candidate == address or (isinstance(addresses, list) and address in addresses):
                balance_change_sat += extract_satoshis(output, ("valueSat", "value"))

        for item in inputs if isinstance(inputs, list) else []:
            if not isinstance(item, dict):
                continue
            previous = item.get("prev_out") or item.get("prevOut") or item
            if not isinstance(previous, dict):
                continue
            candidate = previous.get("addr") or previous.get("address")
            addresses = previous.get("addresses", [])
            if candidate == address or (isinstance(addresses, list) and address in addresses):
                balance_change_sat -= extract_satoshis(previous, ("valueSat", "value"))

        return AddressTransaction(
            hash=str(tx.get("txid") or tx.get("hash", "")),
            time=parse_timestamp(
                tx, ("blockTime", "time", "blocktime", "receivedTime", "timestamp")
            ),
            value_btc=abs(balance_change_sat) / SATOSHI,
            balance_change_btc=balance_change_sat / SATOSHI,
        )
