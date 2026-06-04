"""Common response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Any | None = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    environment: str


class ReadyResponse(BaseModel):
    ready: bool
    providers: int
    realtime_enabled: bool


class PaginationMeta(BaseModel):
    current_page: int = Field(ge=1)
    per_page: int = Field(ge=1)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=1)
