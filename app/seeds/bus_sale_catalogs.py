"""Brand/model SoT for Buses L1 sale subtypes.

Full buses reuse VehicleType.bus brands from parts_vehicle_catalogs.
This module covers microbuses and motorhomes.
"""
from __future__ import annotations

from app.models.category_enums import VehicleType

# (slug, name, country, vehicle_type)
BUS_SALE_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    # Microbuses
    ("mercedes-microbus", "Mercedes-Benz", "Germany", VehicleType.microbus),
    ("ford-microbus", "Ford", "USA", VehicleType.microbus),
    ("gaz-microbus", "ГАЗ", "Russia", VehicleType.microbus),
    ("hyundai-microbus", "Hyundai", "Korea", VehicleType.microbus),
    ("toyota-microbus", "Toyota", "Japan", VehicleType.microbus),
    ("volkswagen-microbus", "Volkswagen", "Germany", VehicleType.microbus),
    ("iveco-microbus", "Iveco", "Italy", VehicleType.microbus),
    ("fiat-microbus", "Fiat", "Italy", VehicleType.microbus),
    ("peugeot-microbus", "Peugeot", "France", VehicleType.microbus),
    ("citroen-microbus", "Citroen", "France", VehicleType.microbus),
    ("nissan-microbus", "Nissan", "Japan", VehicleType.microbus),
    ("isuzu-microbus", "Isuzu", "Japan", VehicleType.microbus),
    ("daewoo-microbus", "Daewoo", "Korea", VehicleType.microbus),
    ("foton-microbus", "Foton", "China", VehicleType.microbus),
    ("uaz-microbus", "UAZ", "Russia", VehicleType.microbus),
    ("baw-microbus", "BAW", "China", VehicleType.microbus),
    ("jac-microbus", "JAC", "China", VehicleType.microbus),
    ("dongfeng-microbus", "Dongfeng", "China", VehicleType.microbus),
    # Catch-all «Другая марка» (optional brand UX)
    ("other-bus", "Другая марка", None, VehicleType.bus),
    ("other-microbus", "Другая марка", None, VehicleType.microbus),
    ("other-motorhome", "Другая марка", None, VehicleType.motorhome),
    # Motorhomes / camper vans
    ("adria", "Adria", "Slovenia", VehicleType.motorhome),
    ("hymer", "Hymer", "Germany", VehicleType.motorhome),
    ("burstner", "Bürstner", "Germany", VehicleType.motorhome),
    ("dethleffs", "Dethleffs", "Germany", VehicleType.motorhome),
    ("knaus", "Knaus", "Germany", VehicleType.motorhome),
    ("hobby-mh", "Hobby", "Germany", VehicleType.motorhome),
    ("chausson", "Chausson", "France", VehicleType.motorhome),
    ("winnebago", "Winnebago", "USA", VehicleType.motorhome),
    ("fiat-motorhome", "Fiat", "Italy", VehicleType.motorhome),
    ("mercedes-motorhome", "Mercedes-Benz", "Germany", VehicleType.motorhome),
    ("ford-motorhome", "Ford", "USA", VehicleType.motorhome),
    ("volkswagen-motorhome", "Volkswagen", "Germany", VehicleType.motorhome),
    ("gaz-motorhome", "ГАЗ", "Russia", VehicleType.motorhome),
    ("iveco-motorhome", "Iveco", "Italy", VehicleType.motorhome),
    ("peugeot-motorhome", "Peugeot", "France", VehicleType.motorhome),
]

BUS_SALE_MODELS: dict[str, list[tuple[str, str]]] = {
    "mercedes-microbus": [
        ("sprinter", "Sprinter"),
        ("vito", "Vito"),
        ("sprinter-city", "Sprinter City"),
    ],
    "ford-microbus": [
        ("transit", "Transit"),
        ("transit-custom", "Transit Custom"),
        ("tourneo", "Tourneo"),
    ],
    "gaz-microbus": [
        ("gazelle-next", "Газель Next"),
        ("gazelle-business", "Газель Бизнес"),
        ("sobol", "Соболь"),
        ("vector-next", "Vector Next"),
    ],
    "hyundai-microbus": [
        ("county", "County"),
        ("staria", "Staria"),
        ("h350", "H350"),
        ("solati", "Solati"),
    ],
    "toyota-microbus": [
        ("hiace", "Hiace"),
        ("coaster", "Coaster"),
        ("alphard", "Alphard"),
    ],
    "volkswagen-microbus": [
        ("crafter", "Crafter"),
        ("transporter", "Transporter"),
        ("caravelle", "Caravelle"),
        ("multivan", "Multivan"),
    ],
    "iveco-microbus": [
        ("daily", "Daily"),
        ("daily-minibus", "Daily Minibus"),
    ],
    "fiat-microbus": [
        ("ducato", "Ducato"),
        ("doblo", "Doblo"),
    ],
    "peugeot-microbus": [
        ("boxer", "Boxer"),
        ("traveller", "Traveller"),
        ("expert", "Expert"),
    ],
    "citroen-microbus": [
        ("jumper", "Jumper"),
        ("spacetourer", "SpaceTourer"),
        ("jumpy", "Jumpy"),
    ],
    "nissan-microbus": [
        ("urvan", "Urvan"),
        ("nv350", "NV350"),
        ("caravan", "Caravan"),
    ],
    "isuzu-microbus": [
        # Elf / NQR are cargo trucks — excluded from passenger microbus catalog.
        ("journey", "Journey"),
    ],
    "adria": [
        ("twin", "Twin"),
        ("matrix", "Matrix"),
        ("coral", "Coral"),
        ("sonic", "Sonic"),
    ],
    "hymer": [
        ("b-class", "B-Class"),
        ("ml-t", "ML-T"),
        ("exsis", "Exsis"),
        ("free", "Free"),
    ],
    "burstner": [
        ("lyseo", "Lyseo"),
        ("ixeo", "Ixeo"),
        ("nexo", "Nexxo"),
        ("eliseo", "Eliseo"),
    ],
    "dethleffs": [
        ("trend", "Trend"),
        ("globebus", "Globebus"),
        ("esprit", "Esprit"),
        ("pulse", "Pulse"),
    ],
    "knaus": [
        ("van-ti", "Van TI"),
        ("live-i", "Live I"),
        ("sky-ti", "Sky TI"),
        ("boxlife", "Boxlife"),
    ],
    "hobby-mh": [
        ("optima", "Optima"),
        ("siesta", "Siesta"),
        ("vantana", "Vantana"),
        ("ontour", "OnTour"),
    ],
    "chausson": [
        ("titanium", "Titanium"),
        ("first-line", "First Line"),
        ("vip", "VIP"),
        ("flash", "Flash"),
    ],
    "winnebago": [
        ("view", "View"),
        ("adventurer", "Adventurer"),
        ("intent", "Intent"),
        ("solis", "Solis"),
    ],
    "fiat-motorhome": [
        ("ducato-camper", "Ducato Camper"),
        ("ducato", "Ducato"),
    ],
    "mercedes-motorhome": [
        ("sprinter-camper", "Sprinter Camper"),
        ("marco-polo", "Marco Polo"),
        ("vito-marco-polo", "Vito Marco Polo"),
    ],
    "ford-motorhome": [
        ("transit-camper", "Transit Camper"),
        ("nugget", "Nugget"),
        ("transit-custom-nugget", "Transit Custom Nugget"),
    ],
    "volkswagen-motorhome": [
        ("california", "California"),
        ("grand-california", "Grand California"),
        ("crafter-camper", "Crafter Camper"),
    ],
    "daewoo-microbus": [
        ("damas", "Damas"),
        # Labo / Nexia Van are cargo — excluded from passenger microbus catalog.
    ],
    "foton-microbus": [
        ("view", "View"),
        ("toano", "Toano"),
        ("view-cs2", "View CS2"),
    ],
    "uaz-microbus": [
        ("2206", "2206"),
        # 3741 is cargo van — excluded from passenger microbus catalog.
        ("profi-bus", "Профи автобус"),
    ],
    "other-bus": [
        ("other-model", "Другая модель"),
    ],
    "other-microbus": [
        ("other-model", "Другая модель"),
    ],
    "other-motorhome": [
        ("other-model", "Другая модель"),
    ],
    "baw-microbus": [
        ("street", "Street"),
        ("tonik", "Tonik"),
        ("fenix", "Fenix"),
    ],
    "jac-microbus": [
        ("sunray", "Sunray"),
        ("refine", "Refine"),
        ("m1", "M1"),
    ],
    "dongfeng-microbus": [
        ("eq5021", "EQ5021"),
        ("mini-bus", "Mini Bus"),
        ("captain-c", "Captain-C"),
    ],
    "gaz-motorhome": [
        ("gazelle-camper", "Газель Camper"),
        ("sobol-camper", "Соболь Camper"),
        ("next-camper", "Next Camper"),
    ],
    "iveco-motorhome": [
        ("daily-camper", "Daily Camper"),
        ("daily", "Daily"),
    ],
    "peugeot-motorhome": [
        ("boxer-camper", "Boxer Camper"),
        ("traveller-camper", "Traveller Camper"),
    ],
}
