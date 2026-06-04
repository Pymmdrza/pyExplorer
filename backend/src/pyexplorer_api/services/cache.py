"""Small async TTL cache for local/demo use."""

import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import TypeVar

T = TypeVar("T")


class TTLCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, object]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> object | None:
        async with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at <= monotonic():
                self._items.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: object, ttl_seconds: int) -> None:
        async with self._lock:
            self._items[key] = (monotonic() + ttl_seconds, value)

    async def get_or_set(
        self, key: str, ttl_seconds: int, factory: Callable[[], Awaitable[T]]
    ) -> T:
        cached = await self.get(key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        value = await factory()
        await self.set(key, value, ttl_seconds)
        return value
