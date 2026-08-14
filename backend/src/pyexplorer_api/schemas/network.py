"""Network overview schemas."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class NetworkOverview(BaseModel):
    market_price_usd: float = Field(ge=0)
    hash_rate: float = Field(ge=0)
    total_fees_btc: float = Field(ge=0)
    total_blocks: int = Field(ge=0)
    blocks_mined: int = Field(ge=0)
    minutes_between_blocks: float = Field(ge=0)
    difficulty: float = Field(ge=0)
    tx_count_24h: int = Field(ge=0)
    mempool_size: int = Field(ge=0)
    latest_block_height: int = Field(ge=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
