"""Tests for realtime transaction fan-out behavior."""

import asyncio

import pytest

from pyexplorer_api.core.config import Settings
from pyexplorer_api.schemas.transaction import LiveTransaction
from pyexplorer_api.services.realtime_transactions import RealtimeTransactionService


@pytest.mark.asyncio
async def test_realtime_broadcasts_to_every_subscriber() -> None:
    service = RealtimeTransactionService(
        Settings(realtime_enabled=False, realtime_subscriber_queue_size=2)
    )
    subscriber_a = service.subscribe(heartbeat_seconds=1).__aiter__()
    subscriber_b = service.subscribe(heartbeat_seconds=1).__aiter__()

    first_a = asyncio.create_task(anext(subscriber_a))
    first_b = asyncio.create_task(anext(subscriber_b))
    await asyncio.sleep(0)

    event = LiveTransaction(hash="a" * 64, amount_btc=0.25)
    service._publish(event)

    assert await first_a == event
    assert await first_b == event

    await subscriber_a.aclose()
    await subscriber_b.aclose()
