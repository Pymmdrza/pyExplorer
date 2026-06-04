"""Address business logic."""

from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.constants import SATOSHI
from pyexplorer_api.exceptions import NotFoundError
from pyexplorer_api.schemas.address import AddressResponse, AddressTransaction
from pyexplorer_api.services.cache import TTLCache
from pyexplorer_api.services.mappers import extract_satoshis, parse_timestamp, to_float
from pyexplorer_api.utils.pagination import paginate
from pyexplorer_api.utils.validators import validate_address


class AddressService:
    def __init__(self, client: BlockchainClient, cache: TTLCache) -> None:
        self.client = client
        self.cache = cache

    async def get_address(
        self, address: str, page: int = 1, per_page: int = 10
    ) -> AddressResponse:
        validated_address = validate_address(address)
        cache_key = f"address:{validated_address}:page:{page}:per_page:{per_page}"

        async def load() -> AddressResponse:
            raw = await self.client.get_address(validated_address)
            if raw is None:
                raise NotFoundError(
                    "Address not found.", {"address": validated_address}
                )

            all_transactions = raw.get("transactions", []) or raw.get("txs", []) or []
            if not isinstance(all_transactions, list):
                all_transactions = []

            transactions = [
                self._normalise_address_transaction(tx, validated_address)
                for tx in all_transactions
            ]
            paginated, meta = paginate(transactions, page, per_page)
            return AddressResponse(
                address=validated_address,
                final_balance_btc=to_float(raw.get("balance")) / SATOSHI,
                total_received_btc=to_float(raw.get("totalReceived")) / SATOSHI,
                total_sent_btc=to_float(raw.get("totalSent")) / SATOSHI,
                tx_count=len(all_transactions),
                transactions=paginated,
                pagination=meta,
            )

        return await self.cache.get_or_set(
            cache_key, self.client.settings.cache_resource_ttl_seconds, load
        )

    def _normalise_address_transaction(
        self, tx: dict, address: str
    ) -> AddressTransaction:
        balance_change_sat = 0
        for vout in tx.get("vout", []) or []:
            addresses = vout.get("addresses", [])
            if address in addresses:
                balance_change_sat += extract_satoshis(vout, ("valueSat", "value"))
        for vin in tx.get("vin", []) or []:
            addresses = vin.get("addresses", [])
            if address in addresses:
                balance_change_sat -= extract_satoshis(vin, ("valueSat", "value"))

        return AddressTransaction(
            hash=tx.get("txid") or tx.get("hash", ""),
            time=parse_timestamp(
                tx, ("blockTime", "time", "blocktime", "receivedTime", "timestamp")
            ),
            value_btc=abs(balance_change_sat) / SATOSHI,
            balance_change_btc=balance_change_sat / SATOSHI,
        )
