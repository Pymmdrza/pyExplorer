"""Search route."""

from fastapi import APIRouter, Query

from pyexplorer_api.schemas.search import SearchResult
from pyexplorer_api.services.search_service import search

router = APIRouter()


@router.get("", response_model=SearchResult)
async def search_query(q: str = Query(..., min_length=1)) -> SearchResult:
    return search(q)
