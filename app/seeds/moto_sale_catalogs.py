"""Brand/model SoT for Mototechnika L1 sale subtypes.

Motorcycle brands live in parts_vehicle_catalogs (VehicleType.motorcycle).
This module covers the remaining Flutter L1 leaves.
"""
from __future__ import annotations

from app.models.category_enums import VehicleType

# (slug, name, country, vehicle_type)
MOTO_SALE_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    # Scooters / mopeds
    ("honda-scooter", "Honda", "Japan", VehicleType.scooter),
    ("yamaha-scooter", "Yamaha", "Japan", VehicleType.scooter),
    ("suzuki-scooter", "Suzuki", "Japan", VehicleType.scooter),
    ("vespa", "Vespa", "Italy", VehicleType.scooter),
    ("piaggio", "Piaggio", "Italy", VehicleType.scooter),
    ("sym", "SYM", "Taiwan", VehicleType.scooter),
    ("kymco", "KYMCO", "Taiwan", VehicleType.scooter),
    ("keeway", "Keeway", "China", VehicleType.scooter),
    ("lifan-scooter", "Lifan", "China", VehicleType.scooter),
    ("racer-scooter", "Racer", "China", VehicleType.scooter),
    ("stels-scooter", "Stels", "Russia", VehicleType.scooter),
    ("irbis-scooter", "Irbis", "Russia", VehicleType.scooter),
    ("vilimi", "Vilimi", "China", VehicleType.scooter),
    ("dawang", "Dawang", "China", VehicleType.scooter),
    ("tank-scooter", "Tank", "China", VehicleType.scooter),
    ("zhorgo", "Жорго", "Kyrgyzstan", VehicleType.scooter),
    ("fosti-scooter", "Fosti", "China", VehicleType.scooter),
    ("spark-scooter", "Spark", "China", VehicleType.scooter),
    # Motorollers / «Муравей» cargo scooters (Lalafo chip)
    ("muravey", "Муравей", "Russia", VehicleType.motoroller),
    ("tulitsa", "Тулица", "Russia", VehicleType.motoroller),
    ("vyatka", "Вятка", "Russia", VehicleType.motoroller),
    ("tula-motoroller", "Тула", "Russia", VehicleType.motoroller),
    ("racer-motoroller", "Racer", "China", VehicleType.motoroller),
    ("lifan-motoroller", "Lifan", "China", VehicleType.motoroller),
    ("dayun-motoroller", "Dayun", "China", VehicleType.motoroller),
    ("bashan-motoroller", "Bashan", "China", VehicleType.motoroller),
    # ATV
    ("cfmoto-atv", "CFMoto", "China", VehicleType.atv),
    ("polaris", "Polaris", "USA", VehicleType.atv),
    ("can-am", "Can-Am", "Canada", VehicleType.atv),
    ("yamaha-atv", "Yamaha", "Japan", VehicleType.atv),
    ("honda-atv", "Honda", "Japan", VehicleType.atv),
    ("kawasaki-atv", "Kawasaki", "Japan", VehicleType.atv),
    ("stels-atv", "Stels", "Russia", VehicleType.atv),
    ("hisun", "Hisun", "China", VehicleType.atv),
    ("linhai", "Linhai", "China", VehicleType.atv),
    ("russkaya-mehanika-atv", "Русская механика", "Russia", VehicleType.atv),
    # Buggy
    ("can-am-buggy", "Can-Am", "Canada", VehicleType.buggy),
    ("polaris-buggy", "Polaris", "USA", VehicleType.buggy),
    ("yamaha-buggy", "Yamaha", "Japan", VehicleType.buggy),
    ("arctic-cat-buggy", "Arctic Cat", "USA", VehicleType.buggy),
    ("joyner", "Joyner", "China", VehicleType.buggy),
    ("bashan-buggy", "Bashan", "China", VehicleType.buggy),
    ("hammerhead", "Hammerhead", "USA", VehicleType.buggy),
    # Tricycles
    ("lifan-tricycle", "Lifan", "China", VehicleType.tricycle),
    ("bajaj-tricycle", "Bajaj", "India", VehicleType.tricycle),
    ("dayun", "Dayun", "China", VehicleType.tricycle),
    ("jinbei-tricycle", "Jinbei", "China", VehicleType.tricycle),
    ("tongxin", "Tongxin", "China", VehicleType.tricycle),
    ("racer-tricycle", "Racer", "China", VehicleType.tricycle),
    # Snowmobiles
    ("ski-doo", "Ski-Doo", "Canada", VehicleType.snowmobile),
    ("yamaha-snow", "Yamaha", "Japan", VehicleType.snowmobile),
    ("polaris-snow", "Polaris", "USA", VehicleType.snowmobile),
    ("arctic-cat", "Arctic Cat", "USA", VehicleType.snowmobile),
    ("lynx", "Lynx", "Finland", VehicleType.snowmobile),
    ("tachyon", "Tachyon", None, VehicleType.snowmobile),
    # Karts
    ("tony-kart", "Tony Kart", "Italy", VehicleType.kart),
    ("crg", "CRG", "Italy", VehicleType.kart),
    ("birel-art", "Birel ART", "Italy", VehicleType.kart),
    ("sodikart", "Sodikart", "France", VehicleType.kart),
    ("exprit", "Exprit", "Italy", VehicleType.kart),
    ("kosmic", "Kosmic", "Italy", VehicleType.kart),
    # Other moto
    ("stels-other", "Stels", "Russia", VehicleType.other_moto),
    ("racer-other", "Racer", "China", VehicleType.other_moto),
    ("irbis-other", "Irbis", "Russia", VehicleType.other_moto),
    ("atom", "Atom", None, VehicleType.other_moto),
    ("motoland", "Motoland", "Russia", VehicleType.other_moto),
]

MOTO_SALE_MODELS: dict[str, list[tuple[str, str]]] = {
    "honda-scooter": [
        ("pcx", "PCX"),
        ("dio", "Dio"),
        ("lead", "Lead"),
        ("forza", "Forza"),
        ("vario", "Vario"),
        ("giorno", "Giorno"),
    ],
    "yamaha-scooter": [
        ("nmax", "NMAX"),
        ("xmax", "XMAX"),
        ("jog", "Jog"),
        ("aerox", "Aerox"),
        ("vino", "Vino"),
    ],
    "suzuki-scooter": [
        ("address", "Address"),
        ("lets", "Let's"),
        ("burgman", "Burgman"),
        ("sepia", "Sepia"),
    ],
    "vespa": [
        ("primavera", "Primavera"),
        ("sprint", "Sprint"),
        ("gts", "GTS"),
        ("lx", "LX"),
    ],
    "piaggio": [
        ("liberty", "Liberty"),
        ("beverly", "Beverly"),
        ("medley", "Medley"),
        ("fly", "Fly"),
    ],
    "sym": [
        ("orbit", "Orbit"),
        ("jet", "Jet"),
        ("fiddle", "Fiddle"),
        ("symphony", "Symphony"),
    ],
    "kymco": [
        ("agility", "Agility"),
        ("like", "Like"),
        ("people", "People"),
        ("super-8", "Super 8"),
    ],
    "keeway": [
        ("fact", "Fact"),
        ("hurricane", "Hurricane"),
        ("focus", "Focus"),
    ],
    "lifan-scooter": [
        ("lf50qt", "LF50QT"),
        ("lf150t", "LF150T"),
        ("kyo", "Kyo"),
    ],
    "racer-scooter": [
        ("meteor", "Meteor"),
        ("dragon", "Dragon"),
        ("rc50qt", "RC50QT"),
    ],
    "stels-scooter": [
        ("vortex", "Vortex"),
        ("tact", "Tact"),
        ("skif", "Skif"),
    ],
    "irbis-scooter": [
        ("nirvana", "Nirvana"),
        ("kaori", "Kaori"),
        ("z50r", "Z50R"),
    ],
    "vilimi": [
        ("v49", "V49"),
        ("v50", "V50"),
        ("city", "City"),
    ],
    "dawang": [
        ("dw49", "DW49"),
        ("dw50", "DW50"),
        ("dw125", "DW125"),
    ],
    "tank-scooter": [
        ("t50", "T50"),
        ("t125", "T125"),
        ("t150", "T150"),
    ],
    "zhorgo": [
        ("city", "City"),
        ("sport", "Sport"),
        ("cargo", "Cargo"),
    ],
    "fosti-scooter": [
        ("ft50", "FT50"),
        ("ft125", "FT125"),
    ],
    "spark-scooter": [
        ("sp50", "SP50"),
        ("sp125", "SP125"),
    ],
    "muravey": [
        ("tg200", "ТГ200"),
        ("tg250", "ТГ250"),
        ("2m02", "2М02"),
    ],
    "tulitsa": [
        ("t200", "Т200"),
        ("t250", "Т250"),
    ],
    "vyatka": [
        ("vp150", "ВП-150"),
        ("electron", "Электрон"),
    ],
    "tula-motoroller": [
        ("t200", "Т-200"),
        ("tmg", "ТМГ"),
    ],
    "racer-motoroller": [
        ("muravey-style", "Muravey"),
        ("rc200", "RC200"),
        ("cargo", "Cargo"),
    ],
    "lifan-motoroller": [
        ("lf200", "LF200"),
        ("lf250", "LF250"),
    ],
    "dayun-motoroller": [
        ("dy150", "DY150"),
        ("dy200", "DY200"),
    ],
    "bashan-motoroller": [
        ("bs150", "BS150"),
        ("bs200", "BS200"),
    ],
    "cfmoto-atv": [
        ("cforce-400", "CForce 400"),
        ("cforce-600", "CForce 600"),
        ("cforce-800", "CForce 800"),
        ("uforce", "UForce"),
    ],
    "polaris": [
        ("sportsman-450", "Sportsman 450"),
        ("sportsman-570", "Sportsman 570"),
        ("scrambler", "Scrambler"),
        ("outlaw", "Outlaw"),
    ],
    "can-am": [
        ("outlander", "Outlander"),
        ("renegade", "Renegade"),
        ("defender", "Defender"),
    ],
    "yamaha-atv": [
        ("grizzly", "Grizzly"),
        ("raptor", "Raptor"),
        ("kodiak", "Kodiak"),
    ],
    "honda-atv": [
        ("trx420", "TRX420"),
        ("trx520", "TRX520"),
        ("pioneer", "Pioneer"),
    ],
    "kawasaki-atv": [
        ("brute-force", "Brute Force"),
        ("teryx", "Teryx"),
    ],
    "stels-atv": [
        ("leopard", "Leopard"),
        ("guepard", "Guepard"),
        ("500h", "500H"),
    ],
    "hisun": [
        ("sector", "Sector"),
        ("strike", "Strike"),
        ("hs400", "HS400"),
    ],
    "linhai": [
        ("400", "400"),
        ("550", "550"),
        ("800", "800"),
    ],
    "russkaya-mehanika-atv": [
        ("rm-500", "RM 500"),
        ("rm-650", "RM 650"),
    ],
    "can-am-buggy": [
        ("maverick-x3", "Maverick X3"),
        ("maverick-sport", "Maverick Sport"),
        ("commander", "Commander"),
    ],
    "polaris-buggy": [
        ("rzr-pro", "RZR Pro"),
        ("rzr-xp", "RZR XP"),
        ("general", "General"),
    ],
    "yamaha-buggy": [
        ("yxz1000r", "YXZ1000R"),
        ("wolverine", "Wolverine"),
    ],
    "arctic-cat-buggy": [
        ("wildcat", "Wildcat"),
        ("prowler", "Prowler"),
    ],
    "joyner": [
        ("sand-viper", "Sand Viper"),
        ("trooper", "Trooper"),
    ],
    "bashan-buggy": [
        ("bs250", "BS250"),
        ("bs300", "BS300"),
    ],
    "hammerhead": [
        ("ggp", "GGP"),
        ("torpedo", "Torpedo"),
    ],
    "lifan-tricycle": [
        ("lf200zh", "LF200ZH"),
        ("lf250zh", "LF250ZH"),
    ],
    "bajaj-tricycle": [
        ("re", "RE"),
        ("maxima", "Maxima"),
    ],
    "dayun": [
        ("dy150", "DY150"),
        ("dy200", "DY200"),
    ],
    "jinbei-tricycle": [
        ("cargo", "Cargo"),
        ("passenger", "Passenger"),
    ],
    "tongxin": [
        ("tx200", "TX200"),
        ("tx250", "TX250"),
    ],
    "racer-tricycle": [
        ("rc200zh", "RC200ZH"),
        ("troyka", "Тройка"),
    ],
    "ski-doo": [
        ("summit", "Summit"),
        ("renegade", "Renegade"),
        ("expedition", "Expedition"),
        ("mxz", "MXZ"),
    ],
    "yamaha-snow": [
        ("sidewinder", "Sidewinder"),
        ("viking", "Viking"),
        ("srx", "SRX"),
    ],
    "polaris-snow": [
        ("rmk", "RMK"),
        ("switchback", "Switchback"),
        ("indy", "Indy"),
    ],
    "arctic-cat": [
        ("m8000", "M 8000"),
        ("zr", "ZR"),
        ("riot", "Riot"),
    ],
    "lynx": [
        ("rave", "Rave"),
        ("boondocker", "Boondocker"),
        ("commander", "Commander"),
    ],
    "tachyon": [
        ("sport", "Sport"),
        ("touring", "Touring"),
    ],
    "tony-kart": [
        ("racer-401", "Racer 401R"),
        ("rok", "ROK"),
        ("evo", "EVO"),
    ],
    "crg": [
        ("road-rebel", "Road Rebel"),
        ("hero", "Hero"),
        ("kt2", "KT2"),
    ],
    "birel-art": [
        ("ry30", "RY30"),
        ("c28", "C28"),
    ],
    "sodikart": [
        ("gt-race", "GT-Race"),
        ("sr4", "SR4"),
    ],
    "exprit": [
        ("rex", "Rex"),
        ("kairos", "Kairos"),
    ],
    "kosmic": [
        ("mercury", "Mercury"),
        ("lynx-kart", "Lynx"),
    ],
    "stels-other": [
        ("enduro", "Enduro"),
        ("cross", "Cross"),
        ("pitbike", "Pitbike"),
    ],
    "racer-other": [
        ("enduro", "Enduro"),
        ("pitbike", "Pitbike"),
        ("mini", "Mini"),
    ],
    "irbis-other": [
        ("ttr", "TTR"),
        ("xr", "XR"),
        ("dino", "Dino"),
    ],
    "atom": [
        ("cross", "Cross"),
        ("enduro", "Enduro"),
    ],
    "motoland": [
        ("xr250", "XR250"),
        ("enduro-250", "Enduro 250"),
        ("pitbike", "Pitbike"),
    ],
}
