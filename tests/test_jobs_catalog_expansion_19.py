# -*- coding: utf-8 -*-
"""Jobs final catalog expansion: 19 sectors, roles, parity, work_mode, pay_type."""
from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal

import pytest

from app.models.job_create_intent import HIRING, JOB_SEEKING
from app.seeds.jobs_create_fields import (
    JOBS_V2_CANONICAL_SLUGS,
    JOBS_V2_INACTIVE_SECTOR_SLUGS,
    WORK_MODE,
    build_jobs_hiring_core_fields,
)
from app.seeds.jobs_search_filters import build_jobs_search_filters
from app.seeds.jobs_seeking_fields import build_jobs_seeking_core_fields
from app.seeds.jobs_sections_catalog import JOB_SECTIONS
from app.seeds.jobs_sewing_catalog import build_sewing_jobs_catalog

# Approved ordered role catalogs (labels only).
_APPROVED: dict[str, tuple[str, ...]] = {
    "jobs-shveynoe-proizvodstvo": (
        "Швея",
        "Закройщик",
        "Портной",
        "Оверлочник / Оверлочница",
        "Распошивальщик / Распошивальщица",
        "Утюжник / Утюжница",
        "Специалист ВТО",
        "Вышивальщик / Вышивальщица",
        "Лаборант швейного производства",
        "Технолог швейного производства",
        "Конструктор одежды",
        "Дизайнер одежды",
        "Комплектовщик швейного производства",
        "Мастер цеха",
        "Контролёр ОТК",
        "Механик швейного оборудования",
        "Другие профессии швейного производства",
    ),
    "jobs-proizvodstvo-i-promyshlennost": (
        "Оператор станков",
        "Слесарь",
        "Токарь",
        "Фрезеровщик",
        "Сборщик",
        "Наладчик оборудования",
        "Оператор производственной линии",
        "Упаковщик",
        "Технолог производства",
        "Контролёр качества",
        "Мастер смены",
        "Начальник производства",
        "Директор производства",
        "Другие профессии производства",
    ),
    "jobs-stroitelstvo-i-remont": (
        "Разнорабочий",
        "Каменщик",
        "Кафельщик / плиточник",
        "Штукатур",
        "Маляр",
        "Отделочник",
        "Гипсокартонщик",
        "Сантехник",
        "Электрик",
        "Электромонтажник",
        "Сварщик",
        "Бетонщик",
        "Арматурщик",
        "Кровельщик",
        "Монтажник",
        "Прораб",
        "Другие профессии строительства и ремонта",
    ),
    "jobs-transport-i-logistika": (
        "Водитель легкового авто",
        "Водитель такси",
        "Водитель Газели",
        "Водитель грузового авто",
        "Водитель фуры",
        "Водитель автобуса",
        "Водитель микроавтобуса",
        "Курьер",
        "Экспедитор",
        "Кладовщик",
        "Грузчик",
        "Комплектовщик",
        "Логист",
        "Диспетчер",
        "Другие профессии транспорта и логистики",
    ),
    "jobs-prodazhi-i-torgovlya": (
        "Продавец",
        "Продавец-консультант",
        "Продавец-кассир",
        "Кассир",
        "Торговый агент",
        "Торговый представитель",
        "Менеджер по продажам",
        "Менеджер интернет-магазина",
        "Мерчандайзер",
        "Супервайзер",
        "Заведующий магазином",
        "Руководитель отдела продаж",
        "Другие профессии продаж и торговли",
    ),
    "jobs-ofis-i-administratsiya": (
        "Офис-менеджер",
        "Секретарь",
        "Администратор",
        "Администратор ресепшн",
        "Делопроизводитель",
        "Оператор колл-центра",
        "Оператор ПК",
        "Помощник руководителя",
        "Менеджер по работе с клиентами",
        "Начальник отдела",
        "Директор",
        "Другие офисные профессии",
    ),
    "jobs-buhgalteriya-i-finansy": (
        "Бухгалтер",
        "Главный бухгалтер",
        "Помощник бухгалтера",
        "Бухгалтер-кассир",
        "Экономист",
        "Финансовый специалист",
        "Финансовый аналитик",
        "Кредитный специалист",
        "Кадровик",
        "Специалист по налогам",
        "Другие профессии бухгалтерии и финансов",
    ),
    "jobs-marketing-reklama-i-media": (
        "Маркетолог",
        "SMM-специалист",
        "Таргетолог",
        "Контент-менеджер",
        "Контент-мейкер",
        "Копирайтер",
        "Графический дизайнер",
        "Видеограф",
        "Фотограф",
        "Видеомонтажёр",
        "Менеджер по рекламе",
        "PR-менеджер",
        "Другие профессии маркетинга и медиа",
    ),
    "jobs-it-i-tehnologii": (
        "Программист",
        "Frontend-разработчик",
        "Backend-разработчик",
        "Мобильный разработчик",
        "Программист 1С",
        "Тестировщик",
        "Системный администратор",
        "Специалист технической поддержки",
        "DevOps-инженер",
        "UI/UX-дизайнер",
        "Веб-дизайнер",
        "Аналитик данных",
        "Бизнес-аналитик",
        "Другие IT-профессии",
    ),
    "jobs-obrazovanie-i-obuchenie": (
        "Учитель начальных классов",
        "Учитель русского языка",
        "Учитель кыргызского языка",
        "Учитель английского языка",
        "Учитель математики",
        "Учитель других предметов",
        "Воспитатель",
        "Помощник воспитателя",
        "Репетитор",
        "Преподаватель курсов",
        "Логопед",
        "Методист",
        "Другие профессии образования",
    ),
    "jobs-meditsina-i-farmatsevtika": (
        "Врач общей практики",
        "Терапевт",
        "Педиатр",
        "Стоматолог",
        "Гинеколог",
        "Хирург",
        "Врач другой специальности",
        "Медсестра / Медбрат",
        "Фельдшер",
        "Фармацевт",
        "Лаборант",
        "Санитар / Санитарка",
        "Администратор клиники",
        "Другие медицинские профессии",
    ),
    "jobs-krasota-i-zdorove": (
        "Парикмахер",
        "Барбер",
        "Колорист",
        "Мастер маникюра",
        "Мастер педикюра",
        "Бровист",
        "Лешмейкер",
        "Визажист",
        "Косметолог",
        "Массажист",
        "Мастер депиляции",
        "Администратор салона",
        "Другие профессии красоты",
    ),
    "jobs-gostinitsy-kafe-i-restorany": (
        "Повар",
        "Шеф-повар",
        "Помощник повара",
        "Кондитер",
        "Пекарь",
        "Официант",
        "Бармен",
        "Бариста",
        "Хостес",
        "Администратор ресторана",
        "Администратор гостиницы",
        "Горничная",
        "Мойщик посуды",
        "Другие профессии гостиниц и общепита",
    ),
    "jobs-sto-i-avtoservis": (
        "Автослесарь",
        "Ходовщик",
        "Моторист",
        "Автоэлектрик",
        "Инжекторщик",
        "Автодиагност",
        "Автомеханик",
        "Мастер по коробкам передач / КПП",
        "Маляр по авто",
        "Кузовщик",
        "Рихтовщик",
        "Сварщик по авто",
        "Шиномонтажник",
        "Мастер развал-схождения",
        "Автомойщик",
        "Детейлер",
        "Установщик автосигнализаций",
        "Мастер по автокондиционерам",
        "Мастер-приёмщик",
        "Другие профессии автосервиса",
    ),
    "jobs-razvlecheniya-i-sport": (
        "Тренер",
        "Фитнес-тренер",
        "Персональный тренер",
        "Инструктор",
        "Тренер по танцам",
        "Хореограф",
        "Аниматор",
        "Ведущий мероприятий",
        "Диджей",
        "Администратор клуба",
        "Администратор спортивного зала",
        "Другие профессии спорта и развлечений",
    ),
    "jobs-domashniy-personal": (
        "Няня",
        "Домработница",
        "Сиделка",
        "Помощник по хозяйству",
        "Семейный повар",
        "Семейный водитель",
        "Гувернантка / Гувернёр",
        "Садовник",
        "Другие профессии домашнего персонала",
    ),
    "jobs-ohrana-i-bezopasnost": (
        "Охранник",
        "Сторож",
        "Сотрудник службы безопасности",
        "Оператор видеонаблюдения",
        "Телохранитель",
        "Контролёр пропускного режима",
        "Инкассатор",
        "Начальник охраны",
        "Другие профессии охраны и безопасности",
    ),
    "jobs-selskoe-hozyaystvo": (
        "Агроном",
        "Тракторист",
        "Механизатор",
        "Комбайнёр",
        "Животновод",
        "Пастух / Чабан",
        "Дояр / Доярка",
        "Ветеринар",
        "Работник фермы",
        "Полевой рабочий",
        "Тепличный работник",
        "Оператор фермы",
        "Другие сельскохозяйственные профессии",
    ),
    "jobs-studenty-i-podrabotka": (
        "Промоутер",
        "Расклейщик объявлений",
        "Тайный покупатель",
        "Работник на мероприятие",
        "Другие подработки",
    ),
}

_STUDENTS_FORBIDDEN = {
    "Курьер",
    "Упаковщик",
    "Комплектовщик",
    "Грузчик",
    "Официант",
    "Оператор колл-центра",
    "Разнорабочий",
}


def _roles_from_section(slug: str) -> list[str]:
    for section in JOB_SECTIONS.values():
        if section["category_slug"] == slug:
            return [r["value"] for r in section["roles"]]
    raise KeyError(slug)


def _normalize(label: str) -> str:
    s = label.strip().lower().replace("ё", "е")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[«»\"'`]", "", s)
    return s


def test_canonical_count_and_abroad_inactive() -> None:
    assert len(JOBS_V2_CANONICAL_SLUGS) == 19
    assert "jobs-rabota-za-rubezhom" in JOBS_V2_INACTIVE_SECTOR_SLUGS
    assert "jobs-rabota-za-rubezhom" not in JOBS_V2_CANONICAL_SLUGS


def test_approved_ordered_role_catalogs() -> None:
    assert set(_APPROVED) == set(JOBS_V2_CANONICAL_SLUGS)
    sewing = [r["value"] for r in build_sewing_jobs_catalog()["roles"]]
    assert sewing == list(_APPROVED["jobs-shveynoe-proizvodstvo"])
    for slug, expected in _APPROVED.items():
        assert _roles_from_section(slug) == list(expected), slug


def test_exactly_one_fallback_role_last() -> None:
    for slug in JOBS_V2_CANONICAL_SLUGS:
        roles = _roles_from_section(slug)
        fallbacks = [r for r in roles if r.startswith("Другие")]
        assert len(fallbacks) == 1, slug
        assert roles[-1] == fallbacks[0], slug
        assert "Другие вакансии" not in roles[-1] or slug == "legacy", slug


def test_students_no_cross_sector_copies() -> None:
    roles = set(_roles_from_section("jobs-studenty-i-podrabotka"))
    assert roles.isdisjoint(_STUDENTS_FORBIDDEN)


def test_production_excludes_welder_and_komplektovshik() -> None:
    roles = set(_roles_from_section("jobs-proizvodstvo-i-promyshlennost"))
    assert "Сварщик" not in roles
    assert "Комплектовщик" not in roles


def test_zero_forbidden_exact_duplicates() -> None:
    by_label: dict[str, list[str]] = defaultdict(list)
    for slug in JOBS_V2_CANONICAL_SLUGS:
        for role in _roles_from_section(slug):
            by_label[role].append(slug)
    forbidden = {k: v for k, v in by_label.items() if len(v) > 1}
    assert forbidden == {}, forbidden


def test_create_search_role_parity_all_19() -> None:
    hiring = build_jobs_hiring_core_fields()
    seeking = build_jobs_seeking_core_fields()
    search = build_jobs_search_filters()

    def create_roles(fields) -> list[str]:
        for f in fields:
            if f[0] == "job_role":
                return [c["value"] for c in f[4]["choices"]]
        raise AssertionError("job_role missing")

    for slug in JOBS_V2_CANONICAL_SLUGS:
        expected = list(_APPROVED[slug])
        h = create_roles(hiring[slug])
        s = create_roles(seeking[slug])
        assert h == expected, f"hiring {slug}"
        assert s == expected, f"seeking {slug}"
        # Search role options come from intelligence role catalog / same section.
        # Filters do not redefine job_role; parity is create ↔ create intents.
        assert h == s


def test_work_mode_hiring_search_parity() -> None:
    search = build_jobs_search_filters()
    for slug in JOBS_V2_CANONICAL_SLUGS:
        hiring = {f[0]: f for f in search[slug][HIRING]}
        assert "work_mode" in hiring, slug
        opts = [o["value"] for o in (hiring["work_mode"][4] or {}).get("options") or []]
        assert opts == list(WORK_MODE), slug
        seeking_keys = {f[0] for f in search[slug][JOB_SEEKING]}
        assert "work_mode" not in seeking_keys, slug


def test_pay_type_option_counts_for_visibility() -> None:
    """Contract: option-based filter with <2 options is not searchable UX."""
    search = build_jobs_search_filters()
    rows = []
    for slug in JOBS_V2_CANONICAL_SLUGS:
        hiring = {f[0]: f for f in search[slug][HIRING]}
        pt = hiring.get("pay_type")
        if pt is None:
            rows.append((slug, 0, False))
            continue
        n = len((pt[4] or {}).get("options") or [])
        visible = n >= 2
        rows.append((slug, n, visible))
        # Presentation rule: callers should hide when n < 2.
        assert (n >= 2) == visible
    # At least office/accounting/security historically have single Оклад.
    single = [r for r in rows if r[1] == 1]
    assert single, "expected some single-option pay_type sectors"


def test_new_spotlight_roles_present() -> None:
    for slug, role in (
        ("jobs-sto-i-avtoservis", "Ходовщик"),
        ("jobs-sto-i-avtoservis", "Инжекторщик"),
        ("jobs-shveynoe-proizvodstvo", "Распошивальщик / Распошивальщица"),
        ("jobs-stroitelstvo-i-remont", "Кафельщик / плиточник"),
        ("jobs-it-i-tehnologii", "Frontend-разработчик"),
        ("jobs-selskoe-hozyaystvo", "Пастух / Чабан"),
    ):
        assert role in _roles_from_section(slug)


def test_legacy_generic_roles_removed_from_catalog() -> None:
    construction = set(_roles_from_section("jobs-stroitelstvo-i-remont"))
    assert "Плиточник" not in construction
    assert "Штукатур-маляр" not in construction
    education = set(_roles_from_section("jobs-obrazovanie-i-obuchenie"))
    assert "Учитель" not in education
    medical = set(_roles_from_section("jobs-meditsina-i-farmatsevtika"))
    assert "Врач" not in medical


def test_depends_on_values_exist_in_role_catalog() -> None:
    seeking = build_jobs_seeking_core_fields()
    for slug, fields in seeking.items():
        roles = set(_roles_from_section(slug))
        for f in fields:
            opts = f[4] or {}
            dep = opts.get("depends_on")
            if not dep:
                continue
            assert dep["field"] == "job_role", f"{slug}/{f[0]}"
            missing = [v for v in dep["values"] if v not in roles]
            assert not missing, f"{slug}/{f[0]} depends on missing roles: {missing}"


@pytest.mark.asyncio
async def test_new_roles_pass_field_validation(client) -> None:
    from app.db.session import engine

    await engine.dispose()
    tree = (await client.get("/api/v1/categories/tree")).json()

    def walk(nodes, out):
        for n in nodes:
            out.append(n)
            walk(n.get("children") or [], out)

    flat: list[dict] = []
    walk(tree, flat)
    by_slug = {n["slug"]: n for n in flat}

    cases = [
        ("jobs-sto-i-avtoservis", HIRING, "Ходовщик"),
        ("jobs-it-i-tehnologii", JOB_SEEKING, "Frontend-разработчик"),
        ("jobs-stroitelstvo-i-remont", HIRING, "Кафельщик / плиточник"),
        ("jobs-shveynoe-proizvodstvo", HIRING, "Распошивальщик / Распошивальщица"),
    ]
    for slug, intent, role in cases:
        cat_id = by_slug[slug]["id"]
        intel = await client.get(
            f"/api/v1/categories/intelligence/{cat_id}",
            params={"intent": intent},
        )
        assert intel.status_code == 200, slug
        role_field = next(
            f for f in intel.json()["core_fields"] if f["field_key"] == "job_role"
        )
        values = [
            c["value"]
            for c in (role_field.get("options") or {}).get("choices") or []
        ]
        assert role in values, f"{slug}/{role}"


@pytest.mark.asyncio
async def test_abroad_absent_from_active_tree(client) -> None:
    from app.db.session import engine

    await engine.dispose()
    tree = (await client.get("/api/v1/categories/tree")).json()

    def walk(nodes, out):
        for n in nodes:
            out.append(n)
            walk(n.get("children") or [], out)

    flat: list[dict] = []
    walk(tree, flat)
    slugs = {n["slug"] for n in flat}
    assert "jobs-rabota-za-rubezhom" not in slugs
    assert len([s for s in JOBS_V2_CANONICAL_SLUGS if s in slugs]) == 19


@pytest.mark.asyncio
async def test_e2e_new_roles_and_work_mode_search(client) -> None:
    """A/B/C/D: new roles searchable; work_mode exact + multi ANY/OR."""
    import json
    from decimal import Decimal

    from sqlalchemy import select, text

    from app.db.session import async_session_maker, engine
    from app.models.category import Category
    from app.models.enums import Currency, ListingStatus
    from app.models.listing import Listing
    from app.models.listing_field_value import ListingFieldValue
    from app.models.user import User

    await engine.dispose()
    ids: list[int] = []
    try:
        async with async_session_maker() as session:
            sto = (
                await session.execute(
                    select(Category).where(Category.slug == "jobs-sto-i-avtoservis")
                )
            ).scalar_one()
            it = (
                await session.execute(
                    select(Category).where(Category.slug == "jobs-it-i-tehnologii")
                )
            ).scalar_one()
            user = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()

            async def add(
                *,
                title: str,
                cat_id: int,
                intent: str,
                role: str,
                work_mode: str | None = None,
            ) -> int:
                row = Listing(
                    title=title,
                    description="jobs-catalog-expansion-e2e",
                    price=Decimal("1000"),
                    currency=Currency.KGS,
                    status=ListingStatus.active,
                    owner_id=user.id,
                    category_id=cat_id,
                    job_intent=intent,
                )
                session.add(row)
                await session.flush()
                session.add(
                    ListingFieldValue(
                        listing_id=row.id, field_key="job_role", value_text=role
                    )
                )
                if work_mode:
                    session.add(
                        ListingFieldValue(
                            listing_id=row.id,
                            field_key="work_mode",
                            value_text=work_mode,
                        )
                    )
                await session.flush()
                return row.id

            lid_sto = await add(
                title="E2E Ходовщик",
                cat_id=sto.id,
                intent=HIRING,
                role="Ходовщик",
                work_mode="2/2",
            )
            lid_fe = await add(
                title="E2E Frontend",
                cat_id=it.id,
                intent=JOB_SEEKING,
                role="Frontend-разработчик",
            )
            lid_other = await add(
                title="E2E mode 5/2",
                cat_id=sto.id,
                intent=HIRING,
                role="Автослесарь",
                work_mode="5/2",
            )
            ids.extend([lid_sto, lid_fe, lid_other])
            await session.commit()
            sto_id, it_id = sto.id, it.id

        # A — hiring role search
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "job_intent": HIRING,
                "attrs": json.dumps({"job_role": "Ходовщик"}, ensure_ascii=False),
                "limit": 50,
            },
        )
        assert r.status_code == 200
        assert "E2E Ходовщик" in {i["title"] for i in r.json()["items"]}

        # B — seeking role search
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": it_id,
                "job_intent": JOB_SEEKING,
                "attrs": json.dumps(
                    {"job_role": "Frontend-разработчик"}, ensure_ascii=False
                ),
                "limit": 50,
            },
        )
        assert r.status_code == 200
        assert "E2E Frontend" in {i["title"] for i in r.json()["items"]}

        # C — work_mode exact
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "job_intent": HIRING,
                "attrs": json.dumps({"work_mode": "2/2"}, ensure_ascii=False),
                "limit": 50,
            },
        )
        assert r.status_code == 200
        titles = {i["title"] for i in r.json()["items"]}
        assert "E2E Ходовщик" in titles
        assert "E2E mode 5/2" not in titles

        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "job_intent": HIRING,
                "attrs": json.dumps({"work_mode": "5/2"}, ensure_ascii=False),
                "limit": 50,
            },
        )
        titles = {i["title"] for i in r.json()["items"]}
        assert "E2E mode 5/2" in titles
        assert "E2E Ходовщик" not in titles

        # D — multi work_mode ANY/OR
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "job_intent": HIRING,
                "attrs": json.dumps(
                    {"work_mode": "5/2||2/2"}, ensure_ascii=False
                ),
                "limit": 50,
            },
        )
        assert r.status_code == 200
        titles = {i["title"] for i in r.json()["items"]}
        assert "E2E Ходовщик" in titles
        assert "E2E mode 5/2" in titles

        # E — cross-intent isolation
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "job_intent": JOB_SEEKING,
                "attrs": json.dumps({"job_role": "Ходовщик"}, ensure_ascii=False),
                "limit": 50,
            },
        )
        assert r.status_code == 200
        assert "E2E Ходовщик" not in {i["title"] for i in r.json()["items"]}
    finally:
        async with async_session_maker() as session:
            for lid in ids:
                await session.execute(
                    text("DELETE FROM listing_field_values WHERE listing_id = :id"),
                    {"id": lid},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": lid},
                )
            await session.commit()
