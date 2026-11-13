"""Visual concept → routing family hints (supporting signal only)."""

from __future__ import annotations

from app.category_resolver.intent_semantics import IntentAction, IntentSemantics

_OBJECT_CONCEPT_SLUG_HINTS: dict[str, tuple[str, ...]] = {
    "PASSENGER_CAR": ("transport-car-sale",),
    "AUTO_PART": ("transport-auto-parts", "transport-tires-wheels"),
    "TRUCK": ("transport-cargo",),
    "SPECIAL_MACHINERY": ("transport-special-equipment",),
    "MOTORCYCLE": ("transport-moto-tech",),
    "WATERCRAFT": ("transport-watercraft",),
    "BUS": ("transport-buses-microbuses-motorhomes",),
    "COMMERCIAL_VAN": ("transport-cargo", "transport-buses-microbuses-motorhomes"),
    "REAL_ESTATE_INTERIOR": ("real-estate-sale", "real-estate-rent"),
    "REAL_ESTATE_EXTERIOR": ("real-estate-sale", "real-estate-rent"),
}

_SERVICE_CONCEPT_SLUG_HINTS: dict[str, tuple[str, ...]] = {
    "TRUCK": ("services-gruzoperevozki-i-pereezdy",),
    "SPECIAL_MACHINERY": ("services-uslugi-spetstehniki",),
    "PASSENGER_CAR": ("services-gruzoperevozki-i-pereezdy",),
    "PERSON": (),
}

_SUBJECT_SLUG_HINTS: dict[str, tuple[str, ...]] = {
    "камаз": ("transport-cargo",),
    "грузовик": ("transport-cargo",),
    "газель": ("transport-cargo", "transport-buses-microbuses-motorhomes"),
    "соболь": ("transport-cargo", "transport-buses-microbuses-motorhomes"),
    "sprinter": ("transport-cargo", "transport-buses-microbuses-motorhomes"),
    "transit": ("transport-cargo", "transport-buses-microbuses-motorhomes"),
    "hiace": ("transport-cargo", "transport-buses-microbuses-motorhomes"),
    "porter": ("transport-cargo",),
    "запчаст": ("transport-auto-parts",),
    "двигатель": ("transport-auto-parts",),
    "коробка": ("transport-auto-parts",),
    "фара": ("transport-auto-parts",),
    "колодки": ("transport-auto-parts",),
    "тормозн": ("transport-auto-parts",),
    "глушитель": ("transport-auto-parts",),
    "магнитол": ("transport-accessories-tuning-avtozvuk-i-multimediya",),
    "шины": ("transport-tires-wheels-shiny", "transport-tires-wheels"),
    "диски": ("transport-tires-wheels-diski", "transport-tires-wheels"),
    "авто": ("transport-car-sale",),
    "сантехник": ("services-santehnika",),
    "электрик": ("services-elektrika",),
    "фотограф": ("services-foto-i-videosemka",),
    "квартира": ("real-estate-sale", "real-estate-rent"),
    "телефон": ("electronics-phones",),
    "мото": ("transport-moto-tech",),
    "лодка": ("transport-watercraft",),
    "грузоперевоз": ("services-gruzoperevozki-i-pereezdy",),
    "корова": ("animals-livestock",),
}


def is_service_action(action: IntentAction) -> bool:
    return action in (IntentAction.SERVICE_OFFER, IntentAction.SERVICE_WANTED)


def is_job_action(action: IntentAction) -> bool:
    return action in (IntentAction.HIRE, IntentAction.JOB_SEEK)


def is_rent_action(action: IntentAction) -> bool:
    return action in (IntentAction.RENT_OUT, IntentAction.RENT_WANTED)


def _excavator_slugs(intent: IntentSemantics) -> tuple[str, ...]:
    if is_service_action(intent.action):
        return ("services-uslugi-spetstehniki",)
    if intent.action in (IntentAction.SELL, IntentAction.BUY):
        return (
            "transport-special-equipment-ekskavatory",
            "transport-special-equipment",
        )
    if is_rent_action(intent.action):
        return ("transport-rental", "transport-special-equipment-ekskavatory")
    return ("transport-special-equipment-ekskavatory",)


def visual_slug_hints(concepts: tuple[str, ...], intent: IntentSemantics) -> tuple[str, ...]:
    hints: list[str] = []
    hint_map = (
        _SERVICE_CONCEPT_SLUG_HINTS
        if is_service_action(intent.action)
        else _OBJECT_CONCEPT_SLUG_HINTS
    )
    for concept in concepts:
        for slug in hint_map.get(concept, ()):
            if slug not in hints:
                hints.append(slug)
    return tuple(hints)


def intent_slug_hints(intent: IntentSemantics) -> tuple[str, ...]:
    hints: list[str] = []
    if intent.action == IntentAction.JOB_SEEK:
        hints.extend(("jobs-resume", "jobs-rezyume-soiskateley"))
    elif intent.action == IntentAction.HIRE:
        hints.extend(("jobs-vacancies", "jobs-vakansii-bez-opyta"))
    elif is_service_action(intent.action):
        if any("repair" in e for e in intent.evidence):
            hints.extend(("services-remont-tehniki", "services-repair"))
        if "грузоперевоз" in intent.subject_terms or any(
            "cargo_transport" in e or "transport_offer" in e for e in intent.evidence
        ):
            hints.append("services-gruzoperevozki-i-pereezdy")
        if "сантехник" in intent.subject_terms:
            hints.append("services-santehnika")
        if "электрик" in intent.subject_terms:
            hints.append("services-elektrika")
        if "фотограф" in intent.subject_terms:
            hints.append("services-foto-i-videosemka")
        if "телефон" in intent.subject_terms and intent.action == IntentAction.SERVICE_OFFER:
            hints.extend(("services-remont-tehniki", "services-repair"))
        if "телефон" in intent.subject_terms and intent.action == IntentAction.SERVICE_WANTED:
            hints.extend(("services-remont-tehniki", "services-repair"))
        if "авто" in intent.subject_terms and "ремонт" in " ".join(intent.evidence):
            hints.append("services-remont-tehniki")
    elif is_rent_action(intent.action):
        if "квартира" in intent.subject_terms:
            hints.append("real-estate-rent")
        if "авто" in intent.subject_terms or "camry" in intent.qualifiers:
            hints.append("transport-rental-legkovye-avtomobili")
        if "грузовик" in intent.subject_terms or "камаз" in intent.subject_terms:
            hints.append("transport-rental-gruzovoy-transport")
        if "квартира" not in intent.subject_terms:
            hints.append("transport-rental")
    # EXCHANGE / GIVE_AWAY: free-exchange retired — no category hints.

    if "экскаватор" in intent.subject_terms:
        for slug in _excavator_slugs(intent):
            if slug not in hints:
                hints.append(slug)

    for term in intent.subject_terms:
        if term == "экскаватор":
            continue
        if is_rent_action(intent.action) and term == "квартира":
            continue
        if is_service_action(intent.action) and term in ("двигатель", "коробка", "шины", "диски", "запчаст"):
            continue
        for slug in _SUBJECT_SLUG_HINTS.get(term, ()):
            if slug not in hints:
                hints.append(slug)
    return tuple(hints)


def detect_intent_visual_conflict(
    intent: IntentSemantics,
    concepts: tuple[str, ...],
) -> bool:
    if not concepts or intent.action == IntentAction.UNKNOWN:
        return False
    top = concepts[0]
    part_terms = ("запчаст", "двигатель", "коробка", "шины", "диски")
    if intent.action in (IntentAction.SELL, IntentAction.BUY) and any(
        t in intent.subject_terms for t in part_terms
    ):
        return top in ("PASSENGER_CAR", "TRUCK", "SPECIAL_MACHINERY")
    if is_service_action(intent.action):
        return top in ("PASSENGER_CAR", "AUTO_PART", "MOTORCYCLE", "TRUCK")
    if is_job_action(intent.action):
        return top in ("TRUCK", "PASSENGER_CAR", "SPECIAL_MACHINERY")
    return False
