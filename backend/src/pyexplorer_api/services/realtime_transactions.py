"""Realtime unconfirmed transaction stream service."""

import asyncio
import json
import logging
from collections import deque
from contextlib import suppress
from typing import Any

import websockets

from pyexplorer_api.core.config import Settings
from pyexplorer_api.core.constants import SATOSHI
from pyexplorer_api.schemas.transaction import LiveTransaction

logger = logging.getLogger(__name__)


class RealtimeTransactionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.status = "idle"
        self._queue: asyncio.Queue[LiveTransaction] = asyncio.Queue(
            maxsize=settings.realtime_queue_size
        )
        self._latest: deque[LiveTransaction] = deque(
            maxlen=settings.realtime_queue_size
        )
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
        self.status = "stopped"

    async def next_event(
        self, heartbeat_seconds: float = 15.0
    ) -> LiveTransaction | None:
        try:
            async with asyncio.timeout(heartbeat_seconds):
                return await self._queue.get()
        except TimeoutError:
            return None

    async def _run(self) -> None:
        delay = self.settings.realtime_reconnect_initial_seconds
        while not self._stop_event.is_set():
            try:
                self.status = "connecting"
                async with websockets.connect(self.settings.blockchain_ws_url) as ws:
                    await ws.send(json.dumps({"op": "unconfirmed_sub"}))
                    self.status = "connected"
                    delay = self.settings.realtime_reconnect_initial_seconds
                    async for message in ws:
                        if self._stop_event.is_set():
                            break
                        event = self._parse_message(message)
                        if event:
                            await self._publish(event)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.status = "reconnecting"
                logger.warning("Realtime transaction stream disconnected: %s", exc)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.settings.realtime_reconnect_max_seconds)

    async def _publish(self, transaction: LiveTransaction) -> None:
        self._latest.appendleft(transaction)
        if self._queue.full():
            with suppress(asyncio.QueueEmpty):
                self._queue.get_nowait()
        await self._queue.put(transaction)

    def _parse_message(self, message: str | bytes) -> LiveTransaction | None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return None
        if data.get("op") != "utx":
            return None
        tx: dict[str, Any] = data.get("x", {})
        outputs = tx.get("out", []) or []
        inputs = tx.get("inputs", []) or []
        return LiveTransaction(
            hash=tx.get("hash", ""),
            time=tx.get("time"),
            amount_btc=sum(output.get("value", 0) for output in outputs) / SATOSHI,
            from_addresses=[
                previous.get("addr")
                for item in inputs
                if isinstance((previous := item.get("prev_out", {})), dict)
                and previous.get("addr")
            ],
            to_addresses=[
                output.get("addr") for output in outputs if output.get("addr")
            ],
        )
