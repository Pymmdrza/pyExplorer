"""API v1 router composition."""

from fastapi import APIRouter

from pyexplorer_api.api.v1.routes import (
    addresses,
    blocks,
    exports,
    health,
    network,
    search,
    stream,
    transactions,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(network.router, prefix="/network", tags=["network"])
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(blocks.router, prefix="/blocks", tags=["blocks"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
