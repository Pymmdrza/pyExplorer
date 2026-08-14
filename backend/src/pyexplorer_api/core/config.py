"""Runtime settings for pyExplorer."""

import json
from functools import lru_cache
from typing import Annotated, Any

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class ProviderConfig(BaseModel):
    """Internal upstream endpoint configuration."""

    name: str
    base_url: AnyHttpUrl
    address_prefix: str = "address/"
    tx_prefix: str = "tx/"
    block_prefix: str = "block/"
    block_index_prefix: str = "block-index/"
    address_suffixes: dict[str, str] = Field(
        default_factory=lambda: {
            "basic": "?details=basic",
            "txs": "?details=txs",
            "txslight": "?details=txslight",
        }
    )


def default_providers() -> list[ProviderConfig]:
    return [
        ProviderConfig(
            name="atomic", base_url="https://bitcoin.atomicwallet.io/api/v2/"
        ),
        ProviderConfig(name="guarda", base_url="https://btcbook.guarda.co/api/v2/"),
        ProviderConfig(name="trezor", base_url="https://btc1.trezor.io/api/v2/"),
    ]


def default_blockchain_paths() -> dict[str, str]:
    return {
        "difficulty": "q/getdifficulty",
        "blockcount": "q/getblockcount",
        "latest_hash": "q/latesthash",
        "tx_count_24h": "q/24hrtransactioncount",
        "mempool_size": "q/unconfirmedcount",
        "marketcap": "q/marketcap",
        "hash_rate": "q/hashrate",
    }


class Settings(BaseSettings):
    """Validated application settings with self-contained local defaults."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_prefix="PYEXPLORER_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    environment: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    request_timeout_seconds: float = 12.0
    request_max_retries: int = 3
    provider_request_timeout_seconds: float = 6.0
    provider_max_retries: int = 1
    retry_backoff_seconds: float = 0.35

    cache_stats_ttl_seconds: int = 120
    cache_resource_ttl_seconds: int = 600
    cache_max_entries: int = 512

    http_max_connections: int = 24
    http_max_keepalive_connections: int = 12
    provider_failure_threshold: int = 3
    provider_cooldown_seconds: float = 20.0

    realtime_enabled: bool = True
    blockchain_ws_url: str = "wss://ws.blockchain.info/inv"
    realtime_queue_size: int = 200
    realtime_subscriber_queue_size: int = 32
    realtime_reconnect_initial_seconds: float = 3.0
    realtime_reconnect_max_seconds: float = 60.0

    blockchain_stats_url: AnyHttpUrl = "https://api.blockchain.info/stats"
    blockchain_base_url: AnyHttpUrl = "https://blockchain.info/"
    mempool_stats_url: AnyHttpUrl = "https://mempool.space/api/mempool"
    unconfirmed_transactions_url: AnyHttpUrl = (
        "https://blockchain.info/unconfirmed-transactions?format=json"
    )
    blockchain_paths: dict[str, str] = Field(default_factory=default_blockchain_paths)
    providers: list[ProviderConfig] = Field(default_factory=default_providers)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    def blockchain_url(self, key: str) -> str:
        path = self.blockchain_paths[key]
        return f"{str(self.blockchain_base_url).rstrip('/')}/{path}"

    def transaction_url(self, tx_hash: str) -> str:
        return f"{str(self.blockchain_base_url).rstrip('/')}/rawtx/{tx_hash}?format=json"

    def address_url(self, address: str, page: int, per_page: int) -> str:
        offset = max(page - 1, 0) * per_page
        return (
            f"{str(self.blockchain_base_url).rstrip('/')}/rawaddr/{address}"
            f"?limit={per_page}&offset={offset}"
        )

    def block_height_url(self, height: int | str) -> str:
        return (
            f"{str(self.blockchain_base_url).rstrip('/')}/block-height/{height}"
            "?format=json"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
