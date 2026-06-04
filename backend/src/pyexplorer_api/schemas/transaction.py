"""Transaction schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class TransactionEndpoint(BaseModel):
    address: str
    value_btc: float = Field(ge=0)


class TransactionResponse(BaseModel):
    hash: str
    time: datetime
    block_height: int = Field(ge=0)
    confirmations: int = Field(ge=0)
    size: int = Field(ge=0)
    value_btc: float = Field(ge=0)
    fee_btc: float = Field(ge=0)
    inputs: list[TransactionEndpoint]
    outputs: list[TransactionEndpoint]


class LiveTransaction(BaseModel):
    hash: str
    time: int | None = None
    amount_btc: float = Field(ge=0)
    from_addresses: list[str] = Field(default_factory=list)
    to_addresses: list[str] = Field(default_factory=list)
