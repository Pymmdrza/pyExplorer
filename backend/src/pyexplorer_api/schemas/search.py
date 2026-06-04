"""Search schemas."""

from enum import StrEnum

from pydantic import BaseModel


class QueryType(StrEnum):
    TRANSACTION = "transaction"
    ADDRESS = "address"
    BLOCK = "block"


class SearchResult(BaseModel):
    query: str
    type: QueryType
    api_path: str
    frontend_path: str
