"""Application-level exceptions with API-friendly metadata."""

from typing import Any


class AppError(Exception):
    """Base exception converted into a structured JSON API error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        code: str = "APP_ERROR",
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class BadRequestError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=400, code="BAD_REQUEST", details=details)


class NotFoundError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=404, code="NOT_FOUND", details=details)


class UpstreamServiceError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(
            message, status_code=502, code="UPSTREAM_SERVICE_ERROR", details=details
        )
