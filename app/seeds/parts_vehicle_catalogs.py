"""Brand/model SoT for non-passenger parts applicability catalogs.

Each brand slug is globally unique. When a marque already exists as a car/truck
row, use a type-suffixed slug and keep the public display name.
"""
from __future__ import annotations

from app.models.category_enums import VehicleType

# (slug, name, country, vehicle_type)
PARTS_CATALOG_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    # --- Buses ---
    ("paz", "ПАЗ", "Russia", VehicleType.bus),
    ("liaz", "ЛиАЗ", "Russia", VehicleType.bus),
    ("nefaz-buses", "НефАЗ", "Russia", VehicleType.bus),
    ("maz-buses", "МАЗ", "Belarus", VehicleType.bus),
    ("mercedes-benz-buses", "Mercedes-Benz", "Germany", VehicleType.bus),
    ("hyundai-buses", "Hyundai", "Korea", VehicleType.bus),
    ("yutong", "Yutong", "China", VehicleType.bus),
    ("king-long", "King Long", "China", VehicleType.bus),
    ("higer", "Higer", "China", VehicleType.bus),
    ("volvo-buses", "Volvo Buses", "Sweden", VehicleType.bus),
    ("man-buses", "MAN", "Germany", VehicleType.bus),
    ("iveco-buses", "Iveco Bus", "Italy", VehicleType.bus),
    ("gaz-buses", "ГАЗ", "Russia", VehicleType.bus),
    ("foton-buses", "Foton", "China", VehicleType.bus),
    ("daewoo-buses", "Daewoo", "Korea", VehicleType.bus),
    ("zhongtong", "Zhongtong", "China", VehicleType.bus),
    ("golden-dragon", "Golden Dragon", "China", VehicleType.bus),
    ("setra", "Setra", "Germany", VehicleType.bus),
    ("daf-buses", "DAF", "Netherlands", VehicleType.bus),
    ("kamaz-buses", "KamAZ", "Russia", VehicleType.bus),
    # --- Special equipment (expand beyond Cat/JCB/Komatsu) ---
    ("hitachi-ce", "Hitachi", "Japan", VehicleType.special),
    ("volvo-ce", "Volvo CE", "Sweden", VehicleType.special),
    ("liebherr", "Liebherr", "Germany", VehicleType.special),
    ("xcmg", "XCMG", "China", VehicleType.special),
    ("sany", "SANY", "China", VehicleType.special),
    ("zoomlion", "Zoomlion", "China", VehicleType.special),
    ("case-ce", "CASE", "USA", VehicleType.special),
    ("doosan", "Doosan", "Korea", VehicleType.special),
    ("bobcat", "Bobcat", "USA", VehicleType.special),
    ("hyundai-ce", "Hyundai CE", "Korea", VehicleType.special),
    ("shantui", "Shantui", "China", VehicleType.special),
    ("lovol", "Lovol", "China", VehicleType.special),
    # --- Agricultural ---
    ("mtz-belarus", "МТЗ Belarus", "Belarus", VehicleType.agricultural),
    ("john-deere", "John Deere", "USA", VehicleType.agricultural),
    ("case-ih", "Case IH", "USA", VehicleType.agricultural),
    ("new-holland", "New Holland", "Italy", VehicleType.agricultural),
    ("claas", "CLAAS", "Germany", VehicleType.agricultural),
    ("rostselmash", "Ростсельмаш", "Russia", VehicleType.agricultural),
    ("kubota", "Kubota", "Japan", VehicleType.agricultural),
    ("mahindra-agri", "Mahindra", "India", VehicleType.agricultural),
    ("yanmar-agri", "Yanmar", "Japan", VehicleType.agricultural),
    ("deutz-fahr", "DEUTZ-FAHR", "Germany", VehicleType.agricultural),
    ("fendt", "Fendt", "Germany", VehicleType.agricultural),
    ("kirovets", "Кировец", "Russia", VehicleType.agricultural),
    ("amkodor", "Амкодор", "Belarus", VehicleType.agricultural),
    ("yto-agri", "YTO (ЮТО)", "China", VehicleType.agricultural),
    ("lovol-agri", "Lovol", "China", VehicleType.agricultural),
    ("foton-agri", "Foton", "China", VehicleType.agricultural),
    ("zoomlion-agri", "Zoomlion", "China", VehicleType.agricultural),
    ("yumz-agri", "ЮМЗ", "Ukraine", VehicleType.agricultural),
    ("xtz-agri", "ХТЗ", "Ukraine", VehicleType.agricultural),
    ("gomselmash-agri", "Гомсельмаш", "Belarus", VehicleType.agricultural),
    ("dji-agras-parts", "DJI Agras", "China", VehicleType.agricultural),
    ("xag-parts", "XAG", "China", VehicleType.agricultural),
    # --- Motorcycles / moto ---
    ("honda-moto", "Honda", "Japan", VehicleType.motorcycle),
    ("yamaha", "Yamaha", "Japan", VehicleType.motorcycle),
    ("suzuki-moto", "Suzuki", "Japan", VehicleType.motorcycle),
    ("kawasaki", "Kawasaki", "Japan", VehicleType.motorcycle),
    ("bmw-motorrad", "BMW Motorrad", "Germany", VehicleType.motorcycle),
    ("ktm", "KTM", "Austria", VehicleType.motorcycle),
    ("harley-davidson", "Harley-Davidson", "USA", VehicleType.motorcycle),
    ("ducati", "Ducati", "Italy", VehicleType.motorcycle),
    ("royal-enfield", "Royal Enfield", "India", VehicleType.motorcycle),
    ("bajaj", "Bajaj", "India", VehicleType.motorcycle),
    ("cfmoto", "CFMoto", "China", VehicleType.motorcycle),
    ("husqvarna-moto", "Husqvarna", "Sweden", VehicleType.motorcycle),
    ("ural-moto", "Ural", "Russia", VehicleType.motorcycle),
    ("triumph", "Triumph", "UK", VehicleType.motorcycle),
    ("aprilia", "Aprilia", "Italy", VehicleType.motorcycle),
    # KG / CIS motorcycle market (pitbike, enduro, classic)
    ("alpha-moto", "Alpha", "China", VehicleType.motorcycle),
    ("motoland-moto", "Motoland", "Russia", VehicleType.motorcycle),
    ("irbis-moto", "Irbis", "Russia", VehicleType.motorcycle),
    ("racer-moto", "Racer", "China", VehicleType.motorcycle),
    ("stels-moto", "Stels", "Russia", VehicleType.motorcycle),
    ("lifan-moto", "Lifan", "China", VehicleType.motorcycle),
    ("zongshen", "Zongshen", "China", VehicleType.motorcycle),
    ("loncin-moto", "Loncin", "China", VehicleType.motorcycle),
    ("skygo", "Skygo", "China", VehicleType.motorcycle),
    ("regulmoto", "Regulmoto", "Russia", VehicleType.motorcycle),
    ("bse", "BSE", "China", VehicleType.motorcycle),
    ("kayo", "Kayo", "China", VehicleType.motorcycle),
    ("progasi", "Progasi", "Russia", VehicleType.motorcycle),
    ("spark-moto", "Spark", "China", VehicleType.motorcycle),
    ("hors", "Hors", "Russia", VehicleType.motorcycle),
    ("ij-moto", "Иж", "Russia", VehicleType.motorcycle),
    ("minsk-moto", "Минск", "Belarus", VehicleType.motorcycle),
    ("voskhod", "Восход", "Russia", VehicleType.motorcycle),
    # --- Electric micromobility ---
    ("ninebot", "Ninebot", "China", VehicleType.electric),
    ("xiaomi-mobility", "Xiaomi", "China", VehicleType.electric),
    ("yadea", "Yadea", "China", VehicleType.electric),
    ("sunra", "Sunra", "China", VehicleType.electric),
    ("kugoo", "Kugoo", "China", VehicleType.electric),
    ("ultron", "Ultron", "China", VehicleType.electric),
    ("electro", "Electro", None, VehicleType.electric),
    ("zero-motorcycles", "Zero", "USA", VehicleType.electric),
    ("segway", "Segway", "China", VehicleType.electric),
    ("razor", "Razor", "USA", VehicleType.electric),
    # --- Bicycles ---
    ("trek", "Trek", "USA", VehicleType.bicycle),
    ("giant", "Giant", "Taiwan", VehicleType.bicycle),
    ("specialized", "Specialized", "USA", VehicleType.bicycle),
    ("merida", "Merida", "Taiwan", VehicleType.bicycle),
    ("canyon", "Canyon", "Germany", VehicleType.bicycle),
    ("cube", "CUBE", "Germany", VehicleType.bicycle),
    ("scott-bikes", "Scott", "Switzerland", VehicleType.bicycle),
    ("cannondale", "Cannondale", "USA", VehicleType.bicycle),
    ("author", "Author", "Czech", VehicleType.bicycle),
    ("stels", "Stels", "Russia", VehicleType.bicycle),
    ("forward", "Forward", "Russia", VehicleType.bicycle),
    ("stern", "Stern", "Russia", VehicleType.bicycle),
    ("gt-bicycles", "GT", "USA", VehicleType.bicycle),
    ("format-bicycles", "Format", "Russia", VehicleType.bicycle),
    ("aspect-bicycles", "Aspect", "Russia", VehicleType.bicycle),
    ("gestalt-bicycles", "Gestalt", "KG", VehicleType.bicycle),
    ("pride-bicycles", "Pride", "Ukraine", VehicleType.bicycle),
    ("himo-parts", "Himo", "China", VehicleType.bicycle),
    ("xiaomi-bicycles", "Xiaomi", "China", VehicleType.bicycle),
    ("brompton-parts", "Brompton", "UK", VehicleType.bicycle),
    ("novatrack-parts", "Novatrack", "Russia", VehicleType.bicycle),
    # --- Watercraft ---
    ("yamaha-marine", "Yamaha Marine", "Japan", VehicleType.watercraft),
    ("suzuki-marine", "Suzuki Marine", "Japan", VehicleType.watercraft),
    ("honda-marine", "Honda Marine", "Japan", VehicleType.watercraft),
    ("mercury", "Mercury", "USA", VehicleType.watercraft),
    ("volvo-penta", "Volvo Penta", "Sweden", VehicleType.watercraft),
    ("brp-sea-doo", "Sea-Doo", "Canada", VehicleType.watercraft),
    ("kawasaki-marine", "Kawasaki Marine", "Japan", VehicleType.watercraft),
    ("bayliner", "Bayliner", "USA", VehicleType.watercraft),
    ("searay", "Sea Ray", "USA", VehicleType.watercraft),
    ("quicksilver", "Quicksilver", "Belgium", VehicleType.watercraft),
    # --- Trailers ---
    ("schmitz", "Schmitz Cargobull", "Germany", VehicleType.trailer),
    ("krone", "Krone", "Germany", VehicleType.trailer),
    ("wielton", "Wielton", "Poland", VehicleType.trailer),
    ("koegel", "Kögel", "Germany", VehicleType.trailer),
    ("tonar", "Тонар", "Russia", VehicleType.trailer),
    ("nefaz-trailers", "НефАЗ", "Russia", VehicleType.trailer),
    ("maz-trailers", "МАЗ", "Belarus", VehicleType.trailer),
    ("chmzap", "ЧМЗАП", "Russia", VehicleType.trailer),
    ("sessu", "Sesu", None, VehicleType.trailer),
    ("schwarzmueller", "Schwarzmüller", "Austria", VehicleType.trailer),
]

# brand_slug → [(model_slug, model_name), ...]
PARTS_CATALOG_MODELS: dict[str, list[tuple[str, str]]] = {
    # Buses
    "paz": [
        ("3205", "3205"),
        ("3204", "3204"),
        ("32053", "32053"),
        ("4234", "4234"),
        ("vector-next", "Vector Next"),
    ],
    "liaz": [
        ("5256", "5256"),
        ("5292", "5292"),
        ("6213", "6213"),
        ("4292", "4292"),
    ],
    "nefaz-buses": [
        ("5299", "5299"),
        ("42299", "42299"),
    ],
    "maz-buses": [
        ("103", "103"),
        ("203", "203"),
        ("206", "206"),
        ("215", "215"),
    ],
    "mercedes-benz-buses": [
        ("citaro", "Citaro"),
        ("intouro", "Intouro"),
        ("tourismo", "Tourismo"),
        ("sprinter-city", "Sprinter City"),
    ],
    "hyundai-buses": [
        ("county", "County"),
        ("universe", "Universe"),
        ("super-aero-city", "Super Aero City"),
    ],
    "yutong": [
        ("zk6122", "ZK6122"),
        ("zk6852", "ZK6852"),
        ("zk6107", "ZK6107"),
    ],
    "king-long": [
        ("xmq6127", "XMQ6127"),
        ("xmq6900", "XMQ6900"),
    ],
    "higer": [
        ("klq6129", "KLQ6129"),
        ("klq6891", "KLQ6891"),
    ],
    "volvo-buses": [
        ("9700", "9700"),
        ("9900", "9900"),
        ("b8r", "B8R"),
    ],
    "man-buses": [
        ("lion-city", "Lion's City"),
        ("lion-coach", "Lion's Coach"),
    ],
    "iveco-buses": [
        ("crossway", "Crossway"),
        ("urbanway", "Urbanway"),
        ("evadys", "Evadys"),
    ],
    "gaz-buses": [
        ("vector-next", "Vector Next"),
        ("city", "City"),
        ("gazelle-next-bus", "Газель Next автобус"),
    ],
    "foton-buses": [
        ("view", "View"),
        ("toano", "Toano"),
        ("auv", "AUV"),
    ],
    "daewoo-buses": [
        ("bs106", "BS106"),
        ("bx212", "BX212"),
        ("lesta", "Lesta"),
    ],
    "zhongtong": [
        ("lck6125", "LCK6125"),
        ("lck6105", "LCK6105"),
        ("lck6860", "LCK6860"),
    ],
    "golden-dragon": [
        ("xml6125", "XML6125"),
        ("xml6907", "XML6907"),
        ("xml6700", "XML6700"),
    ],
    "setra": [
        ("s415", "S 415"),
        ("s516", "S 516"),
        ("s531", "S 531"),
    ],
    "daf-buses": [
        ("sb3000", "SB3000"),
        ("mb200", "MB200"),
        ("chassis", "Chassis"),
    ],
    "kamaz-buses": [
        ("5297", "5297"),
        ("4238", "4238"),
        ("4308-bus", "4308"),
    ],
    # Special — existing brands + new
    "caterpillar": [
        ("320", "320"),
        ("336", "336"),
        ("950", "950"),
        ("d6", "D6"),
        ("140m", "140M"),
    ],
    "jcb": [
        ("3cx", "3CX"),
        ("4cx", "4CX"),
        ("js200", "JS200"),
        ("531-70", "531-70"),
    ],
    "komatsu": [
        ("pc200", "PC200"),
        ("pc300", "PC300"),
        ("wa320", "WA320"),
        ("d65", "D65"),
    ],
    "hitachi-ce": [
        ("zx200", "ZX200"),
        ("zx330", "ZX330"),
        ("zw180", "ZW180"),
    ],
    "volvo-ce": [
        ("ec210", "EC210"),
        ("ec300", "EC300"),
        ("l120", "L120"),
    ],
    "liebherr": [
        ("r926", "R 926"),
        ("l550", "L 550"),
        ("pr736", "PR 736"),
    ],
    "xcmg": [
        ("xe215c", "XE215C"),
        ("lw500fn", "LW500FN"),
        ("xs163", "XS163"),
    ],
    "sany": [
        ("sy215c", "SY215C"),
        ("sy365h", "SY365H"),
        ("sw405k", "SW405K"),
    ],
    "zoomlion": [
        ("ze215e", "ZE215E"),
        ("ze360e", "ZE360E"),
    ],
    "case-ce": [
        ("cx210", "CX210"),
        ("580n", "580N"),
        ("821g", "821G"),
    ],
    "doosan": [
        ("dx225", "DX225"),
        ("dx300", "DX300"),
        ("dl250", "DL250"),
    ],
    "bobcat": [
        ("s650", "S650"),
        ("t770", "T770"),
        ("e85", "E85"),
    ],
    "hyundai-ce": [
        ("r210", "R210"),
        ("r320", "R320"),
        ("hl757", "HL757"),
    ],
    "shantui": [
        ("sd16", "SD16"),
        ("sd22", "SD22"),
        ("sl50w", "SL50W"),
    ],
    "lovol": [
        ("fr220", "FR220"),
        ("fl956h", "FL956H"),
    ],
    # Agricultural
    "mtz-belarus": [
        ("82-1", "82.1"),
        ("892", "892"),
        ("1221", "1221"),
        ("1523", "1523"),
        ("3522", "3522"),
    ],
    "john-deere": [
        ("6m", "6M"),
        ("6r", "6R"),
        ("8r", "8R"),
        ("s780", "S780"),
    ],
    "case-ih": [
        ("puma", "Puma"),
        ("magnum", "Magnum"),
        ("axial-flow", "Axial-Flow"),
    ],
    "new-holland": [
        ("t6", "T6"),
        ("t7", "T7"),
        ("cr", "CR"),
    ],
    "claas": [
        ("arion", "Arion"),
        ("axion", "Axion"),
        ("lexion", "LEXION"),
    ],
    "rostselmash": [
        ("rsm-2375", "RSM 2375"),
        ("acros", "ACROS"),
        ("torum", "TORUM"),
        ("nova", "NOVA"),
    ],
    "kubota": [
        ("m7040", "M7040"),
        ("m8540", "M8540"),
        ("l3901", "L3901"),
    ],
    "mahindra-agri": [
        ("575", "575"),
        ("605", "605"),
        ("arjun", "Arjun"),
    ],
    "yanmar-agri": [
        ("ef494t", "EF494T"),
        ("ym357a", "YM357A"),
    ],
    "deutz-fahr": [
        ("5115", "5115"),
        ("6165", "6165"),
        ("7250", "7250"),
    ],
    "fendt": [
        ("700", "700 Vario"),
        ("900", "900 Vario"),
        ("1000", "1000 Vario"),
    ],
    "kirovets": [
        ("k-744", "К-744"),
        ("k-7m", "К-7М"),
    ],
    "amkodor": [
        ("352", "352"),
        ("527", "527"),
        ("211", "211"),
    ],
    "yto-agri": [
        ("x904", "X904"),
        ("x1204", "X1204"),
        ("nlx1054", "NLX1054"),
    ],
    "lovol-agri": [
        ("tb504", "TB504"),
        ("tb754", "TB754"),
        ("te244", "TE244"),
    ],
    "foton-agri": [
        ("tb504", "TB504"),
        ("ft824", "FT824"),
        ("ft1004", "FT1004"),
    ],
    "zoomlion-agri": [
        ("rs1304", "RS1304"),
        ("rn1104", "RN1104"),
    ],
    "yumz-agri": [
        ("6kl", "6КЛ"),
        ("8040", "8040"),
    ],
    "xtz-agri": [
        ("t-150", "Т-150"),
        ("t-150k", "Т-150К"),
    ],
    "gomselmash-agri": [
        ("palesse-gs12", "PALESSE GS12"),
        ("kzs-1218", "КЗС-1218"),
    ],
    "dji-agras-parts": [
        ("t40", "T40"),
        ("t50", "T50"),
        ("t25", "T25"),
    ],
    "xag-parts": [
        ("p100", "P100"),
        ("v40", "V40"),
    ],
    # Moto
    "honda-moto": [
        ("cbr600rr", "CBR600RR"),
        ("cbr1000rr", "CBR1000RR"),
        ("cb500x", "CB500X"),
        ("africa-twin", "Africa Twin"),
        ("pcx", "PCX"),
        ("dio", "Dio"),
    ],
    "yamaha": [
        ("yzf-r1", "YZF-R1"),
        ("yzf-r6", "YZF-R6"),
        ("mt-07", "MT-07"),
        ("mt-09", "MT-09"),
        ("nmax", "NMAX"),
        ("jog", "Jog"),
    ],
    "suzuki-moto": [
        ("gsx-r600", "GSX-R600"),
        ("gsx-r1000", "GSX-R1000"),
        ("v-strom", "V-Strom"),
        ("address", "Address"),
    ],
    "kawasaki": [
        ("ninja-650", "Ninja 650"),
        ("ninja-zx-10r", "Ninja ZX-10R"),
        ("z900", "Z900"),
        ("versys", "Versys"),
    ],
    "bmw-motorrad": [
        ("r1250gs", "R 1250 GS"),
        ("s1000rr", "S 1000 RR"),
        ("f850gs", "F 850 GS"),
    ],
    "ktm": [
        ("390-duke", "390 Duke"),
        ("790-adventure", "790 Adventure"),
        ("1290-super-duke", "1290 Super Duke"),
    ],
    "harley-davidson": [
        ("sportster", "Sportster"),
        ("street-glide", "Street Glide"),
        ("fat-boy", "Fat Boy"),
    ],
    "ducati": [
        ("panigale-v4", "Panigale V4"),
        ("monster", "Monster"),
        ("multistrada", "Multistrada"),
    ],
    "royal-enfield": [
        ("classic-350", "Classic 350"),
        ("himalayan", "Himalayan"),
        ("interceptor-650", "Interceptor 650"),
    ],
    "bajaj": [
        ("pulsar", "Pulsar"),
        ("dominar", "Dominar"),
        ("avenger", "Avenger"),
    ],
    "cfmoto": [
        ("300nk", "300NK"),
        ("650mt", "650MT"),
        ("800mt", "800MT"),
    ],
    "husqvarna-moto": [
        ("vitpilen-401", "Vitpilen 401"),
        ("svartpilen-401", "Svartpilen 401"),
        ("norden-901", "Norden 901"),
    ],
    "ural-moto": [
        ("gear-up", "Gear Up"),
        ("ct", "cT"),
        ("patrol", "Patrol"),
    ],
    "triumph": [
        ("street-triple", "Street Triple"),
        ("tiger-900", "Tiger 900"),
        ("bonneville", "Bonneville"),
    ],
    "aprilia": [
        ("rs-660", "RS 660"),
        ("tuono-660", "Tuono 660"),
        ("rsv4", "RSV4"),
    ],
    "alpha-moto": [
        ("rx", "RX"),
        ("rs", "RS"),
        ("alpha-125", "Alpha 125"),
        ("alpha-110", "Alpha 110"),
    ],
    "motoland-moto": [
        ("xr250", "XR250"),
        ("enduro-250", "Enduro 250"),
        ("apollo", "Apollo"),
        ("gazelle", "Gazelle"),
    ],
    "irbis-moto": [
        ("ttr-250", "TTR 250"),
        ("xr250r", "XR250R"),
        ("intruder", "Intruder"),
    ],
    "racer-moto": [
        ("rc250", "RC250"),
        ("enduro", "Enduro"),
        ("pitbike", "Pitbike"),
        ("fighter", "Fighter"),
    ],
    "stels-moto": [
        ("enduro-250", "Enduro 250"),
        ("trigger", "Trigger"),
        ("flex", "Flex"),
    ],
    "lifan-moto": [
        ("kp150", "KP150"),
        ("kpr200", "KPR200"),
        ("lf200", "LF200"),
    ],
    "zongshen": [
        ("zs125", "ZS125"),
        ("zs200", "ZS200"),
        ("zs250", "ZS250"),
    ],
    "loncin-moto": [
        ("lx200", "LX200"),
        ("lx250", "LX250"),
        ("gp150", "GP150"),
    ],
    "skygo": [
        ("sg125", "SG125"),
        ("sg150", "SG150"),
        ("king", "King"),
    ],
    "regulmoto": [
        ("sport-003", "Sport-003"),
        ("zr", "ZR"),
        ("five", "Five"),
    ],
    "bse": [
        ("z1", "Z1"),
        ("z3", "Z3"),
        ("z5", "Z5"),
        ("m2", "M2"),
    ],
    "kayo": [
        ("t2", "T2"),
        ("k2", "K2"),
        ("basic", "Basic"),
        ("classic", "Classic"),
    ],
    "progasi": [
        ("super-max", "Super Max"),
        ("palm", "Palm"),
        ("race", "Race"),
    ],
    "spark-moto": [
        ("sp200", "SP200"),
        ("sp250", "SP250"),
        ("enduro", "Enduro"),
    ],
    "hors": [
        ("051", "051"),
        ("054", "054"),
        ("enduro", "Enduro"),
    ],
    "ij-moto": [
        ("planeta-5", "Планета 5"),
        ("yupiter-5", "Юпитер 5"),
        ("junker", "Junker"),
    ],
    "minsk-moto": [
        ("c4-200", "C4 200"),
        ("d4-125", "D4 125"),
        ("x250", "X250"),
    ],
    "voskhod": [
        ("3m", "3М"),
        ("sokil", "Сокол"),
    ],
    # Electric
    "ninebot": [
        ("max-g30", "Max G30"),
        ("f2-pro", "F2 Pro"),
        ("kickscooter-e2", "KickScooter E2"),
    ],
    "xiaomi-mobility": [
        ("electric-scooter-4-pro", "Electric Scooter 4 Pro"),
        ("electric-scooter-3", "Electric Scooter 3"),
    ],
    "yadea": [
        ("g5", "G5"),
        ("keeness", "Keeness"),
        ("c1s", "C1S"),
    ],
    "sunra": [
        ("miku-max", "Miku Max"),
        ("robo-s", "Robo-S"),
    ],
    "kugoo": [
        ("m4-pro", "M4 Pro"),
        ("g2-pro", "G2 Pro"),
        ("kirin-s1", "Kirin S1"),
    ],
    "ultron": [
        ("t128", "T128"),
        ("t10", "T10"),
    ],
    "electro": [
        ("city", "City"),
        ("pro", "Pro"),
    ],
    "zero-motorcycles": [
        ("sr-f", "SR/F"),
        ("dsr-x", "DSR/X"),
        ("fxe", "FXE"),
    ],
    "segway": [
        ("ninebot-max", "Ninebot Max"),
        ("gt2", "GT2"),
    ],
    "razor": [
        ("e300", "E300"),
        ("crazy-cart", "Crazy Cart"),
    ],
    # Bicycles
    "trek": [
        ("marlin", "Marlin"),
        ("domane", "Domane"),
        ("fuel-ex", "Fuel EX"),
        ("slash", "Slash"),
    ],
    "giant": [
        ("talon", "Talon"),
        ("trance", "Trance"),
        ("tcr", "TCR"),
        ("escape", "Escape"),
    ],
    "specialized": [
        ("rockhopper", "Rockhopper"),
        ("stumpjumper", "Stumpjumper"),
        ("tarmac", "Tarmac"),
        ("sirrus", "Sirrus"),
    ],
    "merida": [
        ("big-nine", "Big.Nine"),
        ("big-seven", "Big.Seven"),
        ("scultura", "Scultura"),
    ],
    "canyon": [
        ("grand-canyon", "Grand Canyon"),
        ("ultimate", "Ultimate"),
        ("spectral", "Spectral"),
    ],
    "cube": [
        ("aim", "Aim"),
        ("reaction", "Reaction"),
        ("agree", "Agree"),
    ],
    "scott-bikes": [
        ("scale", "Scale"),
        ("spark", "Spark"),
        ("addict", "Addict"),
    ],
    "cannondale": [
        ("trail", "Trail"),
        ("synapse", "Synapse"),
        ("habit", "Habit"),
    ],
    "author": [
        ("impulse", "Impulse"),
        ("solution", "Solution"),
        ("era", "Era"),
    ],
    "stels": [
        ("navigator", "Navigator"),
        ("miss", "Miss"),
        ("pilot", "Pilot"),
    ],
    "forward": [
        ("apache", "Apache"),
        ("racing", "Racing"),
        ("unit", "Unit"),
    ],
    "stern": [
        ("energy", "Energy"),
        ("motion", "Motion"),
        ("dynamic", "Dynamic"),
    ],
    "gt-bicycles": [
        ("aggressor", "Aggressor"),
        ("avalanche", "Avalanche"),
        ("grade", "Grade"),
    ],
    "format-bicycles": [
        ("1212", "1212"),
        ("1412", "1412"),
        ("5342", "5342"),
    ],
    "aspect-bicycles": [
        ("nickel", "Nickel"),
        ("ideal", "Ideal"),
        ("spark", "Spark"),
    ],
    "gestalt-bicycles": [
        ("mtb", "MTB"),
        ("city", "City"),
        ("teen", "Teen"),
    ],
    "pride-bicycles": [
        ("marvel", "Marvel"),
        ("rocco", "Rocco"),
        ("quadro", "Quadro"),
    ],
    "himo-parts": [
        ("c20", "C20"),
        ("c26", "C26"),
        ("z20", "Z20"),
    ],
    "xiaomi-bicycles": [
        ("qiycle", "Qicycle"),
        ("himo", "Himo"),
        ("folding", "Folding"),
    ],
    "brompton-parts": [
        ("c-line", "C Line"),
        ("p-line", "P Line"),
        ("t-line", "T Line"),
    ],
    "novatrack-parts": [
        ("astra", "Astra"),
        ("vector", "Vector"),
        ("flyer", "Flyer"),
    ],
    # Watercraft
    "yamaha-marine": [
        ("f60", "F60"),
        ("f115", "F115"),
        ("f150", "F150"),
        ("vx", "VX"),
    ],
    "suzuki-marine": [
        ("df60", "DF60"),
        ("df115", "DF115"),
        ("df140", "DF140"),
    ],
    "honda-marine": [
        ("bf60", "BF60"),
        ("bf90", "BF90"),
        ("bf115", "BF115"),
    ],
    "mercury": [
        ("60-efi", "60 EFI"),
        ("115-efi", "115 EFI"),
        ("150-pro-xs", "150 Pro XS"),
    ],
    "volvo-penta": [
        ("d3", "D3"),
        ("d4", "D4"),
        ("d6", "D6"),
    ],
    "brp-sea-doo": [
        ("gti", "GTI"),
        ("rxp-x", "RXP-X"),
        ("spark", "Spark"),
    ],
    "kawasaki-marine": [
        ("ultra-310", "Ultra 310"),
        ("stx-160", "STX 160"),
    ],
    "bayliner": [
        ("element", "Element"),
        ("vr5", "VR5"),
        ("trophy", "Trophy"),
    ],
    "searay": [
        ("spx-190", "SPX 190"),
        ("sdx-250", "SDX 250"),
        ("sundancer", "Sundancer"),
    ],
    "quicksilver": [
        ("activ-555", "Activ 555"),
        ("activ-675", "Activ 675"),
    ],
    # Trailers
    "schmitz": [
        ("scb-s3b", "SCB*S3B"),
        ("scb-s3t", "SCB*S3T"),
        ("cargobull", "Cargobull"),
    ],
    "krone": [
        ("profi-liner", "Profi Liner"),
        ("cool-liner", "Cool Liner"),
        ("mega-liner", "Mega Liner"),
    ],
    "wielton": [
        ("ns3", "NS3"),
        ("ns34", "NS34"),
        ("pw", "PW"),
    ],
    "koegel": [
        ("cargo", "Cargo"),
        ("lightplus", "Lightplus"),
    ],
    "tonar": [
        ("9746", "9746"),
        ("9523", "9523"),
        ("9888", "9888"),
    ],
    "nefaz-trailers": [
        ("9334", "9334"),
        ("96894", "96894"),
    ],
    "maz-trailers": [
        ("9758", "9758"),
        ("93866", "93866"),
    ],
    "chmzap": [
        ("99064", "99064"),
        ("83881", "83881"),
    ],
    "sessu": [
        ("cargo", "Cargo"),
        ("dump", "Dump"),
    ],
    "schwarzmueller": [
        ("spa", "SPA"),
        ("3a", "3-Achs"),
    ],
}

# Extra truck OEMs for cargo parts (unique slugs; display names may match sale).
CARGO_PARTS_TRUCK_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    ("howo", "Howo", "China", VehicleType.truck),
    ("shacman", "Shacman", "China", VehicleType.truck),
    ("faw-trucks", "FAW", "China", VehicleType.truck),
    ("hino", "Hino", "Japan", VehicleType.truck),
    ("foton-trucks", "Foton", "China", VehicleType.truck),
    ("jac-trucks", "JAC", "China", VehicleType.truck),
    ("daf", "DAF", "Netherlands", VehicleType.truck),
    ("renault-trucks", "Renault Trucks", "France", VehicleType.truck),
    ("mercedes-benz-trucks", "Mercedes-Benz Trucks", "Germany", VehicleType.truck),
    ("iveco-trucks", "Iveco Trucks", "Italy", VehicleType.truck),
]

# Passenger/SUV models wrongly attached to VehicleType.truck brands (disable).
TRUCK_PARTS_DISABLED_MODELS: dict[str, frozenset[str]] = {
    "isuzu": frozenset(
        {
            "amigo",
            "ascender",
            "axiom",
            "gemini",
            "mu",
            "mu-x",
            "rodeo",
            "trooper",
            "vehicross",
        }
    ),
    "dongfeng": frozenset(
        {
            "580",
            "a30",
            "aeolus-a60",
            "aeolus-ax7",
            "aeolus-e70",
            "aeolus-yixuan",
            "aeolus-yixuan-gs",
            "ax7",
            "h30",
            "mx3",
            "nammi",
            "s30",
            "shine",
            "t5-evo",
        }
    ),
}

# LCV models on existing car brands — shown in cargo_parts via execution policy.
CARGO_LCV_PARTS_MODELS: dict[str, list[tuple[str, str]]] = {
    "gaz": [
        ("gazelle", "Gazelle"),
        ("gazelle-next", "Газель Next"),
        ("gazelle-business", "Газель Бизнес"),
        ("sobol", "Sobol"),
        ("valdai-next", "Валдай Next"),
    ],
    "hyundai": [
        ("porter", "Porter"),
        ("porter-ii", "Porter II"),
        ("hd35", "HD35"),
        ("hd65", "HD65"),
        ("hd78", "HD78"),
    ],
    "kia": [
        ("bongo", "Bongo"),
        ("bongo-iii", "Bongo III"),
        ("k2500", "K2500"),
    ],
    "ford": [
        ("transit", "Transit"),
        ("transit-custom", "Transit Custom"),
    ],
    "mercedes-benz": [
        ("sprinter", "Sprinter"),
        ("atego", "Atego"),
    ],
    "toyota": [
        ("hiace", "Hiace"),
        ("dyna", "Dyna"),
    ],
    "iveco": [
        ("daily", "Daily"),
        ("eurocargo", "EuroCargo"),
    ],
    "fiat": [
        ("ducato", "Ducato"),
        ("doblo-cargo", "Doblo Cargo"),
    ],
    "citroen": [
        ("jumper", "Jumper"),
    ],
    "uaz": [
        ("profi", "Profi"),
    ],
}

# Truck models for cargo parts (brands already exist or in CARGO_PARTS_TRUCK_BRANDS).
TRUCK_CATALOG_MODELS: dict[str, list[tuple[str, str]]] = {
    "maz": [
        ("5440", "5440"),
        ("6312", "6312"),
        ("6501", "6501"),
        ("5551", "5551"),
        ("5336", "5336"),
        ("4371", "4371"),
    ],
    "ural": [
        ("4320", "4320"),
        ("5557", "5557"),
        ("6370", "6370"),
        ("next", "Next"),
    ],
    "man": [
        ("tgx", "TGX"),
        ("tgs", "TGS"),
        ("tgm", "TGM"),
        ("tgl", "TGL"),
    ],
    "scania": [
        ("r-series", "R-series"),
        ("s-series", "S-series"),
        ("g-series", "G-series"),
        ("p-series", "P-series"),
    ],
    "volvo-trucks": [
        ("fh", "FH"),
        ("fm", "FM"),
        ("fmx", "FMX"),
        ("fe", "FE"),
        ("fl", "FL"),
    ],
    "isuzu": [
        ("nqr", "NQR"),
        ("npr", "NPR"),
        ("elf", "Elf"),
        ("fvr", "FVR"),
        ("giga", "Giga"),
        ("d-max", "D-Max"),
    ],
    "dongfeng": [
        ("captain-t", "Captain-T"),
        ("kapitan", "Капитан"),
        ("kinland", "Kinland"),
        ("dfh", "DFH"),
        ("rich", "Rich"),
    ],
    "kamaz": [
        ("5490", "5490"),
        ("6520", "6520"),
        ("43118", "43118"),
        ("65115", "65115"),
        ("5350", "5350"),
        ("4308", "4308"),
        ("65117", "65117"),
        ("6580", "6580"),
    ],
    "howo": [
        ("a7", "A7"),
        ("t7h", "T7H"),
        ("t5g", "T5G"),
        ("sinotruk-6x4", "6x4"),
    ],
    "shacman": [
        ("f3000", "F3000"),
        ("x3000", "X3000"),
        ("h3000", "H3000"),
    ],
    "faw-trucks": [
        ("j6p", "J6P"),
        ("jh6", "JH6"),
        ("ca3250", "CA3250"),
    ],
    "hino": [
        ("300", "300"),
        ("500", "500"),
        ("700", "700"),
    ],
    "foton-trucks": [
        ("auman", "Auman"),
        ("ollin", "Ollin"),
        ("tunland", "Tunland"),
    ],
    "jac-trucks": [
        ("n56", "N56"),
        ("n75", "N75"),
        ("n120", "N120"),
        ("n200", "N200"),
    ],
    "daf": [
        ("xf", "XF"),
        ("cf", "CF"),
        ("lf", "LF"),
    ],
    "renault-trucks": [
        ("t-high", "T High"),
        ("c-series", "C"),
        ("d-series", "D"),
    ],
    "mercedes-benz-trucks": [
        ("actros", "Actros"),
        ("arocs", "Arocs"),
        ("atego", "Atego"),
        ("econic", "Econic"),
    ],
    "iveco-trucks": [
        ("stralis", "Stralis"),
        ("trakker", "Trakker"),
        ("eurocargo", "Eurocargo"),
        ("daily", "Daily"),
    ],
}
