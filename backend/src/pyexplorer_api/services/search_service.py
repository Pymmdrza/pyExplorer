"""Search dispatch logic."""

from pyexplorer_api.schemas.search import QueryType, SearchResult
from pyexplorer_api.utils.validators import classify_query


def search(query: str) -> SearchResult:
    query_type = classify_query(query)
    candidate = query.strip()
    if query_type == QueryType.TRANSACTION:
        return SearchResult(
            query=candidate,
            type=query_type,
            api_path=f"/transactions/{candidate.lower()}",
            frontend_path=f"/transactions/{candidate.lower()}",
        )
    if query_type == QueryType.ADDRESS:
        return SearchResult(
            query=candidate,
            type=query_type,
            api_path=f"/addresses/{candidate}",
            frontend_path=f"/addresses/{candidate}",
        )
    return SearchResult(
        query=candidate,
        type=query_type,
        api_path=f"/blocks/{int(candidate)}",
        frontend_path=f"/blocks/{int(candidate)}",
    )
