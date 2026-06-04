"""Block schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from pyexplorer_api.schemas.common import PaginationMeta


class BlockTransaction(BaseModel):
    hash: str
    time: datetime | None = None
    value_btc: float = Field(ge=0)


class BlockResponse(BaseModel):
    hash: str
    height: int = Field(ge=0)
    version: str | int | None = None
    timestamp: datetime
    tx_count: int = Field(ge=0)
    size: int = Field(ge=0)
    merkle_root: str = ""
    nonce: int = Field(ge=0)
    bits: str | int | None = None
    difficulty: float = Field(ge=0)
    transactions: list[BlockTransaction]
    pagination: PaginationMeta
