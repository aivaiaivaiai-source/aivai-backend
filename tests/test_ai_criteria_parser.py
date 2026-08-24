from app.core.ai_search_criteria import (
    AiSearchCriteria,
    normalize_brand,
    normalize_engine_volume,
    normalize_model,
)
from app.services.ai_criteria_parser import parse_criteria


def test_parse_auto_brand_city_price_normalized():
    data = parse_criteria(
        "Ищу Toyota Camry в Бишкеке до 800000 сом 2018",
        agent_type="ai_auto",
    )
    assert data["brand"] == "toyota"
    assert data["model"] == "camry"
    assert data["city"] == "Бишкек"
    assert data["max_price"] == 800000
    assert data["year_min"] == 2018
    assert data["year_max"] == 2018


def test_parse_cyrillic_brand_alias():
    data = parse_criteria("хочу тойоту левый руль", agent_type="ai_auto")
    assert data["brand"] == "toyota"
    assert data["steering"] == "left"


def test_parse_chevrolet_cobalt_and_engine():
    data = parse_criteria(
        "ищу шевроле кобальт 1.5л в Бишкеке от 400000 до 700000",
        agent_type="ai_auto",
    )
    assert data["brand"] == "chevrolet"
    assert data["model"] == "cobalt"
    assert data["engine_volume"] == "1.5"
    assert data["city"] == "Бишкек"
    assert data["min_price"] == 400000
    assert data["max_price"] == 700000


def test_parse_engine_volume_explicit():
    data = parse_criteria(
        "Toyota Camry объём двигателя 2,0",
        agent_type="ai_auto",
    )
    assert data["brand"] == "toyota"
    assert data["model"] == "camry"
    assert data["engine_volume"] == "2"


def test_parse_realtor_rooms():
    data = parse_criteria("2 комнатная квартира в Оше от 30000", agent_type="ai_realtor")
    assert data["rooms"] == 2
    assert data["city"] == "Ош"
    assert data["min_price"] == 30000
    assert "model" not in data
    assert "engine_volume" not in data


def test_criteria_contract_roundtrip():
    raw = parse_criteria("Kia Sportage до 1 200 000", agent_type="ai_auto")
    c = AiSearchCriteria.from_dict(raw)
    assert c.brand == "kia"
    assert c.model == "sportage"
    assert c.max_price == 1200000
    assert "q" in c.to_dict()


def test_normalize_helpers():
    assert normalize_brand("Мерседес") == "mercedes"
    assert normalize_brand("BMW") == "bmw"
    assert normalize_brand(None) is None
    assert normalize_model("Кобальт") == "cobalt"
    assert normalize_model("Camry") == "camry"
    assert normalize_engine_volume("1,5 л") == "1.5"
    assert normalize_engine_volume("2.0") == "2"
    assert normalize_engine_volume("900000") is None
