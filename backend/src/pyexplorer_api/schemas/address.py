"""Address schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from pyexplorer_api.schemas.common import PaginationMeta


class AddressTransaction(BaseModel):
    hash: str
    time: datetime | None = None
    value_btc: float
    balance_change_btc: float


class AddressResponse(BaseModel):
    address: str
    final_balance_btc: float
    total_received_btc: float
    total_sent_btc: float
    tx_count: int = Field(ge=0)
    transactions: list[AddressTransaction]
    pagination: PaginationMeta
