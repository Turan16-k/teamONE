"""T10: N+1 önleme ve güvenli pagination mekanizması."""
from math import ceil
from typing import TypeVar, Generic, List

from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Query

T = TypeVar("T")

_MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        return max(1, v)

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        return max(1, min(v, _MAX_PAGE_SIZE))

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PagedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


_SA_SKIP = {"_sa_instance_state"}


def orm_to_dict(obj) -> dict:
    return {k: v for k, v in vars(obj).items() if k not in _SA_SKIP}


def paginate(query: Query, params: PaginationParams) -> dict:
    total = query.count()
    items = query.offset(params.offset).limit(params.page_size).all()
    total_pages = ceil(total / params.page_size) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
        "pages": total_pages,
        "has_next": params.page < total_pages,
        "has_prev": params.page > 1,
    }
