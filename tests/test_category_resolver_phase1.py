"""Substage 3C-3 — Category Resolver foundation tests."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.category_resolver.catalog_snapshot import ResolverCatalogSnapshot, ResolverCategoryNode
from app.category_resolver.engine import CategoryResolverEngine
from app.category_resolver.intent_semantics import IntentAction, interpret_intent
from app.category_resolver.visual_signals import detect_intent_visual_conflict
from app.core.config import Settings
from app.models.category_resolver_enums import CategoryResolverStatus
from app.models.enums import ListingStatus
from app.models.listing_user_intent_enums import ListingUserIntentStatus
from app.schemas.category_intelligence import CategoryRoutingResult
from app.services.category_resolver_service import CategoryResolverService
from app.seeds.transport_canonical import RETIRED_TRANSPORT_SLUGS
from app.user_intent.fingerprint import hybrid_resolver_input_fingerprint


def _node(
    slug: str,
    *,
    node_id: int,
    name: str,
    parent_id: int | None = None,
    parent_slug: str | None = None,
    depth: int = 1,
    path_slugs: tuple[str, ...] | None = None,
) -> ResolverCategoryNode:
    ps = path_slugs or ((parent_slug, slug) if parent_slug else (slug,))
    names = tuple(s.replace("-", " ").title() for s in ps)
    return ResolverCategoryNode(
        id=node_id,
        slug=slug,
        name=name,
        parent_id=parent_id,
        parent_slug=parent_slug,
        depth=depth,
        path_slugs=ps,
        path_names=names,
        entity_type="object",
        is_active=True,
        routable=True,
        schema_ready=False,
        filter_ready=False,
    )


def _catalog() -> ResolverCatalogSnapshot:
    nodes = {
        "transport": _node("transport", node_id=605, name="Транспорт", depth=0, path_slugs=("transport",)),
        "transport-car-sale": _node(
            "transport-car-sale",
            node_id=681,
            name="Продажа авто",
            parent_id=605,
            parent_slug="transport",
            depth=1,
            path_slugs=("transport", "transport-car-sale"),
        ),
        "transport-cargo": _node(
            "transport-cargo",
            node_id=691,
            name="Грузовой транспорт",
            parent_id=605,
            parent_slug="transport",
            depth=1,
            path_slugs=("transport", "transport-cargo"),
        ),
        "transport-auto-parts": _node(
            "transport-auto-parts",
            node_id=682,
            name="Автозапчасти",
            parent_id=605,
            parent_slug="transport",
            depth=1,
            path_slugs=("transport", "transport-auto-parts"),
        ),
        "services": _node("services", node_id=614, name="Услуги", depth=0, path_slugs=("services",)),
        "services-gruzoperevozki-i-pereezdy": _node(
            "services-gruzoperevozki-i-pereezdy",
            node_id=700,
            name="Грузоперевозки и переезды",
            parent_id=614,
            parent_slug="services",
            depth=1,
            path_slugs=("services", "services-gruzoperevozki-i-pereezdy"),
        ),
        "services-uslugi-spetstehniki": _node(
            "services-uslugi-spetstehniki",
            node_id=701,
            name="Услуги спецтехники",
            parent_id=614,
            parent_slug="services",
            depth=1,
            path_slugs=("services", "services-uslugi-spetstehniki"),
        ),
        "services-santehnika": _node(
            "services-santehnika",
            node_id=702,
            name="Сантехника",
            parent_id=614,
            parent_slug="services",
            depth=1,
            path_slugs=("services", "services-santehnika"),
        ),
        "jobs": _node("jobs", node_id=612, name="Работа", depth=0, path_slugs=("jobs",)),
        "jobs-resume": _node(
            "jobs-resume",
            node_id=720,
            name="Резюме",
            parent_id=612,
            parent_slug="jobs",
            depth=1,
            path_slugs=("jobs", "jobs-resume"),
        ),
        "jobs-vacancies": _node(
            "jobs-vacancies",
            node_id=721,
            name="Вакансии",
            parent_id=612,
            parent_slug="jobs",
            depth=1,
            path_slugs=("jobs", "jobs-vacancies"),
        ),
    }
    by_id = {n.id: n for n in nodes.values()}
    children: dict[int, list[int]] = {}
    for n in nodes.values():
        if n.parent_id is not None:
            children.setdefault(n.parent_id, []).append(n.id)
    return ResolverCatalogSnapshot(
        version_hash="test-catalog-hash",
        locale="ru",
        nodes_by_slug=nodes,
        nodes_by_id=by_id,
        children_by_parent_id=children,
        intelligence=None,
    )


def _routing_mock(target_slug: str | None, confidence: float = 0.86) -> MagicMock:
    routing = MagicMock()
    if target_slug:
        routing.route = AsyncMock(
            return_value=CategoryRoutingResult(
                category_id=681,
                category_slug=target_slug,
                category_name=target_slug,
                parent_slug="transport",
                confidence=confidence,
                mode="heuristic",
                reason="test",
            )
        )
    else:
        routing.route = AsyncMock(
            return_value=CategoryRoutingResult(mode="suggestion", confidence=0.2, reason="none")
        )
    return routing


def test_resolver_feature_flags_default_off() -> None:
    assert Settings.model_fields["CATEGORY_RESOLVER_ENABLED"].default is False
    assert Settings.model_fields["CATEGORY_RESOLVER_AUTO_ASSIGN_ENABLED"].default is False


def test_intent_semantics_sell_kamaz() -> None:
    sem = interpret_intent("Продам КамАЗ")
    assert sem.action == IntentAction.SELL
    assert "камаз" in sem.subject_terms


def test_intent_semantics_service_transport() -> None:
    sem = interpret_intent("Предлагаю грузоперевозки")
    assert sem.action == IntentAction.SERVICE_OFFER


def test_intent_semantics_job_seek() -> None:
    sem = interpret_intent("Ищу работу водителем")
    assert sem.action == IntentAction.JOB_SEEK


def test_intent_semantics_hire() -> None:
    sem = interpret_intent("Нужен водитель")
    assert sem.action == IntentAction.HIRE


def test_visual_conflict_parts_vs_car() -> None:
    sem = interpret_intent("Продаю запчасти Toyota")
    assert detect_intent_visual_conflict(sem, ("PASSENGER_CAR",))


def test_fingerprint_includes_catalog_hash() -> None:
    a = hybrid_resolver_input_fingerprint(
        media_set_fingerprint="m1",
        intent_fingerprint="i1",
        catalog_snapshot_hash="c1",
        resolver_version="category-resolver-v1",
    )
    b = hybrid_resolver_input_fingerprint(
        media_set_fingerprint="m1",
        intent_fingerprint="i1",
        catalog_snapshot_hash="c2",
        resolver_version="category-resolver-v1",
    )
    assert a != b


@pytest.mark.asyncio
async def test_engine_kamaz_sale_suggests_cargo() -> None:
    engine = CategoryResolverEngine(_routing_mock("transport-cargo"))
    out = await engine.resolve(
        raw_intent_text="Продам КамАЗ",
        catalog=_catalog(),
        visual_concepts=("TRUCK",),
    )
    assert out.status == CategoryResolverStatus.suggested
    assert out.suggested_slug == "transport-cargo"
    assert out.suggested_category_id == 691


@pytest.mark.asyncio
async def test_engine_service_transport_not_cargo_sale() -> None:
    engine = CategoryResolverEngine(
        _routing_mock("services-gruzoperevozki-i-pereezdy")
    )
    out = await engine.resolve(
        raw_intent_text="Предлагаю грузоперевозки",
        catalog=_catalog(),
        visual_concepts=("TRUCK",),
    )
    assert out.suggested_slug == "services-gruzoperevozki-i-pereezdy"


@pytest.mark.asyncio
async def test_engine_parts_beats_passenger_car_visual() -> None:
    engine = CategoryResolverEngine(_routing_mock("transport-car-sale", confidence=0.86))
    out = await engine.resolve(
        raw_intent_text="Продаю запчасти Toyota",
        catalog=_catalog(),
        visual_concepts=("PASSENGER_CAR",),
    )
    assert out.suggested_slug == "transport-auto-parts"
    assert out.evidence_summary.get("conflict") == "intent_visual_mismatch"


@pytest.mark.asyncio
async def test_engine_santehnika_service() -> None:
    engine = CategoryResolverEngine(_routing_mock(None))
    out = await engine.resolve(
        raw_intent_text="Услуги сантехника",
        catalog=_catalog(),
        visual_concepts=(),
    )
    assert out.suggested_slug == "services-santehnika"


@pytest.mark.asyncio
async def test_engine_job_seek() -> None:
    engine = CategoryResolverEngine(_routing_mock("jobs-vacancies"))
    out = await engine.resolve(
        raw_intent_text="Ищу работу водителем",
        catalog=_catalog(),
        visual_concepts=("PERSON",),
    )
    assert out.suggested_slug in ("jobs-resume", "jobs-rezyume-soiskateley")
    assert out.intent_semantics["action"] == "JOB_SEEK"


@pytest.mark.asyncio
async def test_engine_hire_not_job_seek() -> None:
    engine = CategoryResolverEngine(_routing_mock("jobs-vacancies"))
    out = await engine.resolve(
        raw_intent_text="Нужен водитель",
        catalog=_catalog(),
        visual_concepts=(),
    )
    assert out.intent_semantics["action"] == "HIRE"
    assert out.suggested_slug in ("jobs-vacancies", "jobs-vakansii-bez-opyta")


@pytest.mark.asyncio
async def test_engine_service_vs_sell_truck() -> None:
    engine = CategoryResolverEngine(_routing_mock("transport-cargo"))
    out = await engine.resolve(
        raw_intent_text="Предлагаю грузоперевозки",
        catalog=_catalog(),
        visual_concepts=("TRUCK",),
    )
    assert out.suggested_slug == "services-gruzoperevozki-i-pereezdy"


@pytest.mark.asyncio
async def test_engine_parts_over_visual_car() -> None:
    engine = CategoryResolverEngine(_routing_mock("transport-car-sale"))
    out = await engine.resolve(
        raw_intent_text="Продам двигатель Toyota",
        catalog=_catalog(),
        visual_concepts=("PASSENGER_CAR",),
    )
    assert out.suggested_slug in (
        "transport-auto-parts-dvigatel-i-navesnoe",
        "transport-auto-parts",
    )
    assert out.evidence_summary.get("conflict") == "intent_visual_mismatch"


@pytest.mark.asyncio
async def test_engine_never_suggests_retired_transport() -> None:
    engine = CategoryResolverEngine(_routing_mock("transport-cars"))
    catalog = _catalog()
    assert "transport-cars" not in catalog.nodes_by_slug
    out = await engine.resolve(
        raw_intent_text="Продам машину",
        catalog=catalog,
        visual_concepts=("PASSENGER_CAR",),
    )
    if out.suggested_slug:
        assert out.suggested_slug not in RETIRED_TRANSPORT_SLUGS


@pytest.mark.asyncio
async def test_service_shadow_does_not_assign_category() -> None:
    session = AsyncMock()
    session.commit = AsyncMock()
    settings = Settings(
        CATEGORY_RESOLVER_ENABLED=True,
        CATEGORY_RESOLVER_AUTO_ASSIGN_ENABLED=False,
    )
    service = CategoryResolverService(session, settings=settings)

    listing = SimpleNamespace(id=10, owner_id=5, category_id=None, status=ListingStatus.draft)
    intent = SimpleNamespace(
        raw_intent_text="Продам КамАЗ",
        intent_status=ListingUserIntentStatus.provided,
        intent_fingerprint="abc",
        intent_version=1,
    )

    service._listings.get_by_id = AsyncMock(return_value=listing)
    service._intents.get_by_listing_id = AsyncMock(return_value=intent)
    service._current_media_fingerprint = AsyncMock(return_value="media-fp")
    service._load_visual_evidence = AsyncMock(return_value=(None, ("TRUCK",)))
    service._resolver_repo.get_by_idempotency_key = AsyncMock(return_value=None)
    service._resolver_repo.get_latest_for_listing = AsyncMock(return_value=None)

    created_row = SimpleNamespace(
        listing_id=10,
        status=CategoryResolverStatus.suggested,
        suggested_category_id=691,
        suggested_slug="transport-cargo",
        confidence=0.9,
        needs_confirmation=True,
        candidate_path_json=[],
        alternatives_json=[],
        evidence_summary_json={},
        intent_semantics_json={},
        input_fingerprint="fp",
        catalog_snapshot_hash="hash",
        resolver_version="category-resolver-v1",
        updated_at=datetime.now(UTC),
    )
    service._resolver_repo.create = AsyncMock(return_value=created_row)

    mock_catalog = _catalog()
    mock_output = SimpleNamespace(
        status=CategoryResolverStatus.suggested,
        suggested_category_id=691,
        suggested_slug="transport-cargo",
        confidence=0.9,
        needs_confirmation=True,
        candidate_path=[],
        alternatives=[],
        evidence_summary={},
        intent_semantics={},
    )

    with patch.object(service, "_build_catalog_snapshot", AsyncMock(return_value=mock_catalog)):
        with patch(
            "app.services.category_resolver_service.CategoryResolverEngine"
        ) as engine_cls:
            engine_cls.return_value.resolve = AsyncMock(return_value=mock_output)
            resp = await service.resolve_for_listing(10, actor_user_id=5)

    assert resp.result.suggested_slug == "transport-cargo"
    assert listing.category_id is None
    session.commit.assert_awaited_once()
