"""Concurrent media complete + listing-level classification/VE idempotency races."""

from __future__ import annotations

import asyncio
import io
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.idempotency import insert_or_get_on_unique, is_unique_violation
from app.db.session import async_session_maker, engine
from app.main import app
from app.media_classification.fingerprint import media_set_fingerprint
from app.models.media_classification_enums import MediaClassificationStatus
from app.models.visual_evidence_enums import VisualEvidenceStatus
from app.schemas.user import UserRead
from app.services.media_classification_service import MediaClassificationService
from app.services.visual_evidence_service import VisualEvidenceService
from app.visual_evidence.stub_provider import StubVisualEvidenceProvider


def _jpeg_bytes(color: tuple[int, int, int] = (12, 34, 56)) -> bytes:
    img = Image.new("RGB", (320, 240), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="ConcurrentMediaTester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


@asynccontextmanager
async def _nested_cm():
    yield


def _session_with_nested() -> MagicMock:
    session = MagicMock()
    session.begin_nested = MagicMock(side_effect=lambda: _nested_cm())
    return session


def test_is_unique_violation_matches_constraint_name() -> None:
    class Orig(Exception):
        constraint_name = "uq_media_classifications_idempotency_key"

    exc = IntegrityError("INSERT", {}, Orig("dup"))
    assert is_unique_violation(exc, "uq_media_classifications_idempotency_key")
    assert not is_unique_violation(exc, "uq_listing_visual_evidence_idempotency_key")


def test_is_unique_violation_matches_message_fallback() -> None:
    class Orig(Exception):
        pass

    orig = Orig(
        'duplicate key value violates unique constraint '
        '"uq_listing_visual_evidence_idempotency_key"'
    )
    exc = IntegrityError("INSERT", {}, orig)
    assert is_unique_violation(exc, "uq_listing_visual_evidence_idempotency_key")


@pytest.mark.asyncio
async def test_insert_or_get_on_unique_recovers_expected_conflict() -> None:
    session = _session_with_nested()
    existing = SimpleNamespace(id=9)

    async def insert():
        class Orig(Exception):
            constraint_name = "uq_media_classifications_idempotency_key"

        raise IntegrityError("INSERT", {}, Orig("dup"))

    async def fetch():
        return existing

    got = await insert_or_get_on_unique(
        session,
        insert=insert,
        fetch_existing=fetch,
        constraint_names=("uq_media_classifications_idempotency_key",),
        reused_log="reused %s",
        reused_log_args=("k",),
    )
    assert got is existing


@pytest.mark.asyncio
async def test_insert_or_get_on_unique_rethrows_unrelated_integrity() -> None:
    session = _session_with_nested()

    async def insert():
        class Orig(Exception):
            constraint_name = "some_other_constraint"

        raise IntegrityError("INSERT", {}, Orig("other"))

    with pytest.raises(IntegrityError):
        await insert_or_get_on_unique(
            session,
            insert=insert,
            fetch_existing=AsyncMock(return_value=SimpleNamespace(id=1)),
            constraint_names=("uq_media_classifications_idempotency_key",),
            reused_log="reused",
        )


@pytest.mark.asyncio
async def test_classification_ensure_recovers_idempotency_race() -> None:
    settings = Settings(MEDIA_AI_CLASSIFICATION_ENABLED=True)
    session = _session_with_nested()
    svc = MediaClassificationService(session, settings)
    listing = SimpleNamespace(id=1, owner_id=10, category_id=None)
    svc._listings.get_by_id = AsyncMock(return_value=listing)
    svc._media.list_by_listing = AsyncMock(
        return_value=[
            SimpleNamespace(id=100, order=0, is_placeholder=False, original_storage_key="a"),
            SimpleNamespace(id=101, order=1, is_placeholder=False, original_storage_key="b"),
        ]
    )
    fp = media_set_fingerprint([100, 101])
    existing = SimpleNamespace(
        id=42,
        status=MediaClassificationStatus.pending,
        media_set_fingerprint=fp,
        idempotency_key="k",
    )
    svc._repo = MagicMock()
    svc._repo.get_by_idempotency_key = AsyncMock(side_effect=[None, existing])
    svc._repo.get_latest_for_listing = AsyncMock(return_value=None)

    class Orig(Exception):
        constraint_name = "uq_media_classifications_idempotency_key"

    svc._repo.create = AsyncMock(
        side_effect=IntegrityError("INSERT", {}, Orig("dup")),
    )

    row = await svc.ensure_job_for_listing(1, actor_user_id=10)
    assert row is existing


@pytest.mark.asyncio
async def test_visual_evidence_ensure_recovers_idempotency_race() -> None:
    settings = Settings(MEDIA_VISUAL_EVIDENCE_ENABLED=True)
    session = _session_with_nested()
    svc = VisualEvidenceService(
        session, settings, provider=StubVisualEvidenceProvider()
    )
    listing = SimpleNamespace(id=1, owner_id=10, category_id=None)
    svc._listings.get_by_id = AsyncMock(return_value=listing)
    svc._media.list_by_listing = AsyncMock(
        return_value=[
            SimpleNamespace(id=100, order=0, is_placeholder=False, original_storage_key="a"),
        ]
    )
    existing = SimpleNamespace(
        id=7,
        status=VisualEvidenceStatus.pending,
        media_set_fingerprint=media_set_fingerprint([100]),
    )
    svc._repo = MagicMock()
    svc._repo.get_by_idempotency_key = AsyncMock(side_effect=[None, existing])
    svc._repo.get_latest_for_listing = AsyncMock(return_value=None)

    class Orig(Exception):
        constraint_name = "uq_listing_visual_evidence_idempotency_key"

    svc._repo.create = AsyncMock(
        side_effect=IntegrityError("INSERT", {}, Orig("dup")),
    )

    row = await svc.ensure_job_for_listing(1, actor_user_id=10)
    assert row is existing


@pytest.mark.asyncio
async def test_classification_ensure_rethrows_unrelated_integrity() -> None:
    settings = Settings(MEDIA_AI_CLASSIFICATION_ENABLED=True)
    session = _session_with_nested()
    svc = MediaClassificationService(session, settings)
    listing = SimpleNamespace(id=1, owner_id=10, category_id=None)
    svc._listings.get_by_id = AsyncMock(return_value=listing)
    svc._media.list_by_listing = AsyncMock(
        return_value=[
            SimpleNamespace(id=100, order=0, is_placeholder=False, original_storage_key="a"),
        ]
    )
    svc._repo = MagicMock()
    svc._repo.get_by_idempotency_key = AsyncMock(return_value=None)
    svc._repo.get_latest_for_listing = AsyncMock(return_value=None)

    class Orig(Exception):
        constraint_name = "media_classifications_pkey"

    svc._repo.create = AsyncMock(
        side_effect=IntegrityError("INSERT", {}, Orig("pk")),
    )

    with pytest.raises(IntegrityError):
        await svc.ensure_job_for_listing(1, actor_user_id=10)


async def _upload_n(
    client: AsyncClient,
    listing_id: int,
    n: int,
) -> list[int]:
    media_ids: list[int] = []
    colors = [
        (200, 40, 40),
        (40, 200, 40),
        (40, 40, 200),
        (200, 200, 40),
        (200, 40, 200),
        (40, 200, 200),
        (120, 80, 40),
        (80, 120, 200),
        (160, 160, 160),
        (30, 30, 30),
    ]
    for i in range(n):
        data = _jpeg_bytes(colors[i % len(colors)])
        # make sizes unique
        data = data + bytes([i & 0xFF]) * 8
        init = await client.post(
            f"/api/v1/listings/{listing_id}/media/uploads",
            json={
                "client_upload_id": str(uuid.uuid4()),
                "content_type": "image/jpeg",
                "content_length": len(data),
                "order": i,
            },
        )
        assert init.status_code == 201, init.text
        media_id = int(init.json()["media_id"])
        put = await client.put(
            f"/api/v1/listings/{listing_id}/media/{media_id}/upload",
            content=data,
            headers={"Content-Type": "image/jpeg"},
        )
        assert put.status_code == 204, put.text
        media_ids.append(media_id)
    return media_ids


async def _complete_all(client: AsyncClient, listing_id: int, media_ids: list[int]):
    async def one(mid: int):
        r = await client.post(f"/api/v1/listings/{listing_id}/media/{mid}/complete")
        return mid, r.status_code, r.text

    return await asyncio.gather(*[one(mid) for mid in media_ids])


async def _create_draft(client: AsyncClient) -> int:
    r = await client.post(
        "/api/v1/listings",
        json={"title": "concurrent complete probe", "price": 100},
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


async def _cleanup_listing(listing_id: int) -> None:
    async with async_session_maker() as session:
        await session.execute(
            text("DELETE FROM listings WHERE id = :id"),
            {"id": listing_id},
        )
        await session.commit()


async def _reset_db_engine() -> None:
    """Avoid cross-test asyncpg 'Event loop is closed' on shared pool."""
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_complete_2_photos_both_enabled() -> None:
    settings = get_settings()
    if not settings.MEDIA_DIRECT_UPLOAD_ENABLED:
        pytest.skip("direct upload disabled")
    assert settings.MEDIA_AI_CLASSIFICATION_ENABLED
    assert settings.MEDIA_VISUAL_EVIDENCE_ENABLED

    _auth_user()
    transport = ASGITransport(app=app)
    listing_id = None
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            listing_id = await _create_draft(client)
            media_ids = await _upload_n(client, listing_id, 2)
            results = await _complete_all(client, listing_id, media_ids)
            assert [(mid, st) for mid, st, _ in results] == [
                (media_ids[0], 200),
                (media_ids[1], 200),
            ], results

            async with async_session_maker() as session:
                media_rows = (
                    await session.execute(
                        text(
                            """
                            SELECT id, lifecycle_status FROM media
                            WHERE listing_id = :lid ORDER BY id
                            """
                        ),
                        {"lid": listing_id},
                    )
                ).all()
                assert len(media_rows) == 2
                assert all(r[1] != "uploading" for r in media_rows)

                clf_keys = (
                    await session.execute(
                        text(
                            """
                            SELECT idempotency_key, count(*)
                            FROM media_classifications
                            WHERE listing_id = :lid
                            GROUP BY idempotency_key
                            """
                        ),
                        {"lid": listing_id},
                    )
                ).all()
                assert clf_keys
                assert all(int(c) == 1 for _, c in clf_keys)

                ve_keys = (
                    await session.execute(
                        text(
                            """
                            SELECT idempotency_key, count(*)
                            FROM listing_visual_evidence
                            WHERE listing_id = :lid
                            GROUP BY idempotency_key
                            """
                        ),
                        {"lid": listing_id},
                    )
                ).all()
                assert ve_keys
                assert all(int(c) == 1 for _, c in ve_keys)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        if listing_id is not None:
            await _cleanup_listing(listing_id)
        await _reset_db_engine()


@pytest.mark.asyncio
async def test_concurrent_complete_4_photos_repeat() -> None:
    settings = get_settings()
    if not settings.MEDIA_DIRECT_UPLOAD_ENABLED:
        pytest.skip("direct upload disabled")

    _auth_user()
    listing_ids: list[int] = []
    try:
        for _ in range(3):
            await _reset_db_engine()
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                listing_id = await _create_draft(client)
                listing_ids.append(listing_id)
                media_ids = await _upload_n(client, listing_id, 4)
                results = await _complete_all(client, listing_id, media_ids)
                statuses = [st for _, st, _ in results]
                assert statuses == [200, 200, 200, 200], results

                order = await client.patch(
                    f"/api/v1/listings/{listing_id}/media/order",
                    json={"image_ids": media_ids},
                )
                assert order.status_code == 200, order.text

                async with async_session_maker() as session:
                    stuck = (
                        await session.execute(
                            text(
                                """
                                SELECT count(*) FROM media
                                WHERE listing_id = :lid
                                  AND lifecycle_status = 'uploading'
                                """
                            ),
                            {"lid": listing_id},
                        )
                    ).scalar_one()
                    assert int(stuck) == 0

                    clf_dup = (
                        await session.execute(
                            text(
                                """
                                SELECT max(cnt) FROM (
                                  SELECT count(*) AS cnt
                                  FROM media_classifications
                                  WHERE listing_id = :lid
                                  GROUP BY idempotency_key
                                ) t
                                """
                            ),
                            {"lid": listing_id},
                        )
                    ).scalar_one()
                    assert clf_dup is None or int(clf_dup) == 1

                    ve_dup = (
                        await session.execute(
                            text(
                                """
                                SELECT max(cnt) FROM (
                                  SELECT count(*) AS cnt
                                  FROM listing_visual_evidence
                                  WHERE listing_id = :lid
                                  GROUP BY idempotency_key
                                ) t
                                """
                            ),
                            {"lid": listing_id},
                        )
                    ).scalar_one()
                    assert ve_dup is None or int(ve_dup) == 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        for lid in listing_ids:
            await _cleanup_listing(lid)
        await _reset_db_engine()


@pytest.mark.asyncio
async def test_concurrent_complete_with_category_already_set() -> None:
    settings = get_settings()
    if not settings.MEDIA_DIRECT_UPLOAD_ENABLED:
        pytest.skip("direct upload disabled")

    await _reset_db_engine()
    _auth_user()
    transport = ASGITransport(app=app)
    listing_id = None
    try:
        async with async_session_maker() as session:
            cat_id = (
                await session.execute(
                    text(
                        """
                        SELECT id FROM categories
                        WHERE slug = 'transport-rental-legkovye-avtomobili'
                        LIMIT 1
                        """
                    )
                )
            ).scalar_one_or_none()
            if cat_id is None:
                pytest.skip("rental leaf missing")

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            listing_id = await _create_draft(client)
            patch = await client.patch(
                f"/api/v1/listings/{listing_id}",
                json={"category_id": int(cat_id)},
            )
            assert patch.status_code == 200, patch.text

            media_ids = await _upload_n(client, listing_id, 2)
            results = await _complete_all(client, listing_id, media_ids)
            assert all(st == 200 for _, st, _ in results), results

            async with async_session_maker() as session:
                statuses = (
                    await session.execute(
                        text(
                            """
                            SELECT lifecycle_status FROM media
                            WHERE listing_id = :lid ORDER BY id
                            """
                        ),
                        {"lid": listing_id},
                    )
                ).scalars().all()
                assert all(s != "uploading" for s in statuses)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        if listing_id is not None:
            await _cleanup_listing(listing_id)
        await _reset_db_engine()


@pytest.mark.asyncio
async def test_nine_photo_boundary_concurrent_complete() -> None:
    settings = get_settings()
    if not settings.MEDIA_DIRECT_UPLOAD_ENABLED:
        pytest.skip("direct upload disabled")

    await _reset_db_engine()
    _auth_user()
    transport = ASGITransport(app=app)
    listing_id = None
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            listing_id = await _create_draft(client)
            media_ids = await _upload_n(client, listing_id, 9)
            results = await _complete_all(client, listing_id, media_ids)
            assert [st for _, st, _ in results] == [200] * 9, results

            tenth = _jpeg_bytes((1, 2, 3)) + b"\x01" * 8
            bad = await client.post(
                f"/api/v1/listings/{listing_id}/media/uploads",
                json={
                    "client_upload_id": str(uuid.uuid4()),
                    "content_type": "image/jpeg",
                    "content_length": len(tenth),
                    "order": 8,
                },
            )
            # 10th image rejected by listing max=9 (or order slot conflict).
            assert bad.status_code in {400, 409}, bad.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        if listing_id is not None:
            await _cleanup_listing(listing_id)
        await _reset_db_engine()


@pytest.mark.asyncio
async def test_one_photo_complete_still_works() -> None:
    settings = get_settings()
    if not settings.MEDIA_DIRECT_UPLOAD_ENABLED:
        pytest.skip("direct upload disabled")

    await _reset_db_engine()
    _auth_user()
    transport = ASGITransport(app=app)
    listing_id = None
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            listing_id = await _create_draft(client)
            media_ids = await _upload_n(client, listing_id, 1)
            results = await _complete_all(client, listing_id, media_ids)
            assert results[0][1] == 200, results
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        if listing_id is not None:
            await _cleanup_listing(listing_id)
        await _reset_db_engine()
