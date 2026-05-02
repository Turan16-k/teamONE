"""T10: N+1 önleme ve pagination mekanizması"""
from typing import TypeVar, Generic, List
from pydantic import BaseModel
from sqlalchemy.orm import Query
from math import ceil

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    class Config:
        from_attributes = True


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
        "has_next": params.page < total_pages,
        "has_prev": params.page > 1,
    }
