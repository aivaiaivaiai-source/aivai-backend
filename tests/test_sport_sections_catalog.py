"""Sport goods stay out of clothes, transport, kids and business equipment."""
from app.seeds.sport_sections_catalog import SPORT_SECTIONS


def test_sport_sections_do_not_steal_other_catalogs() -> None:
    assert len(SPORT_SECTIONS) == 15
    seen: dict[str, str] = {}
    for catalog in SPORT_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        labels = [item["label"] for item in catalog["filters"]]
        assert labels[0] == "Продавец"
        assert "Регион" not in labels
        assert "Город" not in labels
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
    assert seen["Мячи"] == "Спортивные товары"
    assert seen["Беговые дорожки"] == "Фитнес и тренажёры"
    assert seen["Протеин"] == "Спортивное питание"
    assert seen["Комуз"] == "Кыргызские музык.ные инст.менты"
    assert seen["Шырдаки"] == "Шырдаки и изделия из войлока"
    assert seen["Сёдла"] == "Конный спорт и верховая езда"
    assert seen["Тогуз коргоол"] == "Настольные игры"
    assert [item["label"] for item in SPORT_SECTIONS["nutrition"]["filters"]] == ["Продавец"]
    assert "Состояние" in [item["label"] for item in SPORT_SECTIONS["sport"]["filters"]]
    banned = {
        "Велосипеды",
        "Детские велосипеды",
        "Детские самокаты",
        "Беговелы",
        "Санки и снегокаты",
        "Рюкзаки",
        "Перчатки",
        "Бутсы",
        "Кроссовки для бега",
        "Футбольная форма",
        "Спортивные костюмы",
        "Купальники",
        "Плавки",
        "Часы",
        "Бильярдные столы",
        "Игровые автоматы",
        "Тренажёры для залов",
        "Коммерческие батуты",
        "Игровые приставки",
        "Геймпады",
        "Игры",
        "Наушники",
        "Микрофоны",
        "Ноты",
        "Краски для рисования",
        "Холсты",
        "Пластилин",
        "Пряжа",
        "Нитки",
        "Ткани",
        "Лошади",
        "Кобылы",
        "Массажёры",
        "Витаминные комплексы",
        "Детские настольные игры",
        "Конструкторы",
        "Редкие книги",
        "Комиксы",
    }
    assert banned.isdisjoint(seen)
