"""Realtime unconfirmed transaction broadcast service."""

import asyncio
import json
import logging
import random
from collections import deque
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any

import websockets

from pyexplorer_api.core.config import Settings
from pyexplorer_api.core.constants import SATOSHI
from pyexplorer_api.schemas.transaction import LiveTransaction

logger = logging.getLogger(__name__)


class RealtimeTransactionService:
    """Maintain one upstream websocket and broadcast events to SSE subscribers."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.status = "idle"
        self._latest: deque[LiveTransaction] = deque(maxlen=settings.realtime_queue_size)
        self._subscribers: set[asyncio.Queue[LiveTransaction]] = set()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._run(), name="pyexplorer-realtime-transactions"
        )

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        self._task = None
        self._subscribers.clear()
        self.status = "stopped"

    def latest(self, limit: int = 20) -> list[LiveTransaction]:
        return list(self._latest)[: max(limit, 0)]

    async def subscribe(
        self, heartbeat_seconds: float = 15.0
    ) -> AsyncIterator[LiveTransaction | None]:
        queue: asyncio.Queue[LiveTransaction] = asyncio.Queue(
            maxsize=self.settings.realtime_subscriber_queue_size
        )
        self._subscribers.add(queue)
        try:
            while True:
                try:
                    async with asyncio.timeout(heartbeat_seconds):
                        yield await queue.get()
                except TimeoutError:
                    yield None
        finally:
            self._subscribers.discard(queue)

    async def _run(self) -> None:
        delay = self.settings.realtime_reconnect_initial_seconds
        while not self._stop_event.is_set():
            try:
                self.status = "connecting"
                async with websockets.connect(
                    self.settings.blockchain_ws_url,
                    open_timeout=self.settings.request_timeout_seconds,
                    close_timeout=3,
                    ping_interval=20,
                    ping_timeout=20,
                    max_queue=32,
                ) as ws:
                    await ws.send(json.dumps({"op": "unconfirmed_sub"}))
                    self.status = "connected"
                    delay = self.settings.realtime_reconnect_initial_seconds
                    async for message in ws:
                        if self._stop_event.is_set():
                            break
                        event = self._parse_message(message)
                        if event is not None:
                            self._publish(event)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.status = "reconnecting"
                logger.warning("Realtime transaction stream disconnected: %s", exc)
                jitter = random.uniform(0.85, 1.15)
                await asyncio.sleep(delay * jitter)
                delay = min(delay * 2, self.settings.realtime_reconnect_max_seconds)

    def _publish(self, transaction: LiveTransaction) -> None:
        self._latest.appendleft(transaction)
        for queue in tuple(self._subscribers):
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            with suppress(asyncio.QueueFull):
                queue.put_nowait(transaction)

    def _parse_message(self, message: str | bytes) -> LiveTransaction | None:
        try:
            data = json.loads(message)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(data, dict) or data.get("op") != "utx":
            return None
        tx: dict[str, Any] = data.get("x", {})
        if not isinstance(tx, dict):
            return None
        outputs = tx.get("out", []) or []
        inputs = tx.get("inputs", []) or []
        tx_hash = tx.get("hash")
        if not isinstance(tx_hash, str) or not tx_hash:
            return None
        return LiveTransaction(
            hash=tx_hash,
            time=tx.get("time"),
            amount_btc=sum(
                output.get("value", 0)
                for output in outputs
                if isinstance(output, dict)
            )
            / SATOSHI,
            from_addresses=[
                previous.get("addr")
                for item in inputs
                if isinstance(item, dict)
                and isinstance((previous := item.get("prev_out", {})), dict)
                and isinstance(previous.get("addr"), str)
            ],
            to_addresses=[
                output.get("addr")
                for output in outputs
                if isinstance(output, dict) and isinstance(output.get("addr"), str)
            ],
        )
