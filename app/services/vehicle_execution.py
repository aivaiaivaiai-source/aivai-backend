"""Vehicle execution / catalog-context helpers (SoT semantics)."""
from __future__ import annotations

from app.models.category_enums import VehicleCatalogContext, VehicleExecution

# Stable machine values → RU labels (display only).
VEHICLE_EXECUTION_LABELS_RU: dict[VehicleExecution, str] = {
    VehicleExecution.cargo: "Грузовой",
    VehicleExecution.passenger: "Пассажирский",
}

# Placement for a concrete listing after execution is chosen.
EXECUTION_PLACEMENT_SLUG: dict[VehicleExecution, str] = {
    VehicleExecution.cargo: "transport-commercial-malotonnazhnye-gruzoviki",
    VehicleExecution.passenger: "transport-commercial-mikroavtobusy",
}

# (brand_slug, model_slug) → allowed executions. Seeded into DB; IDs resolved at migrate time.
APPROVED_MODEL_EXECUTIONS: dict[tuple[str, str], tuple[VehicleExecution, ...]] = {
    # Dual
    ("mercedes-benz", "sprinter"): (VehicleExecution.cargo, VehicleExecution.passenger),
    ("gaz", "gazelle"): (VehicleExecution.cargo, VehicleExecution.passenger),
    ("gaz", "gazelle-next"): (VehicleExecution.cargo, VehicleExecution.passenger),
    ("gaz", "gazelle-business"): (VehicleExecution.cargo, VehicleExecution.passenger),
    ("gaz", "sobol"): (VehicleExecution.cargo, VehicleExecution.passenger),
    ("ford", "transit"): (VehicleExecution.cargo, VehicleExecution.passenger),
    ("ford", "transit-custom"): (VehicleExecution.cargo, VehicleExecution.passenger),
    ("toyota", "hiace"): (VehicleExecution.cargo, VehicleExecution.passenger),
    # Cargo-only (AiVai V2 + KG LCV)
    ("hyundai", "porter"): (VehicleExecution.cargo,),
    ("hyundai", "porter-ii"): (VehicleExecution.cargo,),
    ("hyundai", "hd35"): (VehicleExecution.cargo,),
    ("hyundai", "hd65"): (VehicleExecution.cargo,),
    ("hyundai", "hd78"): (VehicleExecution.cargo,),
    ("kia", "bongo"): (VehicleExecution.cargo,),
    ("kia", "bongo-iii"): (VehicleExecution.cargo,),
    ("kia", "k2500"): (VehicleExecution.cargo,),
    ("gaz", "valdai-next"): (VehicleExecution.cargo,),
    ("mercedes-benz", "atego"): (VehicleExecution.cargo,),
    ("toyota", "dyna"): (VehicleExecution.cargo,),
    ("iveco", "daily"): (VehicleExecution.cargo,),
    ("iveco", "eurocargo"): (VehicleExecution.cargo,),
    ("fiat", "ducato"): (VehicleExecution.cargo,),
    ("fiat", "doblo-cargo"): (VehicleExecution.cargo,),
    ("citroen", "jumper"): (VehicleExecution.cargo,),
    ("uaz", "profi"): (VehicleExecution.cargo,),
}

# Models excluded from new car-sale / passenger-parts pickers.
NON_CAR_SALE_MODEL_KEYS: frozenset[tuple[str, str]] = frozenset(
    APPROVED_MODEL_EXECUTIONS.keys()
)

# Subject tokens for resolver (model families that need execution).
EXECUTION_SENSITIVE_SUBJECTS: frozenset[str] = frozenset(
    {
        "sprinter",
        "gazelle",
        "газель",
        "sobol",
        "соболь",
        "transit",
        "hiace",
        "porter",
        "портер",
        "bongo",
        "daily",
        "ducato",
        "jumper",
        "profi",
    }
)


def resolve_catalog_context(
    *,
    catalog_context: str | None = None,
    applicability: str | None = None,
    vehicle_type: str | None = None,
) -> VehicleCatalogContext | None:
    """Map API query params to a catalog context."""
    if catalog_context:
        raw = catalog_context.strip().lower()
        try:
            return VehicleCatalogContext(raw)
        except ValueError as exc:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail=f"Unknown catalog_context '{catalog_context}'",
            ) from exc
    if applicability:
        key = applicability.strip().lower()
        if key == "passenger_cars":
            return VehicleCatalogContext.passenger_parts
        if key == "cargo":
            return VehicleCatalogContext.cargo_parts
        # buses / special / farm / moto / … use VehicleType filter, not LCV contexts.
    if vehicle_type:
        vt = vehicle_type.strip().lower()
        if vt == "car":
            # Parts passenger path often passes vehicle_type=car.
            return VehicleCatalogContext.passenger_parts
        if vt == "truck":
            return VehicleCatalogContext.cargo_parts
        # vehicle_type=bus → VehicleType.bus brands (not bus_parts LCV proxy).
    return None


def parse_execution(value: str | None) -> VehicleExecution | None:
    if not value:
        return None
    try:
        return VehicleExecution(value.strip().lower())
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Unknown vehicle_execution '{value}'",
        ) from exc


def detect_execution_from_text(text: str) -> VehicleExecution | None:
    """Resolver helper: only explicit cargo/passenger signals; never guess."""
    import re

    t = (text or "").lower()
    cargo = re.search(
        r"грузов(?:ой|ая|ое|ые|ым|ого)|cargo\b|commercial\s+van",
        t,
    )
    passenger = re.search(
        r"пассажирск(?:ий|ая|ое|ие)|passenger\b|микроавтобус|minibus",
        t,
    )
    if cargo and not passenger:
        return VehicleExecution.cargo
    if passenger and not cargo:
        return VehicleExecution.passenger
    return None


def text_mentions_execution_sensitive_subject(text: str) -> bool:
    """True when text mentions an approved dual/cargo LCV family name."""
    import re

    t = (text or "").lower()
    for token in EXECUTION_SENSITIVE_SUBJECTS:
        if re.search(rf"(?<![a-zа-яё]){re.escape(token)}(?![a-zа-яё])", t):
            return True
    return False
