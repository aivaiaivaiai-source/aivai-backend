"""Brand/model SoT for Электротранспорт L1 sale subtypes.



VehicleType.electric remains the parts micromobility catalog.

These types power sale Create/Search catalogs only.

"""

from __future__ import annotations



from app.models.category_enums import VehicleType



# (slug, name, country, vehicle_type)

ELECTRIC_SALE_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [

    # E-scooters

    ("ninebot-escooter", "Ninebot", "China", VehicleType.e_scooter),

    ("xiaomi-escooter", "Xiaomi", "China", VehicleType.e_scooter),

    ("kugoo-escooter", "Kugoo", "China", VehicleType.e_scooter),

    ("ultron-escooter", "Ultron", "China", VehicleType.e_scooter),

    ("yadea-escooter", "Yadea", "China", VehicleType.e_scooter),

    ("segway-escooter", "Segway", "China", VehicleType.e_scooter),

    ("razor-escooter", "Razor", "USA", VehicleType.e_scooter),

    ("dualtron", "Dualtron", "Korea", VehicleType.e_scooter),

    ("kaabo", "Kaabo", "China", VehicleType.e_scooter),

    ("inokim", "Inokim", "Israel", VehicleType.e_scooter),

    ("iconbit-escooter", "IconBIT", "Russia", VehicleType.e_scooter),

    ("hiper-escooter", "HIPER", "Russia", VehicleType.e_scooter),

    ("joyor", "Joyor", "China", VehicleType.e_scooter),

    ("sealup", "Sealup", "China", VehicleType.e_scooter),

    ("halten", "Halten", "Russia", VehicleType.e_scooter),

    ("white-siberia", "White Siberia", "Russia", VehicleType.e_scooter),

    ("like-bike", "Like.Bike", "Ukraine", VehicleType.e_scooter),

    ("digma-escooter", "Digma", "Russia", VehicleType.e_scooter),

    ("minimotors", "Minimotors", "Korea", VehicleType.e_scooter),

    ("other-e-scooter", "Другая марка", None, VehicleType.e_scooter),

    # Sit-down electric scooters / электроскутеры

    ("tank-emoped", "Tank", "China", VehicleType.e_moped),

    ("yadea-emoped", "Yadea", "China", VehicleType.e_moped),

    ("sunra-emoped", "Sunra", "China", VehicleType.e_moped),

    ("electro-emoped", "Electro", None, VehicleType.e_moped),

    ("niu", "NIU", "China", VehicleType.e_moped),

    ("super-soco", "Super Soco", "China", VehicleType.e_moped),

    ("horwin", "Horwin", "China", VehicleType.e_moped),

    ("tailg", "Tailg", "China", VehicleType.e_moped),

    ("luyuan", "Luyuan", "China", VehicleType.e_moped),

    ("vmoto", "Vmoto", "Australia", VehicleType.e_moped),

    ("other-e-moped", "Другая марка", None, VehicleType.e_moped),

    # Electric motorcycles (moved/normalized from other_electric + Zero sale mirror)

    ("surron", "Sur-Ron", "China", VehicleType.e_motorcycle),

    ("talaria", "Talaria", "China", VehicleType.e_motorcycle),

    ("stark-varg", "Stark", "Spain", VehicleType.e_motorcycle),

    ("zero-emotorcycle", "Zero", "USA", VehicleType.e_motorcycle),

    ("super-soco-emotorcycle", "Super Soco", "China", VehicleType.e_motorcycle),

    ("vmoto-emotorcycle", "Vmoto", "Australia", VehicleType.e_motorcycle),

    ("kugoo-emotorcycle", "Kugoo", "China", VehicleType.e_motorcycle),

    ("rerode-emotorcycle", "Rerode", "China", VehicleType.e_motorcycle),

    ("other-e-motorcycle", "Другая марка", None, VehicleType.e_motorcycle),

    # Electric ATV — thin catalog + catch-all (OEM long-tail → Другая марка)

    ("other-e-atv", "Другая марка", None, VehicleType.e_atv),

    # Hoverboards

    ("ninebot-hover", "Ninebot", "China", VehicleType.hoverboard),

    ("xiaomi-hover", "Xiaomi", "China", VehicleType.hoverboard),

    ("smart-balance", "Smart Balance", None, VehicleType.hoverboard),

    ("hoverbot", "Hoverbot", None, VehicleType.hoverboard),

    ("giro-smart", "GiroSmart", None, VehicleType.hoverboard),

    ("iconbit-hover", "IconBIT", "Russia", VehicleType.hoverboard),

    ("hiper-hover", "HIPER", "Russia", VehicleType.hoverboard),

    ("razerscooter-hover", "Razor", "USA", VehicleType.hoverboard),

    ("other-hoverboard", "Другая марка", None, VehicleType.hoverboard),

    # Monowheels

    ("inmotion", "Inmotion", "China", VehicleType.monowheel),

    ("gotway", "Begode", "China", VehicleType.monowheel),  # Begode = Gotway successor

    ("kingsong", "KingSong", "China", VehicleType.monowheel),

    ("ninebot-one", "Ninebot One", "China", VehicleType.monowheel),

    ("solowheel", "Solowheel", "USA", VehicleType.monowheel),

    ("ips", "IPS", "China", VehicleType.monowheel),

    ("veteran", "Veteran", "China", VehicleType.monowheel),

    ("nosfet", "NOSFET", "China", VehicleType.monowheel),

    ("other-monowheel", "Другая марка", None, VehicleType.monowheel),

    # Segways / self-balancing

    ("segway-personal", "Segway", "China", VehicleType.segway),

    ("ninebot-segway", "Ninebot", "China", VehicleType.segway),

    ("airwheel", "Airwheel", "China", VehicleType.segway),

    ("robstep", "Robstep", "China", VehicleType.segway),

    ("hoverboard-segway", "Hoverboard", None, VehicleType.segway),

    ("iconbit-segway", "IconBIT", "Russia", VehicleType.segway),

    ("other-segway", "Другая марка", None, VehicleType.segway),

    # Golf carts / mini EV

    ("club-car", "Club Car", "USA", VehicleType.golf_cart),

    ("ezgo", "E-Z-GO", "USA", VehicleType.golf_cart),

    ("yamaha-golf", "Yamaha", "Japan", VehicleType.golf_cart),

    ("polaris-gem", "Polaris GEM", "USA", VehicleType.golf_cart),

    ("star-ev", "Star EV", "USA", VehicleType.golf_cart),

    ("tomberlin", "Tomberlin", "USA", VehicleType.golf_cart),

    ("lvtong", "Lvtong", "China", VehicleType.golf_cart),

    ("eagle-golf", "Eagle", "USA", VehicleType.golf_cart),

    ("other-golf-cart", "Другая марка", None, VehicleType.golf_cart),

    # Other electric (no e-moto dump)

    ("ninebot-other", "Ninebot", "China", VehicleType.other_electric),

    ("xiaomi-other", "Xiaomi", "China", VehicleType.other_electric),

    ("segway-other", "Segway", "China", VehicleType.other_electric),

    ("razor-other", "Razor", "USA", VehicleType.other_electric),

    ("yadea-other", "Yadea", "China", VehicleType.other_electric),

    ("electro-other", "Electro", None, VehicleType.other_electric),

    ("other-other-electric", "Другая марка", None, VehicleType.other_electric),

]



ELECTRIC_SALE_MODELS: dict[str, list[tuple[str, str]]] = {

    "ninebot-escooter": [

        ("max-g30", "Max G30"),

        ("max-g30lp", "Max G30LP"),

        ("f2-pro", "F2 Pro"),

        ("kickscooter-e2", "KickScooter E2"),

        ("gt2", "GT2"),

        ("other", "Другая модель"),

    ],

    "xiaomi-escooter": [

        ("scooter-4-pro", "Electric Scooter 4 Pro"),

        ("scooter-4", "Electric Scooter 4"),

        ("scooter-3", "Electric Scooter 3"),

        ("scooter-essential", "Essential"),

        ("other", "Другая модель"),

    ],

    "kugoo-escooter": [

        ("m4-pro", "M4 Pro"),

        ("g2-pro", "G2 Pro"),

        ("kirin-s1", "Kirin S1"),

        ("s1-pro", "S1 Pro"),

        ("other", "Другая модель"),

    ],

    "ultron-escooter": [

        ("t128", "T128"),

        ("t10", "T10"),

        ("t11", "T11"),

        ("other", "Другая модель"),

    ],

    "yadea-escooter": [

        ("g5", "G5"),

        ("keeness", "Keeness"),

        ("c1s", "C1S"),

        ("other", "Другая модель"),

    ],

    "segway-escooter": [

        ("ninebot-max", "Ninebot Max"),

        ("e2-plus", "E2 Plus"),

        ("p65", "P65"),

        ("other", "Другая модель"),

    ],

    "razor-escooter": [

        ("e300", "E300"),

        ("e100", "E100"),

        ("scooter-c25", "C25"),

        ("other", "Другая модель"),

    ],

    "dualtron": [

        ("thunder", "Thunder"),

        ("ultra", "Ultra"),

        ("mini", "Mini"),

        ("victor", "Victor"),

        ("other", "Другая модель"),

    ],

    "kaabo": [

        ("wolf-warrior", "Wolf Warrior"),

        ("mantis", "Mantis"),

        ("skywalker", "Skywalker"),

        ("other", "Другая модель"),

    ],

    "inokim": [

        ("oxo", "OXO"),

        ("quick-4", "Quick 4"),

        ("ox", "OX"),

        ("other", "Другая модель"),

    ],

    "iconbit-escooter": [

        ("kick-scooter-s65", "Kick Scooter S65"),

        ("tt", "TT"),

        ("other", "Другая модель"),

    ],

    "hiper-escooter": [

        ("sierra", "Sierra"),

        ("dax", "Dax"),

        ("vinco", "Vinco"),

        ("other", "Другая модель"),

    ],

    "joyor": [

        ("y5s", "Y5S"),

        ("y10", "Y10"),

        ("f5", "F5"),

        ("g5", "G5"),

        ("other", "Другая модель"),

    ],

    "sealup": [

        ("q5", "Q5"),

        ("q6", "Q6"),

        ("q8", "Q8"),

        ("other", "Другая модель"),

    ],

    "halten": [

        ("rs-02", "RS-02"),

        ("rs-03", "RS-03"),

        ("tx-02", "TX-02"),

        ("other", "Другая модель"),

    ],

    "white-siberia": [

        ("taiga", "Taiga"),

        ("luna", "Luna"),

        ("siberia", "Siberia"),

        ("other", "Другая модель"),

    ],

    "like-bike": [

        ("one", "One"),

        ("city", "City"),

        ("gt", "GT"),

        ("other", "Другая модель"),

    ],

    "digma-escooter": [

        ("cs1", "CS1"),

        ("cs2", "CS2"),

        ("other", "Другая модель"),

    ],

    "minimotors": [

        ("dualtron-mini", "Dualtron Mini"),

        ("speedway", "Speedway"),

        ("other", "Другая модель"),

    ],

    "other-e-scooter": [("other", "Другая модель")],

    "tank-emoped": [

        ("t108", "T108"),

        ("t150", "T150"),

        ("city", "City"),

        ("other", "Другая модель"),

    ],

    "yadea-emoped": [

        ("g5", "G5"),

        ("c1s", "C1S"),

        ("keeness", "Keeness"),

        ("other", "Другая модель"),

    ],

    "sunra-emoped": [

        ("miku-max", "Miku Max"),

        ("robo-s", "Robo-S"),

        ("hawk", "Hawk"),

        ("other", "Другая модель"),

    ],

    "electro-emoped": [

        ("city", "City"),

        ("pro", "Pro"),

        ("cargo", "Cargo"),

        ("other", "Другая модель"),

    ],

    "niu": [

        ("nqi", "NQi"),

        ("nqi-gt", "NQi GT"),

        ("mqi", "MQi"),

        ("uqi", "UQi"),

        ("other", "Другая модель"),

    ],

    "super-soco": [

        ("cux", "CUX"),

        ("tc-max", "TC Max"),

        ("cpx", "CPX"),

        ("other", "Другая модель"),

    ],

    "horwin": [

        ("ek1", "EK1"),

        ("ek3", "EK3"),

        ("sk3", "SK3"),

        ("other", "Другая модель"),

    ],

    "tailg": [

        ("r5", "R5"),

        ("v5", "V5"),

        ("city", "City"),

        ("other", "Другая модель"),

    ],

    "luyuan": [

        ("ly150", "LY150"),

        ("ly200", "LY200"),

        ("other", "Другая модель"),

    ],

    "vmoto": [

        ("super-soco-cux", "CUX"),

        ("vs1", "VS1"),

        ("other", "Другая модель"),

    ],

    "other-e-moped": [("other", "Другая модель")],

    # E-motorcycle — existing Sur-Ron / Talaria / Stark + Zero / Super Soco mirrors

    "surron": [

        ("light-bee-x", "Light Bee X"),

        ("light-bee", "Light Bee"),

        ("storm-bee", "Storm Bee"),

        ("other", "Другая модель"),

    ],

    "talaria": [

        ("sting", "Sting"),

        ("xxx", "XXX"),

        ("other", "Другая модель"),

    ],

    "stark-varg": [

        ("varg", "Varg"),

        ("other", "Другая модель"),

    ],

    "zero-emotorcycle": [

        ("dsr-x", "DSR/X"),

        ("fxe", "FXE"),

        ("sr-f", "SR/F"),

        ("other", "Другая модель"),

    ],

    "super-soco-emotorcycle": [

        ("cux", "CUX"),

        ("tc-max", "TC Max"),

        ("cpx", "CPX"),

        ("other", "Другая модель"),

    ],

    "vmoto-emotorcycle": [

        ("cux", "CUX"),

        ("vs1", "VS1"),

        ("other", "Другая модель"),

    ],

    "kugoo-emotorcycle": [("other", "Другая модель")],

    "rerode-emotorcycle": [("other", "Другая модель")],

    "other-e-motorcycle": [("other", "Другая модель")],

    "other-e-atv": [("other", "Другая модель")],

    "ninebot-hover": [

        ("s2", "S2"),

        ("mini-pro", "Mini Pro"),

        ("hoverboard-s-plus", "S-Plus"),

        ("other", "Другая модель"),

    ],

    "xiaomi-hover": [

        ("ninebot-s", "Ninebot S"),

        ("balance-scooter", "Balance Scooter"),

        ("other", "Другая модель"),

    ],

    "smart-balance": [

        ("premium-10", "Premium 10.5"),

        ("wheel-6", "Wheel 6.5"),

        ("surfboard", "Surfboard"),

        ("other", "Другая модель"),

    ],

    "hoverbot": [

        ("a-3", "A-3"),

        ("a-6", "A-6"),

        ("r3", "R3"),

        ("other", "Другая модель"),

    ],

    "giro-smart": [

        ("gs-001", "GS-001"),

        ("gs-007", "GS-007"),

        ("other", "Другая модель"),

    ],

    "iconbit-hover": [

        ("smart-scooter", "Smart Scooter"),

        ("kitboard", "Kitboard"),

        ("other", "Другая модель"),

    ],

    "hiper-hover": [

        ("board", "Board"),

        ("wave", "Wave"),

        ("other", "Другая модель"),

    ],

    "razerscooter-hover": [

        ("hovertrax", "Hovertrax"),

        ("ripple", "Ripple"),

        ("other", "Другая модель"),

    ],

    "other-hoverboard": [("other", "Другая модель")],

    "inmotion": [

        ("v11", "V11"),

        ("v12", "V12"),

        ("v13", "V13"),

        ("v8f", "V8F"),

        ("other", "Другая модель"),

    ],

    "gotway": [

        ("msuper-pro", "Msuper Pro"),

        ("nikola", "Nikola"),

        ("rs", "RS"),

        ("tesla", "Tesla"),

        ("other", "Другая модель"),

    ],

    "kingsong": [

        ("s18", "S18"),

        ("s20", "S20"),

        ("16x", "16X"),

        ("14d", "14D"),

        ("other", "Другая модель"),

    ],

    "ninebot-one": [

        ("z10", "Z10"),

        ("s2", "S2"),

        ("a1", "A1"),

        ("other", "Другая модель"),

    ],

    "solowheel": [

        ("xtreme", "Xtreme"),

        ("orbit", "Orbit"),

        ("other", "Другая модель"),

    ],

    "ips": [

        ("i5", "I5"),

        ("121", "121"),

        ("191", "191"),

        ("other", "Другая модель"),

    ],

    "veteran": [

        ("sherman", "Sherman"),

        ("abramson", "Abrams"),

        ("patton", "Patton"),

        ("other", "Другая модель"),

    ],

    "nosfet": [("other", "Другая модель")],

    "other-monowheel": [("other", "Другая модель")],

    "segway-personal": [

        ("i2", "i2"),

        ("x2", "x2"),

        ("ninebot-s-max", "Ninebot S-MAX"),

        ("other", "Другая модель"),

    ],

    "ninebot-segway": [

        ("s-max", "S-MAX"),

        ("me", "me"),

        ("mini-lite", "miniLITE"),

        ("other", "Другая модель"),

    ],

    "airwheel": [

        ("s8", "S8"),

        ("a3", "A3"),

        ("x3", "X3"),

        ("other", "Другая модель"),

    ],

    "robstep": [

        ("x1", "X1"),

        ("s2", "S2"),

        ("other", "Другая модель"),

    ],

    "hoverboard-segway": [

        ("mini", "Mini"),

        ("pro", "Pro"),

        ("other", "Другая модель"),

    ],

    "iconbit-segway": [

        ("trident", "Trident"),

        ("smart", "Smart"),

        ("other", "Другая модель"),

    ],

    "other-segway": [("other", "Другая модель")],

    "club-car": [

        ("precedent", "Precedent"),

        ("tempo", "Tempo"),

        ("onward", "Onward"),

        ("carryall", "Carryall"),

        ("other", "Другая модель"),

    ],

    "ezgo": [

        ("rxv", "RXV"),

        ("txt", "TXT"),

        ("express", "Express"),

        ("liberty", "Liberty"),

        ("other", "Другая модель"),

    ],

    "yamaha-golf": [

        ("drive2", "Drive2"),

        ("adventurer", "Adventurer"),

        ("umax", "UMAX"),

        ("other", "Другая модель"),

    ],

    "polaris-gem": [

        ("e2", "e2"),

        ("e4", "e4"),

        ("e6", "e6"),

        ("other", "Другая модель"),

    ],

    "star-ev": [

        ("classic", "Classic"),

        ("capella", "Capella"),

        ("sirius", "Sirius"),

        ("other", "Другая модель"),

    ],

    "tomberlin": [

        ("e-merge", "E-Merge"),

        ("ss", "SS"),

        ("other", "Другая модель"),

    ],

    "lvtong": [

        ("lt-a627", "LT-A627"),

        ("lt-a2", "LT-A2"),

        ("other", "Другая модель"),

    ],

    "eagle-golf": [

        ("flx", "FLX"),

        ("champion", "Champion"),

        ("other", "Другая модель"),

    ],

    "other-golf-cart": [("other", "Другая модель")],

    "ninebot-other": [

        ("gokart-pro", "GoKart Pro"),

        ("me-pro", "me Pro"),

        ("drift-w1", "Drift W1"),

        ("other", "Другая модель"),

    ],

    "xiaomi-other": [

        ("ninebot-gokart", "Ninebot GoKart"),

        ("other", "Другая модель"),

    ],

    "segway-other": [

        ("gokart-kit", "GoKart Kit"),

        ("loomo", "Loomo"),

        ("other", "Другая модель"),

    ],

    "razor-other": [

        ("crazy-cart", "Crazy Cart"),

        ("ground-force", "Ground Force"),

        ("power-rider", "Power Rider"),

        ("other", "Другая модель"),

    ],

    "yadea-other": [

        ("c1s", "C1S"),

        ("g5", "G5"),

        ("other", "Другая модель"),

    ],

    "electro-other": [

        ("city", "City"),

        ("pro", "Pro"),

        ("cargo", "Cargo"),

        ("other", "Другая модель"),

    ],

    "other-other-electric": [("other", "Другая модель")],

}



# Display aliases (canonical brand slug → alias strings). Seeded if table exists.

ELECTRIC_BRAND_ALIASES: list[tuple[str, str]] = [

    ("surron", "Surron"),

    ("surron", "Sur Ron"),

    ("gotway", "Gotway"),

    ("gotway", "Begode"),

    ("dualtron", "Minimotors Dualtron"),

    ("minimotors", "Dualtron Minimotors"),

    ("zero-emotorcycle", "Zero Motorcycles"),

]


