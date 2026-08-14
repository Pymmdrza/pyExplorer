"""Async client for Bitcoin provider APIs and public network endpoints."""

import asyncio
import logging
import random
from dataclasses import dataclass
from time import monotonic
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode

import httpx

from pyexplorer_api.core.config import ProviderConfig, Settings
from pyexplorer_api.exceptions import UpstreamServiceError

logger = logging.getLogger(__name__)

EndpointType = Literal["address", "tx", "block", "block_index"]


@dataclass(slots=True)
class ProviderRuntimeState:
    failures: int = 0
    unavailable_until: float = 0.0
    status: str = "unknown"


class BlockchainClient:
    """Async HTTP client with fallback, retry, and lightweight circuit breaking."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._states = {provider.name: ProviderRuntimeState() for provider in settings.providers}
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout_seconds),
            limits=httpx.Limits(
                max_connections=settings.http_max_connections,
                max_keepalive_connections=settings.http_max_keepalive_connections,
            ),
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "pyExplorer/1.0 (+https://github.com/Pymmdrza/pyExplorer)",
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def provider_status(self, provider_name: str) -> str:
        state = self._states.get(provider_name)
        if state is None:
            return "unknown"
        if state.unavailable_until > monotonic():
            return "degraded"
        return state.status

    async def get_transaction(self, tx_hash: str) -> dict[str, Any] | None:
        return await self.get_provider_resource("tx", tx_hash, suffix="?page=1")

    async def get_address(
        self,
        address: str,
        detail_level: str = "txslight",
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any] | None:
        for provider in self.settings.providers:
            suffix = provider.address_suffixes.get(detail_level, "")
            suffix = self._merge_query_suffix(suffix, {"page": page, "pageSize": per_page})
            response = await self._request_provider(
                provider,
                self._build_provider_url(provider, "address", address, suffix),
            )
            if response is not None:
                return response
        logger.warning("All providers failed for address resource")
        if self.settings.providers and all(
            self.provider_status(provider.name) == "degraded"
            for provider in self.settings.providers
        ):
            raise UpstreamServiceError("All configured data providers are unavailable.")
        return None

    async def get_block(self, height: int | str) -> dict[str, Any] | None:
        return await self.get_provider_resource("block", str(height))

    async def get_provider_resource(
        self, endpoint_type: EndpointType, resource_id: str, suffix: str = ""
    ) -> dict[str, Any] | None:
        for provider in self.settings.providers:
            url = self._build_provider_url(provider, endpoint_type, resource_id, suffix)
            response = await self._request_provider(provider, url)
            if response is not None:
                return response
        logger.warning("All providers failed for %s resource", endpoint_type)
        if self.settings.providers and all(
            self.provider_status(provider.name) == "degraded"
            for provider in self.settings.providers
        ):
            raise UpstreamServiceError("All configured data providers are unavailable.")
        return None

    async def get_json_url(self, url: str) -> dict[str, Any] | None:
        response = await self._request(url, label="network endpoint")
        if response is None or response.status_code == 404:
            return None
        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamServiceError("Network endpoint returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise UpstreamServiceError("Network endpoint returned an unexpected payload.")
        return payload

    async def get_text_url(self, url: str) -> str | None:
        response = await self._request(url, label="network endpoint")
        if response is None or response.status_code == 404:
            return None
        return response.text.strip()

    async def _request_provider(
        self, provider: ProviderConfig, url: str
    ) -> dict[str, Any] | None:
        state = self._states[provider.name]
        if state.unavailable_until > monotonic():
            return None

        try:
            response = await self._request(url, label=provider.name, tolerate_errors=True)
        except UpstreamServiceError:
            self._record_provider_failure(provider.name)
            return None
        if response is None:
            self._record_provider_failure(provider.name)
            return None
        if response.status_code == 404:
            state.failures = 0
            state.unavailable_until = 0.0
            state.status = "operational"
            return None
        try:
            payload = response.json()
        except ValueError:
            self._record_provider_failure(provider.name)
            return None
        if not isinstance(payload, dict):
            self._record_provider_failure(provider.name)
            return None
        state.failures = 0
        state.unavailable_until = 0.0
        state.status = "operational"
        return payload

    async def _request(
        self,
        url: str,
        *,
        label: str,
        tolerate_errors: bool = False,
    ) -> httpx.Response | None:
        attempts = max(self.settings.provider_max_retries, 1)
        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.get(url)
                if response.status_code == 404:
                    return response
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < attempts:
                        await self._sleep_before_retry(attempt)
                        continue
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                logger.warning(
                    "Upstream network failure",
                    extra={"source": label, "attempt": attempt},
                )
                if attempt < attempts:
                    await self._sleep_before_retry(attempt)
                    continue
                if tolerate_errors:
                    return None
                raise UpstreamServiceError("Unable to reach an upstream network service.") from exc
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Upstream HTTP failure",
                    extra={"source": label, "status": exc.response.status_code},
                )
                if tolerate_errors:
                    return None
                raise UpstreamServiceError(
                    "An upstream network service rejected the request.",
                    {"status": exc.response.status_code},
                ) from exc
        return None

    def _record_provider_failure(self, provider_name: str) -> None:
        state = self._states[provider_name]
        state.failures += 1
        state.status = "degraded"
        if state.failures >= self.settings.provider_failure_threshold:
            state.unavailable_until = monotonic() + self.settings.provider_cooldown_seconds
            state.failures = 0

    def _build_provider_url(
        self,
        provider: ProviderConfig,
        endpoint_type: EndpointType,
        resource_id: str,
        suffix: str,
    ) -> str:
        base_url = str(provider.base_url).rstrip("/") + "/"
        prefix = {
            "address": provider.address_prefix,
            "tx": provider.tx_prefix,
            "block": provider.block_prefix,
            "block_index": provider.block_index_prefix,
        }[endpoint_type]
        return f"{base_url}{prefix}{resource_id}{suffix}"

    async def _sleep_before_retry(self, attempt: int) -> None:
        base = self.settings.retry_backoff_seconds * (2 ** (attempt - 1))
        await asyncio.sleep(base * random.uniform(0.85, 1.15))

    @staticmethod
    def _merge_query_suffix(suffix: str, params: dict[str, Any]) -> str:
        query = dict(parse_qsl(suffix[1:] if suffix.startswith("?") else suffix))
        for key, value in params.items():
            if value is not None:
                query[key] = str(value)
        return f"?{urlencode(query)}" if query else ""
