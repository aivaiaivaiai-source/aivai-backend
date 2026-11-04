"""Deterministic intent semantics — action vs subject (no LLM)."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field

from app.services.category_text import normalize_text


class IntentAction(str, enum.Enum):
    SELL = "SELL"
    BUY = "BUY"
    RENT_OUT = "RENT_OUT"
    RENT_WANTED = "RENT_WANTED"
    SERVICE_OFFER = "SERVICE_OFFER"
    SERVICE_WANTED = "SERVICE_WANTED"
    HIRE = "HIRE"
    JOB_SEEK = "JOB_SEEK"
    GIVE_AWAY = "GIVE_AWAY"
    EXCHANGE = "EXCHANGE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class IntentSemantics:
    action: IntentAction
    subject_terms: tuple[str, ...]
    qualifiers: tuple[str, ...]
    confidence: float
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_json(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "subject_terms": list(self.subject_terms),
            "qualifiers": list(self.qualifiers),
            "confidence": round(self.confidence, 4),
            "evidence": list(self.evidence),
        }


# Order matters — more specific patterns first.
_ACTION_RULES: tuple[tuple[IntentAction, re.Pattern[str], float, str], ...] = (
    # Jobs — seek before hire; "ищu работу" before "ищu водителя".
    (IntentAction.JOB_SEEK, re.compile(r"ищу\s+работ", re.I), 0.92, "job_seek_phrase"),
    (IntentAction.JOB_SEEK, re.compile(r"нужна\s+работ", re.I), 0.9, "job_need_work"),
    (IntentAction.JOB_SEEK, re.compile(r"\bрезюме\b", re.I), 0.9, "resume_keyword"),
    (IntentAction.JOB_SEEK, re.compile(r"трудоустройств", re.I), 0.85, "employment_keyword"),
    (IntentAction.HIRE, re.compile(r"ищу\s+.+\s+на\s+работу", re.I), 0.9, "hire_on_job"),
    (IntentAction.HIRE, re.compile(r"нужен\s+(?:водител|сотрудник|рабоч)", re.I), 0.9, "hire_need_person"),
    (IntentAction.HIRE, re.compile(r"ищу\s+(?:водител|сотрудник|рабоч)", re.I), 0.88, "hire_seek_person"),
    (IntentAction.HIRE, re.compile(r"\bваканс", re.I), 0.88, "vacancy_keyword"),
    (IntentAction.HIRE, re.compile(r"требуется\s+(?:водител|сотрудник|рабоч)", re.I), 0.86, "required_person"),
    # Rent before sell/buy.
    (IntentAction.RENT_WANTED, re.compile(r"возьму\s+.+\s+в\s+аренду", re.I), 0.9, "rent_wanted_take"),
    (IntentAction.RENT_WANTED, re.compile(r"нужен\s+.+\s+в\s+аренду", re.I), 0.88, "rent_wanted_need"),
    (IntentAction.RENT_WANTED, re.compile(r"сниму|снять\s+в\s+аренду|ищу\s+в\s+аренду", re.I), 0.86, "rent_wanted"),
    (IntentAction.RENT_OUT, re.compile(r"сдам|сдаю\s+в\s+аренду|сдаётся", re.I), 0.88, "rent_out"),
    # Service wanted before service offer.
    (IntentAction.SERVICE_WANTED, re.compile(r"нужен\s+(?:сантехник|электрик|мастер)", re.I), 0.88, "service_wanted_pro"),
    (IntentAction.SERVICE_WANTED, re.compile(r"нужна\s+грузоперевоз", re.I), 0.88, "service_wanted_cargo"),
    (IntentAction.SERVICE_OFFER, re.compile(r"предлага(?:ю|ем)\s+услуг", re.I), 0.92, "service_offer_phrase"),
    (IntentAction.SERVICE_OFFER, re.compile(r"оказыва(?:ю|ем)\s+услуг", re.I), 0.9, "service_provide"),
    (IntentAction.SERVICE_OFFER, re.compile(r"услуги\s+(?:сантехник|электрик|экскаватор|грузоперевоз|фотограф)", re.I), 0.9, "service_type"),
    (IntentAction.SERVICE_OFFER, re.compile(r"грузоперевоз", re.I), 0.88, "cargo_transport_service"),
    (IntentAction.SERVICE_OFFER, re.compile(r"перевезу|перевозу", re.I), 0.87, "transport_offer_verb"),
    (IntentAction.SERVICE_OFFER, re.compile(r"ремонтирую|^ремонт\b", re.I), 0.86, "repair_offer"),
    (IntentAction.SERVICE_OFFER, re.compile(r"^электрик\b", re.I), 0.84, "electrician_offer_line"),
    (IntentAction.SERVICE_WANTED, re.compile(r"нужн(?:а|ы)\s+услуг", re.I), 0.85, "service_wanted"),
    (IntentAction.GIVE_AWAY, re.compile(r"отдам\s+даром|бесплатно|даром", re.I), 0.88, "give_away"),
    (IntentAction.EXCHANGE, re.compile(r"\bобмен\b|\bменяю\b|\bобменяю\b", re.I), 0.85, "exchange"),
    (IntentAction.BUY, re.compile(r"куплю|покупаю|ищу\s+купить", re.I), 0.88, "buy"),
    (IntentAction.SELL, re.compile(r"прода(?:ю|м|ть)|продам|\bsale\b", re.I), 0.86, "sell"),
)

_SUBJECT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("камаз", re.compile(r"камаз|kamaz", re.I)),
    ("грузовик", re.compile(r"грузовик|фура", re.I)),
    ("газель", re.compile(r"газель|gazelle", re.I)),
    ("соболь", re.compile(r"соболь|sobol", re.I)),
    ("sprinter", re.compile(r"sprinter|спринтер", re.I)),
    ("transit", re.compile(r"\btransit\b|транзит", re.I)),
    ("hiace", re.compile(r"hiace|хайас|хайс", re.I)),
    ("porter", re.compile(r"\bporter\b|портер", re.I)),
    ("запчаст", re.compile(r"запчаст|автозапчаст|бампер|фара|аккумулятор", re.I)),
    ("двигатель", re.compile(r"двигател|мотор\b", re.I)),
    ("коробка", re.compile(r"коробк|кпп|transmission", re.I)),
    ("шины", re.compile(r"шин[ыа]|r17", re.I)),
    ("диски", re.compile(r"\bдиск", re.I)),
    ("авто", re.compile(r"авто|машин|легков|bmw|toyota|mercedes|седан|camry", re.I)),
    ("экскаватор", re.compile(r"экскаватор|погрузчик|спецтехник|кран\b", re.I)),
    ("сантехник", re.compile(r"сантехник|труб|унитаз", re.I)),
    ("электрик", re.compile(r"электрик|проводк|розетк", re.I)),
    ("фотограф", re.compile(r"фотограф", re.I)),
    ("квартира", re.compile(r"квартир|недвижим|дом\b|участок", re.I)),
    ("телефон", re.compile(r"айфон|iphone|телефон|ноутбук|планшет|samsung", re.I)),
    ("мото", re.compile(r"мото|мотоцикл|скутер", re.I)),
    ("лодка", re.compile(r"лодк|катер|яхт|гидроцикл", re.I)),
    ("грузоперевоз", re.compile(r"грузоперевоз|перевоз|переезд", re.I)),
    ("корова", re.compile(r"коров|бык|телен", re.I)),
)

LCV_EXECUTION_SUBJECTS = frozenset(
    {
        "газель",
        "соболь",
        "sprinter",
        "transit",
        "hiace",
        "porter",
    }
)

_QUALIFIER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("toyota", re.compile(r"toyota|тойота", re.I)),
    ("urgent", re.compile(r"срочно|быстро", re.I)),
    ("cargo_execution", re.compile(r"грузов(?:ой|ая|ое|ые|ым|ого)|\bcargo\b", re.I)),
    (
        "passenger_execution",
        re.compile(r"пассажирск(?:ий|ая|ое|ие)|\bpassenger\b|микроавтобус", re.I),
    ),
)


def interpret_intent(raw_text: str) -> IntentSemantics:
    text = (raw_text or "").strip()
    if not text:
        return IntentSemantics(
            action=IntentAction.UNKNOWN,
            subject_terms=(),
            qualifiers=(),
            confidence=0.0,
            evidence=("empty",),
        )

    normalized = normalize_text(text)
    evidence: list[str] = []
    action = IntentAction.UNKNOWN
    action_conf = 0.35

    for candidate_action, pattern, conf, tag in _ACTION_RULES:
        if pattern.search(text) or pattern.search(normalized):
            action = candidate_action
            action_conf = conf
            evidence.append(f"action:{tag}")
            break

    subjects: list[str] = []
    for term, pattern in _SUBJECT_PATTERNS:
        if pattern.search(text) or pattern.search(normalized):
            subjects.append(term)
            evidence.append(f"subject:{term}")

    qualifiers: list[str] = []
    for term, pattern in _QUALIFIER_PATTERNS:
        if pattern.search(text) or pattern.search(normalized):
            qualifiers.append(term)
            evidence.append(f"qualifier:{term}")

    if action == IntentAction.UNKNOWN and re.search(r"услуг", text, re.I):
        action = IntentAction.SERVICE_OFFER
        action_conf = 0.78
        evidence.append("action:service_implied")

    overall = action_conf
    if subjects:
        overall = min(0.98, overall + 0.05 * min(len(subjects), 2))

    return IntentSemantics(
        action=action,
        subject_terms=tuple(subjects),
        qualifiers=tuple(qualifiers),
        confidence=round(overall, 4),
        evidence=tuple(evidence),
    )
