"""Tests for the internal data-source fallback chain."""

import httpx
import pytest

from pyexplorer_api.clients.blockchain_client import BlockchainClient
from pyexplorer_api.core.config import Settings


@pytest.mark.asyncio
async def test_internal_pool_falls_through_to_next_source() -> None:
    settings = Settings(_env_file=None, request_max_retries=1, realtime_enabled=False)
    client = BlockchainClient(settings)
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        if request.url.host == "bitcoin.atomicwallet.io":
            return httpx.Response(503, request=request)
        if request.url.host == "btcbook.guarda.co":
            return httpx.Response(200, json={"txid": "a" * 64}, request=request)
        return httpx.Response(500, request=request)

    await client._client.aclose()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        payload = await client.get_transaction("a" * 64)
    finally:
        await client.aclose()

    assert payload == {"txid": "a" * 64}
    assert calls == ["bitcoin.atomicwallet.io", "btcbook.guarda.co"]


@pytest.mark.asyncio
async def test_public_fallback_is_used_when_internal_pool_is_unavailable() -> None:
    settings = Settings(_env_file=None, request_max_retries=1, realtime_enabled=False)
    client = BlockchainClient(settings)
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        if request.url.host in {
            "bitcoin.atomicwallet.io",
            "btcbook.guarda.co",
            "btc1.trezor.io",
        }:
            return httpx.Response(503, request=request)
        if request.url.host == "blockchain.info" and request.url.path.startswith("/rawtx/"):
            return httpx.Response(200, json={"hash": "b" * 64}, request=request)
        return httpx.Response(404, request=request)

    await client._client.aclose()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        payload = await client.get_transaction("b" * 64)
    finally:
        await client.aclose()

    assert payload == {"hash": "b" * 64}
    assert calls[:3] == [
        "bitcoin.atomicwallet.io",
        "btcbook.guarda.co",
        "btc1.trezor.io",
    ]
    assert calls[-1] == "blockchain.info"


@pytest.mark.asyncio
async def test_provider_runtime_details_are_not_part_of_public_readiness() -> None:
    from fastapi.testclient import TestClient

    from pyexplorer_api.main import create_app

    settings = Settings(_env_file=None, realtime_enabled=False)
    app = create_app(settings)

    with TestClient(app) as api:
        payload = api.get("/api/v1/ready").json()

    assert payload == {"ready": True, "realtime_enabled": False}
    assert "providers" not in payload
