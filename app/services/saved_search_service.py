from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TransactionFailedError
from app.core.pagination import clamp_limit
from app.models.saved_search import SavedSearch
from app.repositories.saved_search_repository import SavedSearchRepository
from app.schemas.saved_search import SavedSearchCreate, SavedSearchRead, SavedSearchUpdate


class SavedSearchService:
    def __init__(
        self,
        session: AsyncSession,
        saved_search_repository: SavedSearchRepository,
    ) -> None:
        self._session = session
        self._saved_searches = saved_search_repository

    async def list_for_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[SavedSearchRead]:
        limit = clamp_limit(limit)
        rows = await self._saved_searches.list_for_user(user_id, limit=limit, offset=offset)
        return [SavedSearchRead.model_validate(r) for r in rows]

    async def get_for_user(self, search_id: int, user_id: int) -> SavedSearchRead:
        row = await self._saved_searches.get_for_user(search_id, user_id)
        if row is None:
            raise EntityNotFoundError("SavedSearch", entity_id=search_id)
        return SavedSearchRead.model_validate(row)

    async def create_saved_search(self, data: SavedSearchCreate, user_id: int) -> SavedSearchRead:
        row = await self._saved_searches.create(
            SavedSearch(
                user_id=user_id,
                query_params=dict(data.query_params),
                is_active=data.is_active,
            )
        )
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to create saved search; transaction rolled back.",
            ) from exc
        await self._session.refresh(row)
        return SavedSearchRead.model_validate(row)

    async def update_for_user(
        self,
        search_id: int,
        user_id: int,
        data: SavedSearchUpdate,
    ) -> SavedSearchRead:
        row = await self._saved_searches.get_for_user(search_id, user_id)
        if row is None:
            raise EntityNotFoundError("SavedSearch", entity_id=search_id)

        payload = data.model_dump(exclude_unset=True)
        if "query_params" in payload:
            row.query_params = dict(payload["query_params"])
        if "is_active" in payload:
            row.is_active = bool(payload["is_active"])

        try:
            await self._session.flush()
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to update saved search; transaction rolled back.",
            ) from exc
        await self._session.refresh(row)
        return SavedSearchRead.model_validate(row)

    async def toggle_for_user(self, search_id: int, user_id: int) -> SavedSearchRead:
        row = await self._saved_searches.get_for_user(search_id, user_id)
        if row is None:
            raise EntityNotFoundError("SavedSearch", entity_id=search_id)
        row.is_active = not row.is_active
        try:
            await self._session.flush()
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to toggle saved search; transaction rolled back.",
            ) from exc
        await self._session.refresh(row)
        return SavedSearchRead.model_validate(row)

    async def delete_for_user(self, search_id: int, user_id: int) -> None:
        row = await self._saved_searches.get_for_user(search_id, user_id)
        if row is None:
            raise EntityNotFoundError("SavedSearch", entity_id=search_id)

        await self._saved_searches.delete(row)
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to delete saved search; transaction rolled back.",
            ) from exc
