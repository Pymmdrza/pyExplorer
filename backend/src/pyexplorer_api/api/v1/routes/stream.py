"""Server-sent event routes."""

from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from pyexplorer_api.api.dependencies import RealtimeServiceDep
from pyexplorer_api.services.exporters import to_json

router = APIRouter()


@router.get("/transactions")
async def stream_transactions(
    realtime: RealtimeServiceDep,
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        while True:
            transaction = await realtime.next_event(heartbeat_seconds=15.0)
            if transaction is None:
                yield f'event: ping\ndata: {{"status": "{realtime.status}"}}\n\n'
                continue
            yield f"data: {to_json(transaction)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
