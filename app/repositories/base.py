from __future__ import annotations

from typing import Any, Generic, TypeVar, overload

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_class import Base as ORMBase

ModelType = TypeVar("ModelType", bound=ORMBase)

_FORBIDDEN_UPDATE_FIELDS = frozenset({"id", "created_at", "updated_at"})


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, entity_id: int) -> ModelType | None:
        stmt = select(self._model).where(self._model.id == entity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        stmt = (
            select(self._model)
            .order_by(self._model.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj: ModelType) -> ModelType:
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def update(self, entity_id: int, **values: Any) -> ModelType | None:
        obj = await self.get_by_id(entity_id)
        if obj is None:
            return None
        safe = {k: v for k, v in values.items() if k not in _FORBIDDEN_UPDATE_FIELDS}
        for key, value in safe.items():
            setattr(obj, key, value)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    @overload
    async def delete(self, target: int) -> bool: ...

    @overload
    async def delete(self, target: ModelType) -> bool: ...

    async def delete(self, target: int | ModelType) -> bool:
        if isinstance(target, int):
            obj = await self.get_by_id(target)
            if obj is None:
                return False
            await self._session.delete(obj)
        elif isinstance(target, self._model):
            await self._session.delete(target)
        else:
            raise TypeError(
                f"delete() expects int or {self._model.__name__}, got {type(target)!r}"
            )
        await self._session.flush()
        return True
