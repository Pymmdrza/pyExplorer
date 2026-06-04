"""Pagination helpers."""

from typing import TypeVar

from pyexplorer_api.exceptions import BadRequestError
from pyexplorer_api.schemas.common import PaginationMeta

T = TypeVar("T")


def paginate(
    items: list[T], page: int = 1, per_page: int = 10
) -> tuple[list[T], PaginationMeta]:
    if page < 1:
        raise BadRequestError(
            "Page must be greater than or equal to 1.", {"page": page}
        )
    if per_page < 1 or per_page > 100:
        raise BadRequestError(
            "per_page must be between 1 and 100.", {"per_page": per_page}
        )

    total_items = len(items)
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    return items[start_index:end_index], PaginationMeta(
        current_page=page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
    )
