"""plot_area is an exact decimal in сотках; Search is a numeric range."""
from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.real_estate_v2 import (
    HOUSES_SLUG,
    LAND_SLUG,
    RE_CORE_FIELDS_BY_SLUG,
    RE_SEARCH_FILTERS_BY_SLUG,
)


def _plot(slug: str):
    return next(f for f in RE_CORE_FIELDS_BY_SLUG[slug] if f[0] == "plot_area")


def test_land_and_house_plot_area_is_exact_decimal():
    for slug in (LAND_SLUG, HOUSES_SLUG):
        field = _plot(slug)
        assert field[1] == "Площадь участка"
        assert field[2] == CategoryFieldType.decimal
        assert field[3] is True
        assert field[5]["unit"] == "соток"
        assert field[5]["allow_decimal"] is True
        filt = next(f for f in RE_SEARCH_FILTERS_BY_SLUG[slug] if f[0] == "plot_area")
        assert filt[2] == CategoryFilterType.range
        assert filt[4]["unit"] == "соток"


def test_plot_area_is_not_an_enum_bucket():
    opts = _plot(LAND_SLUG)[5]
    assert "choices" not in opts
    assert "2_to_5" not in str(opts)
