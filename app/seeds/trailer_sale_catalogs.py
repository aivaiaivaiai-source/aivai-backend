"""Brand/model SoT for Trailers L1 sale subtypes.

Parts trailer brands live in parts_vehicle_catalogs (VehicleType.trailer).
"""
from __future__ import annotations

from app.models.category_enums import VehicleType

# (slug, name, country, vehicle_type)
TRAILER_SALE_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    # Drawbar trailers — прицепы
    ("mzsa", "МЗСА", "Russia", VehicleType.drawbar_trailer),
    ("kurgan", "Курганские прицепы", "Russia", VehicleType.drawbar_trailer),
    ("laker", "Laker", "Russia", VehicleType.drawbar_trailer),
    ("treyler", "Трейлер", "Russia", VehicleType.drawbar_trailer),
    ("avtos", "Автос", "Russia", VehicleType.drawbar_trailer),
    ("expedition", "Экспедиция", "Russia", VehicleType.drawbar_trailer),
    ("thule-trailer", "Thule", "Sweden", VehicleType.drawbar_trailer),
    ("humbaur", "Humbaur", "Germany", VehicleType.drawbar_trailer),
    ("bocker", "Böckmann", "Germany", VehicleType.drawbar_trailer),
    ("respo", "Respo", "Estonia", VehicleType.drawbar_trailer),
    # Semi-trailers — полуприцепы
    ("schmitz-semi", "Schmitz Cargobull", "Germany", VehicleType.semi_trailer),
    ("krone-semi", "Krone", "Germany", VehicleType.semi_trailer),
    ("wielton-semi", "Wielton", "Poland", VehicleType.semi_trailer),
    ("koegel-semi", "Kögel", "Germany", VehicleType.semi_trailer),
    ("tonar-semi", "Тонар", "Russia", VehicleType.semi_trailer),
    ("nefaz-semi", "НефАЗ", "Russia", VehicleType.semi_trailer),
    ("maz-semi", "МАЗ", "Belarus", VehicleType.semi_trailer),
    ("chmzap-semi", "ЧМЗАП", "Russia", VehicleType.semi_trailer),
    ("schwarzmueller-semi", "Schwarzmüller", "Austria", VehicleType.semi_trailer),
    ("sessu-semi", "Sesu", None, VehicleType.semi_trailer),
    # Camper / living trailers
    ("hobby-camper", "Hobby", "Germany", VehicleType.camper_trailer),
    ("adria-camper", "Adria", "Slovenia", VehicleType.camper_trailer),
    ("knaus-camper", "Knaus", "Germany", VehicleType.camper_trailer),
    ("burstner-camper", "Bürstner", "Germany", VehicleType.camper_trailer),
    ("dethleffs-camper", "Dethleffs", "Germany", VehicleType.camper_trailer),
    ("fendt-camper", "Fendt Caravan", "Germany", VehicleType.camper_trailer),
    ("tabbert", "Tabbert", "Germany", VehicleType.camper_trailer),
    ("sterling", "Sterling", "UK", VehicleType.camper_trailer),
    ("swift", "Swift", "UK", VehicleType.camper_trailer),
    ("hymer-camper", "Hymer", "Germany", VehicleType.camper_trailer),
]

TRAILER_SALE_MODELS: dict[str, list[tuple[str, str]]] = {
    "mzsa": [
        ("817700", "817700"),
        ("817701", "817701"),
        ("817711", "817711"),
        ("832132", "832132"),
    ],
    "kurgan": [
        ("krechet", "Кречет"),
        ("universal", "Универсал"),
        ("viking", "Викинг"),
    ],
    "laker": [
        ("light", "Light"),
        ("pro", "Pro"),
        ("heavy", "Heavy"),
    ],
    "treyler": [
        ("8294", "8294"),
        ("8322", "8322"),
        ("titan", "Титан"),
    ],
    "avtos": [
        ("a35", "А35"),
        ("a45", "А45"),
        ("a55", "А55"),
    ],
    "expedition": [
        ("business", "Business"),
        ("touring", "Touring"),
        ("cargo", "Cargo"),
    ],
    "thule-trailer": [
        ("chiefline", "Chiefline"),
        ("courier", "Courier"),
    ],
    "humbaur": [
        ("ha", "HA"),
        ("hn", "HN"),
        ("htk", "HTK"),
    ],
    "bocker": [
        ("tl", "TL"),
        ("kt", "KT"),
        ("big-champion", "Big Champion"),
    ],
    "respo": [
        ("m1", "M1"),
        ("m2", "M2"),
        ("m3", "M3"),
    ],
    "schmitz-semi": [
        ("scb-s3b", "SCB*S3B"),
        ("scb-s3t", "SCB*S3T"),
        ("cargobull", "Cargobull"),
    ],
    "krone-semi": [
        ("profi-liner", "Profi Liner"),
        ("cool-liner", "Cool Liner"),
        ("mega-liner", "Mega Liner"),
    ],
    "wielton-semi": [
        ("ns3", "NS3"),
        ("ns34", "NS34"),
        ("pw", "PW"),
    ],
    "koegel-semi": [
        ("cargo", "Cargo"),
        ("lightplus", "Lightplus"),
        ("portamaxx", "PortaMaxx"),
    ],
    "tonar-semi": [
        ("9746", "9746"),
        ("9523", "9523"),
        ("9888", "9888"),
    ],
    "nefaz-semi": [
        ("9334", "9334"),
        ("96894", "96894"),
    ],
    "maz-semi": [
        ("9758", "9758"),
        ("93866", "93866"),
    ],
    "chmzap-semi": [
        ("99064", "99064"),
        ("83881", "83881"),
    ],
    "schwarzmueller-semi": [
        ("spa", "SPA"),
        ("3a", "3-Achs"),
    ],
    "sessu-semi": [
        ("cargo", "Cargo"),
        ("dump", "Dump"),
    ],
    "hobby-camper": [
        ("excellent", "Excellent"),
        ("prestige", "Prestige"),
        ("de-luxe", "De Luxe"),
    ],
    "adria-camper": [
        ("altea", "Altea"),
        ("adora", "Adora"),
        ("alpina", "Alpina"),
    ],
    "knaus-camper": [
        ("sport", "Sport"),
        ("sudwind", "Südwind"),
        ("deseo", "Deseo"),
    ],
    "burstner-camper": [
        ("premio", "Premio"),
        ("averso", "Averso"),
        ("amico", "Amico"),
    ],
    "dethleffs-camper": [
        ("c-go", "c'go"),
        ("beduin", "Beduin"),
        ("nomad", "Nomad"),
    ],
    "fendt-camper": [
        ("bianco", "Bianco"),
        ("tendenza", "Tendenza"),
        ("diamant", "Diamant"),
    ],
    "tabbert": [
        ("pantalica", "Pantalica"),
        ("rossini", "Rossini"),
        ("vivant", "Vivant"),
    ],
    "sterling": [
        ("eccles", "Eccles"),
        ("elite", "Elite"),
    ],
    "swift": [
        ("challenger", "Challenger"),
        ("sprite", "Sprite"),
        ("conqueror", "Conqueror"),
    ],
    "hymer-camper": [
        ("eriba", "Eriba"),
        ("nova", "Nova"),
        ("free", "Free"),
    ],
}
