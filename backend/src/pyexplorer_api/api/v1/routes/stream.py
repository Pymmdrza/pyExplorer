"""Server-sent event routes."""

from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from pyexplorer_api.api.dependencies import RealtimeServiceDep
from pyexplorer_api.services.exporters import to_json

router = APIRouter()


@router.get("/transactions")
async def stream_transactions(
    request: Request,
    realtime: RealtimeServiceDep,
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        async for transaction in realtime.subscribe(heartbeat_seconds=15.0):
            if await request.is_disconnected():
                break
            if transaction is None:
                yield f'event: ping\ndata: {{"status": "{realtime.status}"}}\n\n'
            else:
                yield f"data: {to_json(transaction)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
