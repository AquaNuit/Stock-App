"""Generic repository — small, typed CRUD base.

Repositories own *all* SQL. Services compose them (docs/architecture.md §1).
Sessions are injected per-instance; callers manage commit via ``session_scope``
or the FastAPI dependency in ``api.deps``.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.base import Base

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    model: type[T]

    def __init__(self, session: Session):
        self.session = session

    def get(self, pk: int) -> T | None:
        return self.session.get(self.model, pk)

    def add(self, obj: T) -> T:
        self.session.add(obj)
        self.session.flush()
        return obj

    def list(self, *, limit: int = 100, offset: int = 0) -> list[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.scalars(stmt))

    def count(self) -> int:
        from sqlalchemy import func

        return int(self.session.scalar(select(func.count()).select_from(self.model)) or 0)

    def delete(self, obj: T) -> None:
        self.session.delete(obj)
        self.session.flush()
