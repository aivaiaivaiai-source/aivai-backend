from __future__ import annotations

from app.repositories.health_repository import HealthRepository


class HealthService:
    def __init__(self, health_repository: HealthRepository) -> None:
        self._health = health_repository

    async def check(self) -> dict[str, str]:
        await self._health.ping_db()
        return {"status": "ok"}
