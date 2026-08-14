"""Async client for Bitcoin data sources and public network endpoints."""

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
    """Pooled async client with internal fallback, retry, and circuit breaking."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._states = {
            provider.name: ProviderRuntimeState() for provider in settings.providers
        }
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout_seconds),
            limits=httpx.Limits(
                max_connections=settings.http_max_connections,
                max_keepalive_connections=settings.http_max_keepalive_connections,
            ),
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "pyExplorer/1.0",
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def provider_status(self, provider_name: str) -> str:
        """Return internal runtime state without exposing it through public schemas."""
        state = self._states.get(provider_name)
        if state is None:
            return "unknown"
        if state.unavailable_until > monotonic():
            return "degraded"
        return state.status

    async def get_transaction(self, tx_hash: str) -> dict[str, Any] | None:
        payload = await self.get_provider_resource("tx", tx_hash, suffix="?page=1")
        if payload is not None:
            return payload
        return await self.get_json_url(
            self.settings.transaction_url(tx_hash), allow_404=True
        )

    async def get_address(
        self,
        address: str,
        detail_level: str = "txslight",
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any] | None:
        for provider in self.settings.providers:
            suffix = provider.address_suffixes.get(detail_level, "")
            suffix = self._merge_query_suffix(
                suffix,
                {
                    "page": page,
                    "pageSize": per_page,
                },
            )
            response = await self._request_provider(
                provider,
                self._build_provider_url(provider, "address", address, suffix),
            )
            if response is not None:
                return response

        return await self.get_json_url(
            self.settings.address_url(address, page or 1, min(per_page or 10, 50)),
            allow_404=True,
        )

    async def get_block(self, height: int | str) -> dict[str, Any] | None:
        payload = await self.get_provider_resource("block", str(height))
        if payload is not None:
            return payload

        fallback = await self.get_json_url(
            self.settings.block_height_url(height), allow_404=True
        )
        if fallback is None:
            return None
        blocks = fallback.get("blocks")
        if isinstance(blocks, list):
            return next((item for item in blocks if isinstance(item, dict)), None)
        return fallback

    async def get_provider_resource(
        self, endpoint_type: EndpointType, resource_id: str, suffix: str = ""
    ) -> dict[str, Any] | None:
        for provider in self.settings.providers:
            url = self._build_provider_url(provider, endpoint_type, resource_id, suffix)
            response = await self._request_provider(provider, url)
            if response is not None:
                return response
        logger.warning("Internal data-source pool exhausted for %s", endpoint_type)
        return None

    async def get_json_url(
        self, url: str, *, allow_404: bool = False
    ) -> dict[str, Any] | None:
        response = await self._request(url, allow_404=allow_404)
        if response is None:
            return None
        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamServiceError("The data endpoint returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise UpstreamServiceError("The data endpoint returned an unexpected payload.")
        return payload

    async def get_text_url(self, url: str) -> str | None:
        response = await self._request(url, allow_404=True)
        if response is None:
            return None
        return response.text.strip()

    async def _request_provider(
        self, provider: ProviderConfig, url: str
    ) -> dict[str, Any] | None:
        state = self._states[provider.name]
        if state.unavailable_until > monotonic():
            return None

        response = await self._request(
            url,
            allow_404=True,
            tolerate_errors=True,
            log_label=provider.name,
            attempts=self.settings.provider_max_retries,
            timeout_seconds=self.settings.provider_request_timeout_seconds,
        )
        if response is None:
            self._record_provider_failure(provider.name)
            return None
        if response.status_code == 404:
            self._record_provider_success(provider.name)
            return None

        try:
            payload = response.json()
        except ValueError:
            self._record_provider_failure(provider.name)
            return None
        if not isinstance(payload, dict):
            self._record_provider_failure(provider.name)
            return None

        self._record_provider_success(provider.name)
        return payload

    async def _request(
        self,
        url: str,
        *,
        allow_404: bool = False,
        tolerate_errors: bool = False,
        log_label: str = "network",
        attempts: int | None = None,
        timeout_seconds: float | None = None,
    ) -> httpx.Response | None:
        attempts = max(attempts or self.settings.request_max_retries, 1)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.get(url, timeout=timeout_seconds)
                if response.status_code == 404 and allow_404:
                    return response if tolerate_errors else None
                if response.status_code == 429 or response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Transient upstream status {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                await self._sleep_before_retry(attempt)

        logger.warning(
            "Network data request failed",
            extra={"source": log_label, "error": str(last_error)},
        )
        if tolerate_errors:
            return None
        raise UpstreamServiceError(
            "Network data is temporarily unavailable. Please retry shortly."
        ) from last_error

    def _record_provider_success(self, provider_name: str) -> None:
        state = self._states[provider_name]
        state.failures = 0
        state.unavailable_until = 0.0
        state.status = "operational"

    def _record_provider_failure(self, provider_name: str) -> None:
        state = self._states[provider_name]
        state.failures += 1
        state.status = "degraded"
        if state.failures >= max(self.settings.provider_failure_threshold, 1):
            state.unavailable_until = monotonic() + max(
                self.settings.provider_cooldown_seconds, 0.0
            )
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
        base_delay = self.settings.retry_backoff_seconds * (2 ** (attempt - 1))
        jitter = random.uniform(0.85, 1.15)
        await asyncio.sleep(max(base_delay, 0.0) * jitter)

    @staticmethod
    def _merge_query_suffix(suffix: str, params: dict[str, Any]) -> str:
        query = dict(parse_qsl(suffix[1:] if suffix.startswith("?") else suffix))
        for key, value in params.items():
            if value is not None:
                query[key] = str(value)
        return f"?{urlencode(query)}" if query else ""
