"""Bounded asynchronous TTL cache with request coalescing."""

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Generic, TypeVar, cast

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Small in-process cache designed for single-worker deployments.

    Entries are bounded with least-recently-used eviction. Concurrent cache misses
    for the same key share one in-flight task so upstream services are not hit
    repeatedly during traffic bursts.
    """

    def __init__(self, max_entries: int = 512) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be greater than zero")
        self._max_entries = max_entries
        self._items: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self._inflight: dict[str, asyncio.Task[T]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> T | None:
        async with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at <= monotonic():
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return value

    async def set(self, key: str, value: T, ttl_seconds: float) -> None:
        if ttl_seconds <= 0:
            return
        async with self._lock:
            self._items[key] = (monotonic() + ttl_seconds, value)
            self._items.move_to_end(key)
            self._prune_expired_locked()
            while len(self._items) > self._max_entries:
                self._items.popitem(last=False)

    async def get_or_set(
        self, key: str, ttl_seconds: float, factory: Callable[[], Awaitable[T]]
    ) -> T:
        cached = await self.get(key)
        if cached is not None:
            return cached

        async with self._lock:
            task = self._inflight.get(key)
            if task is None:
                task = asyncio.create_task(factory())
                self._inflight[key] = task

        try:
            value = await asyncio.shield(task)
        finally:
            if task.done():
                async with self._lock:
                    if self._inflight.get(key) is task:
                        self._inflight.pop(key, None)

        await self.set(key, value, ttl_seconds)
        return cast(T, value)

    async def clear(self) -> None:
        async with self._lock:
            self._items.clear()

    def _prune_expired_locked(self) -> None:
        now = monotonic()
        expired = [key for key, (expires_at, _) in self._items.items() if expires_at <= now]
        for key in expired:
            self._items.pop(key, None)
