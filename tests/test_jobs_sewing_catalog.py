"""Sewing jobs are vacancies, not garment types or services."""
from app.seeds.jobs_sewing_catalog import build_sewing_jobs_catalog


def test_sewing_jobs_are_vacancies() -> None:
    catalog = build_sewing_jobs_catalog()
    roles = [item["label"] for item in catalog["roles"]]
    filters = {item["label"]: [opt["label"] for opt in item["options"]] for item in catalog["filters"]}
    assert catalog["category_slug"] == "jobs-shveynoe-proizvodstvo"
    assert roles[0] == "Швея"
    assert roles[-1] == "Другие профессии швейного производства"
    assert "Закройщик" in roles
    assert "Технолог швейного производства" in roles
    for banned in (
        "Юбка",
        "Платье",
        "Прямострочка",
        "Оверлок",
        "Ателье",
        "Бухгалтер",
        "Водитель",
        "Охрана",
        "Частный мастер",
    ):
        assert banned not in roles
    assert filters["Работодатель"][-1] == "Другой"
    assert filters["Формат"] == ["В цехе", "На дому"]
    assert "Сдельная" in filters["Оплата"]
    assert "Без опыта" in filters["Опыт"]
