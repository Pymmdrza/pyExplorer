from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from pyexplorer_api.api.dependencies import (
    get_blockchain_client,
    get_cache,
    get_realtime_service,
    get_settings,
)
from pyexplorer_api.core.config import Settings
from pyexplorer_api.main import create_app
from pyexplorer_api.services.cache import TTLCache

TEST_TX_HASH = "a" * 64
TEST_ADDRESS = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
TEST_BLOCK_HEIGHT = 840000


def make_test_settings() -> Settings:
    return Settings(_env_file=None, realtime_enabled=False)


def make_raw_transaction(tx_hash: str = TEST_TX_HASH) -> dict[str, Any]:
    return {
        "txid": tx_hash,
        "time": 1_710_000_000,
        "blockHeight": TEST_BLOCK_HEIGHT,
        "confirmations": 12,
        "size": 225,
        "fees": 1_000,
        "vin": [{"addresses": ["bc1qinputaddress"], "valueSat": 100_000}],
        "vout": [{"addresses": [TEST_ADDRESS], "valueSat": 99_000}],
    }


def make_raw_address(address: str = TEST_ADDRESS) -> dict[str, Any]:
    return {
        "balance": 50_000,
        "totalReceived": 150_000,
        "totalSent": 100_000,
        "transactions": [
            {
                "txid": "b" * 64,
                "time": 1_710_000_100,
                "vin": [{"addresses": ["bc1qsender"], "valueSat": 25_000}],
                "vout": [{"addresses": [address], "valueSat": 25_000}],
            },
            {
                "txid": "c" * 64,
                "time": 1_710_000_200,
                "vin": [{"addresses": [address], "valueSat": 10_000}],
                "vout": [{"addresses": ["bc1qreceiver"], "valueSat": 9_000}],
            },
        ],
    }


def make_raw_block(height: int = TEST_BLOCK_HEIGHT) -> dict[str, Any]:
    return {
        "hash": "f" * 64,
        "height": height,
        "version": 1,
        "time": 1_710_000_300,
        "size": 1_234_567,
        "merkleRoot": "d" * 64,
        "nonce": 42,
        "bits": "1705dd01",
        "difficulty": 86_388_558_925_171,
        "txs": [
            {"txid": TEST_TX_HASH, "time": 1_710_000_000, "valueSat": 99_000},
            {"txid": "e" * 64, "time": 1_710_000_100, "valueSat": 12_345},
        ],
    }


class FakeBlockchainClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.transactions = {TEST_TX_HASH: make_raw_transaction()}
        self.addresses = {TEST_ADDRESS: make_raw_address()}
        self.blocks = {TEST_BLOCK_HEIGHT: make_raw_block()}
        self.stats_payload = {
            "market_price_usd": 65_000,
            "hash_rate": 600_000_000,
            "total_fees_btc": 125_000_000,
            "n_blocks_total": TEST_BLOCK_HEIGHT,
            "n_blocks_mined": 144,
            "minutes_between_blocks": 9.8,
        }
        self.mempool_stats_payload = {"count": 12_345}
        self.unconfirmed_payload = {
            "txs": [
                {
                    "hash": "d" * 64,
                    "time": 1_710_000_400,
                    "inputs": [{"prev_out": {"addr": "bc1qliveinput"}}],
                    "out": [{"addr": "bc1qliveoutput", "value": 42_000}],
                }
            ]
        }
        self.text_payloads = {
            settings.blockchain_url("difficulty"): "86388558925171",
            settings.blockchain_url("tx_count_24h"): "412345",
            settings.blockchain_url("mempool_size"): "12345",
            settings.blockchain_url("blockcount"): str(TEST_BLOCK_HEIGHT),
        }

    async def get_transaction(self, tx_hash: str) -> dict[str, Any] | None:
        return self.transactions.get(tx_hash)

    async def get_address(
        self,
        address: str,
        detail_level: str = "txslight",
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any] | None:
        _ = page, per_page
        _ = detail_level
        return self.addresses.get(address)

    async def get_block(self, height: int | str) -> dict[str, Any] | None:
        return self.blocks.get(int(height))

    async def get_json_url(self, url: str) -> dict[str, Any] | None:
        if url == str(self.settings.mempool_stats_url):
            return self.mempool_stats_payload
        if url == str(self.settings.unconfirmed_transactions_url):
            return self.unconfirmed_payload
        return self.stats_payload

    async def get_text_url(self, url: str) -> str | None:
        return self.text_payloads.get(url)


class FakeRealtimeService:
    status = "idle"

    async def next_event(self, heartbeat_seconds: float = 15.0) -> None:
        _ = heartbeat_seconds
        return None


@pytest.fixture
def test_settings() -> Settings:
    return make_test_settings()


@pytest.fixture
def fake_blockchain_client(test_settings: Settings) -> FakeBlockchainClient:
    return FakeBlockchainClient(test_settings)


@pytest.fixture
def api_client(
    test_settings: Settings, fake_blockchain_client: FakeBlockchainClient
) -> Iterator[TestClient]:
    app = create_app(test_settings)
    cache = TTLCache()
    realtime = FakeRealtimeService()

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_blockchain_client] = lambda: fake_blockchain_client
    app.dependency_overrides[get_cache] = lambda: cache
    app.dependency_overrides[get_realtime_service] = lambda: realtime

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
