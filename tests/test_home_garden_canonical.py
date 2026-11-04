"""Home & garden L2 canonicalization smoke."""
from __future__ import annotations

from app.seeds.home_garden_canonical import (
    HOME_GARDEN_CARPETS_SLUG,
    HOME_GARDEN_DECOR_SLUG,
    HOME_GARDEN_FURNITURE_SLUG,
    RETIRED_HOME_GARDEN_LEGACY_SLUGS,
)
from app.seeds.mobile_category_skeleton import MOBILE_CATEGORY_SKELETON


def test_home_garden_legacy_not_in_skeleton() -> None:
    slugs = {row[1] for row in MOBILE_CATEGORY_SKELETON if row[0] == "home-garden"}
    assert RETIRED_HOME_GARDEN_LEGACY_SLUGS.isdisjoint(slugs)


def test_home_garden_unified_furniture_carpets_decor() -> None:
    by_slug = {
        row[1]: row[2]
        for row in MOBILE_CATEGORY_SKELETON
        if row[0] == "home-garden"
    }
    assert by_slug[HOME_GARDEN_FURNITURE_SLUG] == "Мебель"
    assert by_slug[HOME_GARDEN_CARPETS_SLUG] == "Ковры"
    assert by_slug[HOME_GARDEN_DECOR_SLUG] == "Декор и интерьер"
    assert "home-garden-sadovyy-dekor" not in by_slug
    assert "home-garden-prazdnichnyy-i-sezonnyy-dekor" not in by_slug
    assert "home-garden-osveschenie-i-elektrika-dlya-doma" not in by_slug
    assert not any("садовый декор" in name.lower() for name in by_slug.values())
    assert not any("праздничн" in name.lower() for name in by_slug.values())
    assert len(by_slug) == 28
    assert by_slug["home-garden-basseyny-i-tovary-dlya-otdyha"] == "Бассейны и аксессуары"
    assert by_slug["home-garden-sadovye-kacheli-i-gamaki"] == "Садовые качели и гамаки"


def test_home_garden_flutter_label_count_matches_skeleton() -> None:
    """Flutter labels must cover every skeleton display name (checked locally)."""
    from pathlib import Path

    candidates = [
        Path(__file__).resolve().parents[2].parent
        / "aivai_mobile"
        / "lib"
        / "features"
        / "home"
        / "data"
        / "home_garden_subcategories_data.dart",
        Path("/host/aivai_mobile/lib/features/home/data/home_garden_subcategories_data.dart"),
    ]
    dart = next((p for p in candidates if p.exists()), None)
    if dart is None:
        return
    text = dart.read_text(encoding="utf-8")
    skeleton_names = {
        row[2] for row in MOBILE_CATEGORY_SKELETON if row[0] == "home-garden"
    }
    for name in skeleton_names:
        assert f"'{name}'" in text or f'"{name}"' in text, name
