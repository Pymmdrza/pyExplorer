"""Async client for Bitcoin provider APIs and blockchain.info utility endpoints."""

import asyncio
import logging
from typing import Any, Literal

import httpx

from pyexplorer_api.core.config import ProviderConfig, Settings
from pyexplorer_api.exceptions import UpstreamServiceError

logger = logging.getLogger(__name__)

EndpointType = Literal["address", "tx", "block", "block_index"]


class BlockchainClient:
    """Async HTTP client with provider fallback and bounded retry behavior."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout_seconds),
            headers={
                "User-Agent": "pyExplorer/0.1 (+https://github.com/Pymmdrza/pyExplorer)"
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_transaction(self, tx_hash: str) -> dict[str, Any] | None:
        return await self.get_provider_resource("tx", tx_hash, suffix="?page=1")

    async def get_address(
        self, address: str, detail_level: str = "txslight"
    ) -> dict[str, Any] | None:
        suffix = self.settings.providers[0].address_suffixes.get(detail_level, "")
        return await self.get_provider_resource("address", address, suffix=suffix)

    async def get_block(self, height: int | str) -> dict[str, Any] | None:
        return await self.get_provider_resource("block", str(height))

    async def get_provider_resource(
        self, endpoint_type: EndpointType, resource_id: str, suffix: str = ""
    ) -> dict[str, Any] | None:
        errors: list[dict[str, Any]] = []
        for provider in self.settings.providers:
            url = self._build_provider_url(provider, endpoint_type, resource_id, suffix)
            response = await self._request_json(url, provider.name)
            if response is not None:
                return response
            errors.append({"provider": provider.name, "url": url})

        logger.warning("All providers failed for %s/%s", endpoint_type, resource_id)
        return None

    async def get_json_url(self, url: str) -> dict[str, Any] | None:
        for attempt in range(1, self.settings.provider_max_retries + 1):
            try:
                response = await self._client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning(
                    "JSON request failed",
                    extra={"url": url, "attempt": attempt, "error": str(exc)},
                )
                await self._sleep_before_retry(attempt)
        raise UpstreamServiceError(
            "Unable to load blockchain JSON endpoint.", {"url": url}
        )

    async def get_text_url(self, url: str) -> str | None:
        for attempt in range(1, self.settings.provider_max_retries + 1):
            try:
                response = await self._client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.text.strip()
            except httpx.HTTPError as exc:
                logger.warning(
                    "Text request failed",
                    extra={"url": url, "attempt": attempt, "error": str(exc)},
                )
                await self._sleep_before_retry(attempt)
        raise UpstreamServiceError(
            "Unable to load blockchain text endpoint.", {"url": url}
        )

    async def _request_json(
        self, url: str, provider_name: str
    ) -> dict[str, Any] | None:
        for attempt in range(1, self.settings.provider_max_retries + 1):
            try:
                response = await self._client.get(url)
                if response.status_code == 404:
                    return None
                if response.status_code == 503:
                    logger.warning(
                        "Provider unavailable",
                        extra={"provider": provider_name, "url": url},
                    )
                    await self._sleep_before_retry(attempt)
                    continue
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                logger.warning(
                    "Provider network issue",
                    extra={"provider": provider_name, "error": str(exc)},
                )
                await self._sleep_before_retry(attempt)
            except (httpx.HTTPStatusError, ValueError) as exc:
                logger.warning(
                    "Provider response rejected",
                    extra={"provider": provider_name, "error": str(exc)},
                )
                return None
        return None

    def _build_provider_url(
        self,
        provider: ProviderConfig,
        endpoint_type: EndpointType,
        resource_id: str,
        suffix: str,
    ) -> str:
        base_url = str(provider.base_url).rstrip("/") + "/"
        if endpoint_type == "address":
            return f"{base_url}{provider.address_prefix}{resource_id}{suffix}"
        if endpoint_type == "tx":
            return f"{base_url}{provider.tx_prefix}{resource_id}{suffix}"
        if endpoint_type == "block":
            return f"{base_url}{provider.block_prefix}{resource_id}{suffix}"
        if endpoint_type == "block_index":
            return f"{base_url}{provider.block_index_prefix}{resource_id}{suffix}"
        raise ValueError(f"Unsupported endpoint type: {endpoint_type}")

    async def _sleep_before_retry(self, attempt: int) -> None:
        await asyncio.sleep(self.settings.retry_backoff_seconds * attempt)
