"""Tests for bounded asynchronous cache behavior."""

import asyncio

import pytest

from pyexplorer_api.services.cache import TTLCache


@pytest.mark.asyncio
async def test_cache_coalesces_concurrent_misses() -> None:
    cache: TTLCache[int] = TTLCache(max_entries=8)
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return 42

    results = await asyncio.gather(
        *(cache.get_or_set("shared", 30, factory) for _ in range(12))
    )

    assert results == [42] * 12
    assert calls == 1


@pytest.mark.asyncio
async def test_cache_evicts_least_recently_used_entry() -> None:
    cache: TTLCache[int] = TTLCache(max_entries=2)
    await cache.set("a", 1, 30)
    await cache.set("b", 2, 30)
    assert await cache.get("a") == 1
    await cache.set("c", 3, 30)

    assert await cache.get("a") == 1
    assert await cache.get("b") is None
    assert await cache.get("c") == 3
