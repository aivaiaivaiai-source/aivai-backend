"""Action ↔ category compatibility — deterministic penalties/bonuses."""

from __future__ import annotations

from app.category_resolver.intent_semantics import (
    IntentAction,
    IntentSemantics,
    LCV_EXECUTION_SUBJECTS,
)
from app.models.category_enums import VehicleExecution

# Slug substrings that indicate job-seeker vs employer branches (Catalog SoT patterns).
_JOB_SEEK_SLUG_MARKERS = (
    "jobs-resume",
    "jobs-rezyume",
    "rezyume-soiskateley",
)
_JOB_HIRE_SLUG_MARKERS = (
    "jobs-vacancies",
    "jobs-vakansii",
    "vakansii-bez-opyta",
)

_OBJECT_SALE_PREFIXES = (
    "transport-car-sale",
    "transport-cargo",
    "transport-special-equipment",
    "transport-auto-parts",
    "transport-moto-tech",
    "electronics-phones",
    "real-estate-sale",
)

_GENERIC_SERVICE_SLUGS = frozenset(
    {
        "services-transport",
        "services-prochie-uslugi",
        "services-bytovye-uslugi",
    }
)


def is_job_seek_slug(slug: str) -> bool:
    return any(m in slug for m in _JOB_SEEK_SLUG_MARKERS)


def is_job_hire_slug(slug: str) -> bool:
    return any(m in slug for m in _JOB_HIRE_SLUG_MARKERS)


def action_compatibility_adjustment(
    slug: str,
    intent: IntentSemantics,
    *,
    base_score: float,
) -> tuple[float, str | None]:
    """
    Return adjusted score and optional reason tag.
    Negative adjustment = penalty; positive = bonus.
    """
    score = base_score
    tag: str | None = None

    if intent.action == IntentAction.JOB_SEEK:
        if is_job_hire_slug(slug):
            score -= 0.45
            tag = "incompatible:job_seek_vs_vacancy"
        elif is_job_seek_slug(slug):
            score += 0.08
            tag = "compatible:job_seek"
    elif intent.action == IntentAction.HIRE:
        if is_job_seek_slug(slug):
            score -= 0.45
            tag = "incompatible:hire_vs_resume"
        elif is_job_hire_slug(slug):
            score += 0.08
            tag = "compatible:hire"

    if intent.action in (IntentAction.SERVICE_OFFER, IntentAction.SERVICE_WANTED):
        if slug.startswith("services-") and slug not in _GENERIC_SERVICE_SLUGS:
            score += 0.06
            tag = tag or "compatible:specific_service"
        if any(slug.startswith(p) for p in _OBJECT_SALE_PREFIXES):
            score -= 0.35
            tag = "incompatible:service_vs_object_sale"

    if intent.action in (IntentAction.SELL, IntentAction.BUY, IntentAction.RENT_OUT, IntentAction.RENT_WANTED):
        if slug.startswith("services-") and "грузоперевоз" not in intent.subject_terms:
            score -= 0.38
            tag = tag or "incompatible:object_vs_service"

    part_terms = ("запчаст", "двигатель", "коробка", "шины", "диски")
    if intent.action in (IntentAction.SELL, IntentAction.BUY) and any(
        t in intent.subject_terms for t in part_terms
    ):
        if slug.startswith("transport-auto-parts") or slug.startswith("transport-tires-wheels"):
            score += 0.1
            tag = tag or "compatible:parts"
        if slug in ("transport-car-sale", "transport-cargo", "transport-buses-microbuses-motorhomes"):
            score -= 0.42
            tag = "incompatible:parts_vs_vehicle_sale"

    if intent.action in (IntentAction.RENT_OUT, IntentAction.RENT_WANTED):
        if slug in ("transport-car-sale", "real-estate-sale"):
            score -= 0.42
            tag = tag or "incompatible:rent_vs_sale"
        if "transport-rental" in slug and "квартира" in intent.subject_terms:
            score -= 0.55
            tag = tag or "incompatible:rent_realty_vs_transport"
        if slug == "real-estate-rent" and "квартира" in intent.subject_terms:
            score += 0.22
            tag = tag or "compatible:real_estate_rent"
        elif slug == "real-estate-rent":
            score += 0.1
            tag = tag or "compatible:rent"
        elif "transport-rental" in slug:
            score += 0.1
            tag = tag or "compatible:rent"
        if intent.action in (IntentAction.RENT_OUT, IntentAction.RENT_WANTED) and slug == "real-estate-sale":
            score -= 0.5
            tag = tag or "incompatible:rent_vs_sale_branch"

    if intent.action in (IntentAction.SELL, IntentAction.BUY) and (
        LCV_EXECUTION_SUBJECTS & set(intent.subject_terms)
    ):
        detected: VehicleExecution | None = None
        if "cargo_execution" in intent.qualifiers and "passenger_execution" not in intent.qualifiers:
            detected = VehicleExecution.cargo
        elif "passenger_execution" in intent.qualifiers and "cargo_execution" not in intent.qualifiers:
            detected = VehicleExecution.passenger
        # Prefer explicit execution placement; never push car-sale for these models.
        if slug == "transport-car-sale":
            score -= 0.45
            tag = tag or "incompatible:lcv_vs_car_sale"
        if detected == VehicleExecution.cargo:
            if slug in (
                "transport-cargo",
                "transport-commercial-malotonnazhnye-gruzoviki",
            ) or slug.startswith("transport-cargo"):
                score += 0.18
                tag = tag or "compatible:lcv_cargo"
            if slug.startswith("transport-buses") or "mikroavtobus" in slug:
                score -= 0.2
                tag = tag or "incompatible:lcv_cargo_vs_bus"
        elif detected == VehicleExecution.passenger:
            if slug.startswith("transport-buses") or "mikroavtobus" in slug:
                score += 0.18
                tag = tag or "compatible:lcv_passenger"
            if slug.startswith("transport-cargo"):
                score -= 0.2
                tag = tag or "incompatible:lcv_passenger_vs_cargo"
        else:
            # Unresolved dual: allow cargo OR buses, never car-sale (already penalized).
            if slug in (
                "transport-cargo",
                "transport-buses-microbuses-motorhomes",
            ) or slug.startswith("transport-cargo") or "mikroavtobus" in slug:
                score += 0.1
                tag = tag or "compatible:lcv_unresolved"

    if intent.action == IntentAction.RENT_OUT and "transport-rental" in slug:
        score += 0.04
    if intent.action == IntentAction.RENT_WANTED and "transport-rental" in slug:
        score += 0.04

    if intent.action == IntentAction.EXCHANGE and slug == "free-exchange-swap":
        score += 0.12
        tag = tag or "compatible:exchange"

    return max(0.0, min(0.99, score)), tag


def is_generic_slug(slug: str) -> bool:
    return slug in _GENERIC_SERVICE_SLUGS or slug in ("jobs", "transport", "services", "electronics")


def specificity_bonus(slug: str, intent: IntentSemantics, competitor_slug: str) -> float:
    """Bounded bonus when specific slug beats generic overlap."""
    if is_generic_slug(competitor_slug) and not is_generic_slug(slug):
        if slug.startswith("services-") and intent.action in (
            IntentAction.SERVICE_OFFER,
            IntentAction.SERVICE_WANTED,
        ):
            return 0.06
        if slug.startswith("transport-") and intent.action in (
            IntentAction.SELL,
            IntentAction.BUY,
            IntentAction.RENT_OUT,
        ):
            return 0.05
        if slug.startswith("jobs-") and intent.action in (IntentAction.JOB_SEEK, IntentAction.HIRE):
            return 0.05
    return 0.0
