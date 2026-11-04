"""Brand/model SoT for Farm Machinery L1 sale subtypes.

Parts agri brands live in parts_vehicle_catalogs (VehicleType.agricultural).
"""
from __future__ import annotations

from app.models.category_enums import VehicleType

# (slug, name, country, vehicle_type)
FARM_SALE_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    # Tractors (Lalafo KG chips + CIS/CN market)
    ("mtz-tractor", "МТЗ Belarus", "Belarus", VehicleType.tractor),
    ("john-deere-tractor", "John Deere", "USA", VehicleType.tractor),
    ("case-ih-tractor", "Case IH", "USA", VehicleType.tractor),
    ("new-holland-tractor", "New Holland", "Italy", VehicleType.tractor),
    ("claas-tractor", "CLAAS", "Germany", VehicleType.tractor),
    ("fendt-tractor", "Fendt", "Germany", VehicleType.tractor),
    ("kubota-tractor", "Kubota", "Japan", VehicleType.tractor),
    ("kirovets-tractor", "Кировец", "Russia", VehicleType.tractor),
    ("deutz-fahr-tractor", "DEUTZ-FAHR", "Germany", VehicleType.tractor),
    ("mahindra-tractor", "Mahindra", "India", VehicleType.tractor),
    ("yto-tractor", "YTO (ЮТО)", "China", VehicleType.tractor),
    ("yumz-tractor", "ЮМЗ", "Ukraine", VehicleType.tractor),
    ("xtz-tractor", "ХТЗ", "Ukraine", VehicleType.tractor),
    ("ltz-tractor", "ЛТЗ", "Russia", VehicleType.tractor),
    ("vtz-tractor", "ВТЗ", "Russia", VehicleType.tractor),
    # ВгТЗ owns DT-75 family (do NOT treat ДТ-75 as manufacturer).
    ("vgtz-tractor", "ВгТЗ", "Russia", VehicleType.tractor),
    ("lovol-tractor", "Lovol", "China", VehicleType.tractor),
    ("foton-tractor", "Foton", "China", VehicleType.tractor),
    ("zoomlion-tractor", "Zoomlion", "China", VehicleType.tractor),
    ("yanmar-tractor", "Yanmar", "Japan", VehicleType.tractor),
    ("dongfanghong-tractor", "Dongfanghong", "China", VehicleType.tractor),
    ("changfa-tractor", "Changfa", "China", VehicleType.tractor),
    ("weihe-tractor", "Weihe", "China", VehicleType.tractor),
    ("kasun-tractor", "KASUN", "China", VehicleType.tractor),
    ("yuki-tractor", "Yuki", "China", VehicleType.tractor),
    ("fm-world-tractor", "FM World", "China", VehicleType.tractor),
    # Shifeng — common Chinese compact tractor in CIS/KG dealer channels.
    ("shifeng-tractor", "Shifeng (Шифенг)", "China", VehicleType.tractor),
    # Mini-tractors
    ("kubota-mini", "Kubota", "Japan", VehicleType.mini_tractor),
    ("iseki-mini", "Iseki", "Japan", VehicleType.mini_tractor),
    ("yanmar-mini", "Yanmar", "Japan", VehicleType.mini_tractor),
    ("hinomoto-mini", "Hinomoto", "Japan", VehicleType.mini_tractor),
    ("xingtai-mini", "Xingtai", "China", VehicleType.mini_tractor),
    ("jinma-mini", "Jinma", "China", VehicleType.mini_tractor),
    ("scout-mini", "Scout", "Russia", VehicleType.mini_tractor),
    ("uralets-mini", "Уралец", "Russia", VehicleType.mini_tractor),
    ("mtz-mini", "МТЗ Belarus", "Belarus", VehicleType.mini_tractor),
    ("lovol-mini", "Lovol", "China", VehicleType.mini_tractor),
    ("solis-mini", "Solis", "India", VehicleType.mini_tractor),
    ("dongfeng-mini", "Dongfeng", "China", VehicleType.mini_tractor),
    ("shifeng-mini", "Shifeng (Шифенг)", "China", VehicleType.mini_tractor),
    # Walk-behind / cultivators
    ("neva", "Нева", "Russia", VehicleType.walk_behind),
    ("salyut", "Салют", "Russia", VehicleType.walk_behind),
    ("cascade", "Каскад", "Russia", VehicleType.walk_behind),
    ("celina", "Целина", "Russia", VehicleType.walk_behind),
    ("champion-wb", "Champion", "Russia", VehicleType.walk_behind),
    ("huter", "Huter", "Germany", VehicleType.walk_behind),
    ("patriot-wb", "Patriot", "USA", VehicleType.walk_behind),
    ("kubota-wb", "Kubota", "Japan", VehicleType.walk_behind),
    ("honda-wb", "Honda", "Japan", VehicleType.walk_behind),
    ("pubert", "Pubert", "France", VehicleType.walk_behind),
    ("rolf-wb", "ROLF", "China", VehicleType.walk_behind),
    ("lifan-wb", "Lifan", "China", VehicleType.walk_behind),
    ("forza-wb", "Forza", "China", VehicleType.walk_behind),
    # Combines
    ("rostselmash-combine", "Ростсельмаш", "Russia", VehicleType.combine),
    ("john-deere-combine", "John Deere", "USA", VehicleType.combine),
    ("claas-combine", "CLAAS", "Germany", VehicleType.combine),
    ("case-ih-combine", "Case IH", "USA", VehicleType.combine),
    ("new-holland-combine", "New Holland", "Italy", VehicleType.combine),
    ("gomselmash", "Гомсельмаш", "Belarus", VehicleType.combine),
    ("fendt-combine", "Fendt", "Germany", VehicleType.combine),
    ("sampo", "Sampo Rosenlew", "Finland", VehicleType.combine),
    ("lovol-combine", "Lovol", "China", VehicleType.combine),
    ("zoomlion-combine", "Zoomlion", "China", VehicleType.combine),
    # Seeders / planters
    ("amazone-seeder", "Amazone", "Germany", VehicleType.seeder),
    ("vaderstad-seeder", "Väderstad", "Sweden", VehicleType.seeder),
    ("john-deere-seeder", "John Deere", "USA", VehicleType.seeder),
    ("kuhn-seeder", "Kuhn", "France", VehicleType.seeder),
    ("horsch-seeder", "Horsch", "Germany", VehicleType.seeder),
    ("gazeman", "Газмаш", "Russia", VehicleType.seeder),
    ("belotserkovmash", "БелоцерковМАЗ", "Ukraine", VehicleType.seeder),
    ("kinze", "Kinze", "USA", VehicleType.seeder),
    # Potato planters
    ("grimme-planter", "Grimme", "Germany", VehicleType.potato_planter),
    ("hassia-planter", "Hassia", "Germany", VehicleType.potato_planter),
    ("akpil-planter", "Akpil", "Poland", VehicleType.potato_planter),
    ("bolko-planter", "Болко", "Russia", VehicleType.potato_planter),
    ("ksm-planter", "КСМ", "Russia", VehicleType.potato_planter),
    # Legacy tillage / forage umbrellas (kept for existing rows)
    ("lemken", "Lemken", "Germany", VehicleType.tillage),
    ("kverneland", "Kverneland", "Norway", VehicleType.tillage),
    ("amazone-tillage", "Amazone", "Germany", VehicleType.tillage),
    ("horsch-tillage", "Horsch", "Germany", VehicleType.tillage),
    ("vaderstad-tillage", "Väderstad", "Sweden", VehicleType.tillage),
    ("kuhn-tillage", "Kuhn", "France", VehicleType.tillage),
    ("wil-rich", "Wil-Rich", "USA", VehicleType.tillage),
    ("bdt", "БДТ", "Russia", VehicleType.tillage),
    ("unlu-tillage", "Ünlü", "Turkey", VehicleType.tillage),
    ("claas-forage", "CLAAS", "Germany", VehicleType.forage),
    ("john-deere-forage", "John Deere", "USA", VehicleType.forage),
    ("krone-forage", "Krone", "Germany", VehicleType.forage),
    ("pottinger", "Pöttinger", "Austria", VehicleType.forage),
    ("rostselmash-forage", "Ростсельмаш", "Russia", VehicleType.forage),
    ("kuhn-forage", "Kuhn", "France", VehicleType.forage),
    ("new-holland-forage", "New Holland", "Italy", VehicleType.forage),
    ("sipma", "Sipma", "Poland", VehicleType.forage),
    # Plows
    ("lemken-plow", "Lemken", "Germany", VehicleType.plow),
    ("kverneland-plow", "Kverneland", "Norway", VehicleType.plow),
    ("unlu-plow", "Ünlü", "Turkey", VehicleType.plow),
    ("vogel-noot", "Vogel & Noot", "Austria", VehicleType.plow),
    ("alpler-plow", "Alpler", "Turkey", VehicleType.plow),
    ("pln-plow", "ПЛН", "Russia", VehicleType.plow),
    ("gregoire-besson", "Grégoire-Besson", "France", VehicleType.plow),
    # Harrows
    ("bdt-harrow", "БДТ", "Russia", VehicleType.harrow),
    ("lemken-harrow", "Lemken", "Germany", VehicleType.harrow),
    ("amazone-harrow", "Amazone", "Germany", VehicleType.harrow),
    ("horsch-harrow", "Horsch", "Germany", VehicleType.harrow),
    ("vaderstad-harrow", "Väderstad", "Sweden", VehicleType.harrow),
    ("quivogne-harrow", "Quivogne", "France", VehicleType.harrow),
    ("akpil-harrow", "Akpil", "Poland", VehicleType.harrow),
    # Cultivators
    ("kuhn-cult", "Kuhn", "France", VehicleType.cultivator),
    ("lemken-cult", "Lemken", "Germany", VehicleType.cultivator),
    ("horsch-cult", "Horsch", "Germany", VehicleType.cultivator),
    ("kverneland-cult", "Kverneland", "Norway", VehicleType.cultivator),
    ("amazone-cult", "Amazone", "Germany", VehicleType.cultivator),
    ("kpsh-cult", "КПШ", "Russia", VehicleType.cultivator),
    ("wil-rich-cult", "Wil-Rich", "USA", VehicleType.cultivator),
    # Hillers
    ("okuchnik-std", "Окучник", "Russia", VehicleType.hiller),
    ("akpil-hiller", "Akpil", "Poland", VehicleType.hiller),
    ("grimme-hiller", "Grimme", "Germany", VehicleType.hiller),
    ("neva-hiller", "Нева", "Russia", VehicleType.hiller),
    # Ditchers
    ("arychnik-std", "Арычник", "Kyrgyzstan", VehicleType.ditcher),
    ("dondi-ditcher", "Dondi", "Italy", VehicleType.ditcher),
    ("baselier-ditcher", "Baselier", "Netherlands", VehicleType.ditcher),
    # Mulchers
    ("orcsi-mulcher", "Orcsi", "Italy", VehicleType.mulcher),
    ("kuhn-mulcher", "Kuhn", "France", VehicleType.mulcher),
    ("berti-mulcher", "Berti", "Italy", VehicleType.mulcher),
    ("humus-mulcher", "Humus", "Germany", VehicleType.mulcher),
    ("schulte-mulcher", "Schulte", "Canada", VehicleType.mulcher),
    # Mowers
    ("claas-mower", "CLAAS", "Germany", VehicleType.mower),
    ("krone-mower", "Krone", "Germany", VehicleType.mower),
    ("kuhn-mower", "Kuhn", "France", VehicleType.mower),
    ("pottinger-mower", "Pöttinger", "Austria", VehicleType.mower),
    ("rostselmash-mower", "Ростсельмаш", "Russia", VehicleType.mower),
    ("sipma-mower", "Sipma", "Poland", VehicleType.mower),
    ("john-deere-mower", "John Deere", "USA", VehicleType.mower),
    # Walk-behind mowers
    ("husqvarna-wbm", "Husqvarna", "Sweden", VehicleType.walk_behind_mower),
    ("stiga-wbm", "Stiga", "Italy", VehicleType.walk_behind_mower),
    ("champion-wbm", "Champion", "Russia", VehicleType.walk_behind_mower),
    ("patriot-wbm", "Patriot", "USA", VehicleType.walk_behind_mower),
    ("al-ko-wbm", "AL-KO", "Germany", VehicleType.walk_behind_mower),
    # Balers
    ("claas-baler", "CLAAS", "Germany", VehicleType.baler),
    ("krone-baler", "Krone", "Germany", VehicleType.baler),
    ("new-holland-baler", "New Holland", "Italy", VehicleType.baler),
    ("john-deere-baler", "John Deere", "USA", VehicleType.baler),
    ("sipma-baler", "Sipma", "Poland", VehicleType.baler),
    ("pr-baler", "ПР", "Russia", VehicleType.baler),
    ("welger-baler", "Welger", "Germany", VehicleType.baler),
    # Headers
    ("claas-header", "CLAAS", "Germany", VehicleType.header),
    ("john-deere-header", "John Deere", "USA", VehicleType.header),
    ("rostselmash-header", "Ростсельмаш", "Russia", VehicleType.header),
    ("gomselmash-header", "Гомсельмаш", "Belarus", VehicleType.header),
    ("capello-header", "Capello", "Italy", VehicleType.header),
    # Rakes
    ("claas-rake", "CLAAS", "Germany", VehicleType.rake),
    ("kuhn-rake", "Kuhn", "France", VehicleType.rake),
    ("krone-rake", "Krone", "Germany", VehicleType.rake),
    ("pottinger-rake", "Pöttinger", "Austria", VehicleType.rake),
    ("gvk-rake", "ГВК", "Russia", VehicleType.rake),
    # Feed mixers
    ("trioliet", "Trioliet", "Netherlands", VehicleType.feed_mixer),
    ("kuhn-mixer", "Kuhn", "France", VehicleType.feed_mixer),
    ("siolo", "Siolo", "Italy", VehicleType.feed_mixer),
    ("rmh-mixer", "RMH", "Germany", VehicleType.feed_mixer),
    ("isk-mixer", "ИСК", "Russia", VehicleType.feed_mixer),
    # Sprayers
    ("amazone-sprayer", "Amazone", "Germany", VehicleType.sprayer),
    ("john-deere-sprayer", "John Deere", "USA", VehicleType.sprayer),
    ("hagie", "Hagie", "USA", VehicleType.sprayer),
    ("hardi", "Hardi", "Denmark", VehicleType.sprayer),
    ("kverneland-sprayer", "Kverneland", "Norway", VehicleType.sprayer),
    ("rogator", "RoGator", "USA", VehicleType.sprayer),
    ("oprysk", "ОП", "Russia", VehicleType.sprayer),
    ("tecnoma", "Tecnoma", "France", VehicleType.sprayer),
    # Fertilizer spreaders
    ("amazone-spread", "Amazone", "Germany", VehicleType.fertilizer_spreader),
    ("kuhn-spread", "Kuhn", "France", VehicleType.fertilizer_spreader),
    ("rauch-spread", "Rauch", "Germany", VehicleType.fertilizer_spreader),
    ("sulky-spread", "Sulky", "France", VehicleType.fertilizer_spreader),
    ("rmu-spread", "РМУ", "Russia", VehicleType.fertilizer_spreader),
    # Manure spreaders
    ("bergmann-manure", "Bergmann", "Germany", VehicleType.manure_spreader),
    ("strautmann-manure", "Strautmann", "Germany", VehicleType.manure_spreader),
    ("prt-manure", "ПРТ", "Russia", VehicleType.manure_spreader),
    ("rozmiesz-manure", "Rozmiesz", "Poland", VehicleType.manure_spreader),
    # Potato diggers
    ("grimme-digger", "Grimme", "Germany", VehicleType.potato_digger),
    ("bolko-digger", "Болко", "Russia", VehicleType.potato_digger),
    ("ktn-digger", "КТН", "Russia", VehicleType.potato_digger),
    ("akpil-digger", "Akpil", "Poland", VehicleType.potato_digger),
    ("double-l-digger", "Double L", "USA", VehicleType.potato_digger),
    # KUN / front loaders
    ("pku-kun", "ПКУ", "Russia", VehicleType.kun),
    ("tur-kun", "ТУР", "Russia", VehicleType.kun),
    ("metal-fach-kun", "Metal-Fach", "Poland", VehicleType.kun),
    ("stoll-kun", "Stoll", "Germany", VehicleType.kun),
    ("quicke-kun", "Quicke", "Sweden", VehicleType.kun),
    ("amkodor-kun", "Амкодор", "Belarus", VehicleType.kun),
    # Farm crushers
    ("drobilka-std", "Дробилка", "Russia", VehicleType.farm_crusher),
    ("hammer-mill", "Hammer Mill", "China", VehicleType.farm_crusher),
    ("mlyn-crusher", "Млын", "Belarus", VehicleType.farm_crusher),
    ("farmet-crusher", "Farmet", "Czech", VehicleType.farm_crusher),
    # Grain throwers
    ("zernomet-std", "Зерномёт", "Russia", VehicleType.grain_thrower),
    ("pzm-thrower", "ПЗМ", "Russia", VehicleType.grain_thrower),
    ("zps-thrower", "ЗПС", "Russia", VehicleType.grain_thrower),
    # Grain cleaners
    ("petkus-cleaner", "Petkus", "Germany", VehicleType.grain_cleaner),
    ("crippen-cleaner", "Crippen", "USA", VehicleType.grain_cleaner),
    ("ovs-cleaner", "ОВС", "Russia", VehicleType.grain_cleaner),
    ("zav-cleaner", "ЗАВ", "Russia", VehicleType.grain_cleaner),
    # Film layers / bed formers
    ("plenka-layer", "Пленкоукладчик", "China", VehicleType.film_layer),
    ("bed-former", "Грядообразователь", "China", VehicleType.film_layer),
    ("hortitec-layer", "Hortitec", "Italy", VehicleType.film_layer),
    # Ridge formers
    ("bugor-std", "Бугорообразователь", "Russia", VehicleType.ridge_former),
    ("grimme-ridge", "Grimme", "Germany", VehicleType.ridge_former),
    ("baselier-ridge", "Baselier", "Netherlands", VehicleType.ridge_former),
    # Agri drones
    ("dji-agras", "DJI Agras", "China", VehicleType.agri_drone),
    ("xag-drone", "XAG", "China", VehicleType.agri_drone),
    ("autel-agri", "Autel", "China", VehicleType.agri_drone),
    ("joviau-drone", "JOUAV", "China", VehicleType.agri_drone),
    ("t30-drone", "T30 Agri", "China", VehicleType.agri_drone),
    ("agronomist-drone", "Агроном", "Russia", VehicleType.agri_drone),
    # Other agri
    ("mtz-other", "МТЗ Belarus", "Belarus", VehicleType.other_agri),
    ("john-deere-other", "John Deere", "USA", VehicleType.other_agri),
    ("claas-other", "CLAAS", "Germany", VehicleType.other_agri),
    ("rostselmash-other", "Ростсельмаш", "Russia", VehicleType.other_agri),
    ("kubota-other", "Kubota", "Japan", VehicleType.other_agri),
    ("amkodor-other", "Амкодор", "Belarus", VehicleType.other_agri),
    ("fendt-other", "Fendt", "Germany", VehicleType.other_agri),
    ("new-holland-other", "New Holland", "Italy", VehicleType.other_agri),
    ("lovol-other", "Lovol", "China", VehicleType.other_agri),
    ("yto-other", "YTO (ЮТО)", "China", VehicleType.other_agri),
]

# Retired model-as-brand identity (kept disabled by seed cleanup).
FARM_DISABLE_BRAND_SLUGS: tuple[str, ...] = ("dt75-tractor",)

# Truck model nicknames wrongly attached to Foton tractor brand.
FARM_DISABLE_MODELS_BY_BRAND: dict[str, tuple[str, ...]] = {
    "foton-tractor": ("auman", "est", "gntl"),
}

FARM_SALE_MODELS: dict[str, list[tuple[str, str]]] = {
    "mtz-tractor": [
        ("80", "80"),
        ("82", "82"),
        ("82-1", "82.1"),
        ("892", "892"),
        ("920", "920"),
        ("1025", "1025"),
        ("1221", "1221"),
        ("1523", "1523"),
        ("3522", "3522"),
    ],
    "john-deere-tractor": [
        ("6m", "6M"),
        ("6r", "6R"),
        ("8r", "8R"),
        ("5e", "5E"),
    ],
    "case-ih-tractor": [
        ("puma", "Puma"),
        ("magnum", "Magnum"),
        ("farmall", "Farmall"),
    ],
    "new-holland-tractor": [
        ("t6", "T6"),
        ("t7", "T7"),
        ("t8", "T8"),
    ],
    "claas-tractor": [
        ("arion", "Arion"),
        ("axion", "Axion"),
        ("xerion", "Xerion"),
    ],
    "fendt-tractor": [
        ("700", "700 Vario"),
        ("900", "900 Vario"),
        ("1000", "1000 Vario"),
    ],
    "kubota-tractor": [
        ("m7040", "M7040"),
        ("m8540", "M8540"),
        ("l3901", "L3901"),
    ],
    "kirovets-tractor": [
        ("k-744", "К-744"),
        ("k-7m", "К-7М"),
        ("k-525", "К-525"),
    ],
    "deutz-fahr-tractor": [
        ("5115", "5115"),
        ("6165", "6165"),
        ("7250", "7250"),
    ],
    "mahindra-tractor": [
        ("575", "575"),
        ("605", "605"),
        ("arjun", "Arjun"),
    ],
    "yto-tractor": [
        ("x904", "X904"),
        ("x1204", "X1204"),
        ("nlx1054", "NLX1054"),
    ],
    "yumz-tractor": [
        ("6kl", "6КЛ"),
        ("8040", "8040"),
        ("8280", "8280"),
    ],
    "xtz-tractor": [
        ("t-16", "Т-16"),
        ("t-150", "Т-150"),
        ("t-150k", "Т-150К"),
        ("17221", "17221"),
    ],
    "ltz-tractor": [
        ("t-40", "Т-40"),
        ("55", "55"),
        ("60ab", "60АБ"),
        ("95b", "95Б"),
    ],
    "vtz-tractor": [
        ("t-25", "Т-25"),
        ("t-30", "Т-30"),
        ("vtz-2032", "ВТЗ-2032"),
    ],
    # Canonical manufacturer for DT-75 family (Volgograd / ВгТЗ).
    "vgtz-tractor": [
        ("dt-75", "ДТ-75"),
        ("dt-75m", "ДТ-75М"),
        ("dt-75d", "ДТ-75Д"),
    ],
    # Legacy rows under retired brand slug — keep for reference remap only.
    "dt75-tractor": [
        ("dt-75", "ДТ-75"),
        ("dt-75m", "ДТ-75М"),
        ("dt-75d", "ДТ-75Д"),
    ],
    "shifeng-tractor": [
        ("sf240", "SF240"),
        ("sf244", "SF244"),
        ("sf504", "SF504"),
        ("sf904", "SF904"),
    ],
    "shifeng-mini": [
        ("sf240", "SF240"),
        ("sf244", "SF244"),
        ("sf324", "SF324"),
    ],
    "lovol-tractor": [
        ("tb504", "TB504"),
        ("tb754", "TB754"),
        ("m804", "M804"),
    ],
    "foton-tractor": [
        ("tb504", "TB504"),
        ("ft824", "FT824"),
        ("ft1004", "FT1004"),
    ],
    "zoomlion-tractor": [
        ("rs1304", "RS1304"),
        ("rn1104", "RN1104"),
        ("pl2304", "PL2304"),
    ],
    "yanmar-tractor": [
        ("ef494t", "EF494T"),
        ("ym357a", "YM357A"),
        ("eg453", "EG453"),
    ],
    "dongfanghong-tractor": [
        ("lx904", "LX904"),
        ("lx1204", "LX1204"),
        ("lx1004", "LX1004"),
    ],
    "changfa-tractor": [
        ("cf504", "CF504"),
        ("cf704", "CF704"),
    ],
    "weihe-tractor": [
        ("wh404", "WH404"),
        ("wh504", "WH504"),
    ],
    "kasun-tractor": [
        ("ks404", "KS404"),
        ("ks504", "KS504"),
    ],
    "yuki-tractor": [
        ("1004", "1004"),
        ("1204", "1204"),
    ],
    "fm-world-tractor": [
        ("wd1104m", "WD1104M"),
        ("wd904", "WD904"),
    ],
    "kubota-mini": [
        ("b2601", "B2601"),
        ("l1-382", "L1-382"),
        ("bx2380", "BX2380"),
    ],
    "iseki-mini": [
        ("tm3185", "TM3185"),
        ("tg5470", "TG5470"),
        ("th4290", "TH4290"),
    ],
    "yanmar-mini": [
        ("ke-160", "KE-160"),
        ("af-180", "AF-180"),
        ("rs-27", "RS-27"),
    ],
    "hinomoto-mini": [
        ("n209", "N209"),
        ("e202", "E202"),
        ("c174", "C174"),
    ],
    "xingtai-mini": [
        ("xt244", "XT244"),
        ("xt304", "XT304"),
        ("xt404", "XT404"),
    ],
    "jinma-mini": [
        ("jm244", "JM244"),
        ("jm354", "JM354"),
        ("jm404", "JM404"),
    ],
    "scout-mini": [
        ("t-25", "Т-25"),
        ("t-15", "Т-15"),
        ("t-18", "Т-18"),
    ],
    "uralets-mini": [
        ("220", "220"),
        ("224", "224"),
        ("254", "254"),
    ],
    "mtz-mini": [
        ("320", "320"),
        ("321", "321"),
        ("422", "422"),
    ],
    "lovol-mini": [
        ("te244", "TE244"),
        ("te354", "TE354"),
    ],
    "solis-mini": [
        ("26", "26"),
        ("50", "50"),
    ],
    "dongfeng-mini": [
        ("df244", "DF244"),
        ("df304", "DF304"),
    ],
    "neva": [
        ("mb-2", "МБ-2"),
        ("mb-23", "МБ-23"),
        ("mb-compakt", "МБ-Компакт"),
    ],
    "salyut": [
        ("100", "100"),
        ("5l-6-0", "5Л-6.0"),
        ("100-x", "100-X"),
    ],
    "cascade": [
        ("mb-6", "МБ-6"),
        ("mb-4", "МБ-4"),
    ],
    "celina": [
        ("mb-501", "МБ-501"),
        ("mb-601", "МБ-601"),
    ],
    "champion-wb": [
        ("bc-8716", "BC8716"),
        ("bc-5712", "BC5712"),
    ],
    "huter": [
        ("gmc-6-5", "GMC-6.5"),
        ("gmc-7-0", "GMC-7.0"),
    ],
    "patriot-wb": [
        ("california", "California"),
        ("vegas", "Vegas"),
        ("oregon", "Oregon"),
    ],
    "kubota-wb": [
        ("tg1860", "TG1860"),
        ("t1870", "T1870"),
    ],
    "honda-wb": [
        ("f220", "F220"),
        ("f560", "F560"),
        ("fj500", "FJ500"),
    ],
    "pubert": [
        ("vario", "Vario"),
        ("eco", "Eco"),
        ("quatro", "Quatro"),
    ],
    "rolf-wb": [
        ("mh-500", "MH-500"),
        ("mh-700", "MH-700"),
    ],
    "lifan-wb": [
        ("1wg900", "1WG900"),
        ("1wg1100", "1WG1100"),
    ],
    "forza-wb": [
        ("mb-80", "МБ-80"),
        ("mb-105", "МБ-105"),
    ],
    "rostselmash-combine": [
        ("acros", "ACROS"),
        ("torum", "TORUM"),
        ("nova", "NOVA"),
        ("rsm-161", "RSM 161"),
    ],
    "john-deere-combine": [
        ("s780", "S780"),
        ("s770", "S770"),
        ("t670", "T670"),
    ],
    "claas-combine": [
        ("lexion", "LEXION"),
        ("trion", "TRION"),
        ("tucano", "TUCANO"),
    ],
    "case-ih-combine": [
        ("axial-flow", "Axial-Flow"),
        ("afx", "AFX"),
    ],
    "new-holland-combine": [
        ("cr", "CR"),
        ("cx", "CX"),
        ("tc", "TC"),
    ],
    "gomselmash": [
        ("palesse-gs12", "PALESSE GS12"),
        ("palesse-gs16", "PALESSE GS16"),
        ("kzs-1218", "КЗС-1218"),
    ],
    "fendt-combine": [
        ("ideal", "IDEAL"),
        ("5275", "5275 C"),
    ],
    "sampo": [
        ("comia", "Comia"),
        ("vr", "VR"),
    ],
    "lovol-combine": [
        ("gf80", "GF80"),
        ("gm80", "GM80"),
    ],
    "zoomlion-combine": [
        ("tb60", "TB60"),
        ("4lz", "4LZ"),
    ],
    "amazone-seeder": [
        ("d9", "D9"),
        ("citan", "Citan"),
        ("precea", "Precea"),
    ],
    "vaderstad-seeder": [
        ("rapid", "Rapid"),
        ("spirit", "Spirit"),
        ("tempo", "Tempo"),
    ],
    "john-deere-seeder": [
        ("1890", "1890"),
        ("1775nt", "1775NT"),
        ("db60", "DB60"),
    ],
    "kuhn-seeder": [
        ("maxima", "Maxima"),
        ("premia", "Premia"),
        ("esprit", "Esprit"),
    ],
    "horsch-seeder": [
        ("pronto", "Pronto"),
        ("maestro", "Maestro"),
        ("avatar", "Avatar"),
    ],
    "gazeman": [
        ("sz-3-6", "СЗ-3.6"),
        ("szp-3-6", "СЗП-3.6"),
    ],
    "belotserkovmash": [
        ("sz-5-4", "СЗ-5.4"),
        ("supn-8", "СУПН-8"),
    ],
    "kinze": [
        ("3600", "3600"),
        ("4900", "4900"),
    ],
    "lemken": [
        ("juwel", "Juwel"),
        ("karat", "Karat"),
        ("rubin", "Rubin"),
    ],
    "kverneland": [
        ("ed", "ED"),
        ("qualidisc", "Qualidisc"),
        ("clc", "CLC"),
    ],
    "amazone-tillage": [
        ("catros", "Catros"),
        ("cenius", "Cenius"),
        ("cayron", "Cayron"),
    ],
    "horsch-tillage": [
        ("joker", "Joker"),
        ("tiger", "Tiger"),
        ("terrano", "Terrano"),
    ],
    "vaderstad-tillage": [
        ("carrier", "Carrier"),
        ("topdown", "TopDown"),
        ("cultus", "Cultus"),
    ],
    "kuhn-tillage": [
        ("discover", "Discover"),
        ("optimer", "Optimer"),
        ("multi-master", "Multi-Master"),
    ],
    "wil-rich": [
        ("3400", "3400"),
        ("3570", "3570"),
    ],
    "bdt": [
        ("bdt-7", "БДТ-7"),
        ("bdt-3", "БДТ-3"),
        ("ldn-5", "ЛДГ-5"),
    ],
    "unlu-tillage": [
        ("nitor", "Nitor"),
        ("master", "Master"),
        ("disk", "Disk"),
    ],
    "claas-forage": [
        ("jaguar", "JAGUAR"),
        ("disco", "DISCO"),
        ("quadrant", "QUADRANT"),
    ],
    "john-deere-forage": [
        ("8800", "8800"),
        ("w260", "W260"),
        ("l1534", "L1534"),
    ],
    "krone-forage": [
        ("big-x", "Big X"),
        ("easycut", "EasyCut"),
        ("comprima", "Comprima"),
    ],
    "pottinger": [
        ("jumbo", "Jumbo"),
        ("novacat", "NOVACAT"),
        ("impress", "Impress"),
    ],
    "rostselmash-forage": [
        ("don-680m", "ДОН-680М"),
        ("rsm-1401", "RSM 1401"),
        ("f-2650", "F 2650"),
    ],
    "kuhn-forage": [
        ("fc", "FC"),
        ("ga", "GA"),
        ("vb", "VB"),
    ],
    "new-holland-forage": [
        ("fr", "FR"),
        ("roll-belt", "Roll-Belt"),
        ("discbine", "Discbine"),
    ],
    "sipma": [
        ("pk", "PK"),
        ("z", "Z"),
        ("ps", "PS"),
    ],
    "amazone-sprayer": [
        ("ux", "UX"),
        ("pantera", "Pantera"),
        ("uf", "UF"),
    ],
    "john-deere-sprayer": [
        ("r4045", "R4045"),
        ("m4040", "M4040"),
        ("4030", "4030"),
    ],
    "hagie": [
        ("sts12", "STS12"),
        ("sts16", "STS16"),
    ],
    "hardi": [
        ("commander", "Commander"),
        ("navigator", "Navigator"),
        ("alpha", "Alpha"),
    ],
    "kverneland-sprayer": [
        ("ixter", "iXter"),
        ("ixtrack", "iXtrack"),
    ],
    "rogator": [
        ("rg1100", "RG1100"),
        ("rg1300", "RG1300"),
    ],
    "oprysk": [
        ("op-2000", "ОП-2000"),
        ("op-2500", "ОП-2500"),
        ("msh-9", "МШ-9"),
    ],
    "tecnoma": [
        ("laser", "Laser"),
        ("tecnis", "Tecnis"),
    ],
    "dji-agras": [
        ("t40", "T40"),
        ("t50", "T50"),
        ("t25", "T25"),
        ("t30", "T30"),
    ],
    "xag-drone": [
        ("p100", "P100"),
        ("v40", "V40"),
        ("p40", "P40"),
    ],
    "autel-agri": [
        ("evo-ii", "EVO II"),
        ("dragonfish", "Dragonfish"),
    ],
    "joviau-drone": [
        ("cw-15", "CW-15"),
        ("ph-20", "PH-20"),
    ],
    "t30-drone": [
        ("t30", "T30"),
        ("t20", "T20"),
    ],
    "agronomist-drone": [
        ("ag-30", "AG-30"),
        ("ag-50", "AG-50"),
    ],
    "mtz-other": [
        ("82-1", "82.1"),
        ("1221", "1221"),
    ],
    "john-deere-other": [
        ("6r", "6R"),
        ("s780", "S780"),
    ],
    "claas-other": [
        ("arion", "Arion"),
        ("lexion", "LEXION"),
    ],
    "rostselmash-other": [
        ("acros", "ACROS"),
        ("rsm-2375", "RSM 2375"),
    ],
    "kubota-other": [
        ("m7040", "M7040"),
        ("l3901", "L3901"),
    ],
    "amkodor-other": [
        ("352", "352"),
        ("527", "527"),
    ],
    "fendt-other": [
        ("700", "700 Vario"),
        ("ideal", "IDEAL"),
    ],
    "new-holland-other": [
        ("t7", "T7"),
        ("cr", "CR"),
    ],
    "lovol-other": [
        ("tb504", "TB504"),
        ("te244", "TE244"),
    ],
    "yto-other": [
        ("x904", "X904"),
        ("x1204", "X1204"),
    ],
    "grimme-planter": [
        ("gl-420", "GL 420"),
        ("gl-34t", "GL 34T"),
    ],
    "hassia-planter": [
        ("sl-4", "SL 4"),
        ("unimat", "Unimat"),
    ],
    "akpil-planter": [
        ("rhino", "Rhino"),
        ("glebogryzarka", "Glebogryzarka"),
    ],
    "bolko-planter": [
        ("ksm-4", "КСМ-4"),
        ("ksm-6", "КСМ-6"),
    ],
    "ksm-planter": [
        ("ksm-4", "КСМ-4"),
        ("ksm-6", "КСМ-6"),
    ],
    "lemken-plow": [
        ("juwel", "Juwel"),
        ("europal", "Europal"),
        ("varian", "Varian"),
    ],
    "kverneland-plow": [
        ("ed", "ED"),
        ("eg", "EG"),
        ("lb", "LB"),
    ],
    "unlu-plow": [
        ("nitor", "Nitor"),
        ("master", "Master"),
    ],
    "vogel-noot": [
        ("xms", "XMS"),
        ("xm", "XM"),
    ],
    "alpler-plow": [
        ("ap", "AP"),
        ("np", "NP"),
    ],
    "pln-plow": [
        ("pln-3-35", "ПЛН-3-35"),
        ("pln-5-35", "ПЛН-5-35"),
    ],
    "gregoire-besson": [
        ("rw", "RW"),
        ("spb", "SPB"),
    ],
    "bdt-harrow": [
        ("bdt-7", "БДТ-7"),
        ("bdt-3", "БДТ-3"),
        ("ldn-5", "ЛДГ-5"),
    ],
    "lemken-harrow": [
        ("rubin", "Rubin"),
        ("helidor", "Heliodor"),
    ],
    "amazone-harrow": [
        ("catros", "Catros"),
        ("discros", "Discros"),
    ],
    "horsch-harrow": [
        ("joker", "Joker"),
        ("cruiser", "Cruiser"),
    ],
    "vaderstad-harrow": [
        ("carrier", "Carrier"),
        ("rapid", "Rapid"),
    ],
    "quivogne-harrow": [
        ("apv", "APV"),
        ("ssd", "SSD"),
    ],
    "akpil-harrow": [
        ("tiger", "Tiger"),
        ("bison", "Bison"),
    ],
    "kuhn-cult": [
        ("optimer", "Optimer"),
        ("cultimer", "Cultimer"),
    ],
    "lemken-cult": [
        ("karat", "Karat"),
        ("koralin", "Koralin"),
    ],
    "horsch-cult": [
        ("tiger", "Tiger"),
        ("terrano", "Terrano"),
    ],
    "kverneland-cult": [
        ("clc", "CLC"),
        ("enduro", "Enduro"),
    ],
    "amazone-cult": [
        ("cenius", "Cenius"),
        ("cayros", "Cayros"),
    ],
    "kpsh-cult": [
        ("kpsh-9", "КПШ-9"),
        ("kpsh-5", "КПШ-5"),
    ],
    "wil-rich-cult": [
        ("3400", "3400"),
        ("3570", "3570"),
    ],
    "okuchnik-std": [
        ("2h", "2-рядный"),
        ("3h", "3-рядный"),
        ("4h", "4-рядный"),
    ],
    "akpil-hiller": [
        ("rhino", "Rhino"),
        ("pole", "Pole"),
    ],
    "grimme-hiller": [
        ("gh", "GH"),
        ("gf", "GF"),
    ],
    "neva-hiller": [
        ("on-2", "ОН-2"),
        ("on-3", "ОН-3"),
    ],
    "arychnik-std": [
        ("1r", "1-рядный"),
        ("2r", "2-рядный"),
    ],
    "dondi-ditcher": [
        ("d60", "D60"),
        ("d90", "D90"),
    ],
    "baselier-ditcher": [
        ("fk", "FK"),
        ("ridge", "Ridge"),
    ],
    "orcsi-mulcher": [
        ("fox", "Fox"),
        ("tiger", "Tiger"),
    ],
    "kuhn-mulcher": [
        ("bpr", "BPR"),
        ("bke", "BKE"),
    ],
    "berti-mulcher": [
        ("tfb", "TFB"),
        ("park", "Park"),
    ],
    "humus-mulcher": [
        ("spm", "SPM"),
        ("oms", "OMS"),
    ],
    "schulte-mulcher": [
        ("fx", "FX"),
        ("xh", "XH"),
    ],
    "claas-mower": [
        ("disco", "DISCO"),
        ("corto", "CORTO"),
    ],
    "krone-mower": [
        ("easycut", "EasyCut"),
        ("activemow", "ActiveMow"),
    ],
    "kuhn-mower": [
        ("fc", "FC"),
        ("gmd", "GMD"),
    ],
    "pottinger-mower": [
        ("novacat", "NOVACAT"),
        ("eurocat", "EUROCAT"),
    ],
    "rostselmash-mower": [
        ("ktsu", "КТСУ"),
        ("ks-2-1", "КС-2.1"),
    ],
    "sipma-mower": [
        ("kd", "KD"),
        ("kdt", "KDT"),
    ],
    "john-deere-mower": [
        ("r", "R"),
        ("f", "F"),
    ],
    "husqvarna-wbm": [
        ("lc", "LC"),
        ("r", "R"),
    ],
    "stiga-wbm": [
        ("collector", "Collector"),
        ("combi", "Combi"),
    ],
    "champion-wbm": [
        ("lm", "LM"),
        ("gm", "GM"),
    ],
    "patriot-wbm": [
        ("pt", "PT"),
        ("garden", "Garden"),
    ],
    "al-ko-wbm": [
        ("classic", "Classic"),
        ("highline", "Highline"),
    ],
    "claas-baler": [
        ("quadrant", "QUADRANT"),
        ("rollant", "ROLLANT"),
        ("markant", "MARKANT"),
    ],
    "krone-baler": [
        ("comprima", "Comprima"),
        ("big-pack", "Big Pack"),
        ("fortima", "Fortima"),
    ],
    "new-holland-baler": [
        ("roll-belt", "Roll-Belt"),
        ("bigbaler", "BigBaler"),
    ],
    "john-deere-baler": [
        ("l", "L"),
        ("v", "V"),
    ],
    "sipma-baler": [
        ("pk", "PK"),
        ("z", "Z"),
        ("ps", "PS"),
    ],
    "pr-baler": [
        ("pr-f-145", "ПР-Ф-145"),
        ("pr-f-180", "ПР-Ф-180"),
    ],
    "welger-baler": [
        ("rp", "RP"),
        ("ap", "AP"),
    ],
    "claas-header": [
        ("vario", "VARIO"),
        ("cerio", "CERIO"),
    ],
    "john-deere-header": [
        ("600r", "600R"),
        ("700fd", "700FD"),
    ],
    "rostselmash-header": [
        ("power-stream", "Power Stream"),
        ("argus", "Argus"),
    ],
    "gomselmash-header": [
        ("zhzs", "ЖЗС"),
        ("zhkk", "ЖКК"),
    ],
    "capello-header": [
        ("helianthus", "Helianthus"),
        ("quasar", "Quasar"),
    ],
    "claas-rake": [
        ("liner", "LINER"),
        ("schwader", "Schwader"),
    ],
    "kuhn-rake": [
        ("ga", "GA"),
        ("gf", "GF"),
    ],
    "krone-rake": [
        ("swadro", "Swadro"),
        ("vendro", "Vendro"),
    ],
    "pottinger-rake": [
        ("top", "TOP"),
        ("hit", "HIT"),
    ],
    "gvk-rake": [
        ("gvk-6", "ГВК-6"),
        ("gvk-7", "ГВК-7"),
    ],
    "trioliet": [
        ("solomix", "Solomix"),
        ("gigant", "Gigant"),
    ],
    "kuhn-mixer": [
        ("euromix", "Euromix"),
        ("profile", "Profile"),
    ],
    "siolo": [
        ("self", "Self"),
        ("trailer", "Trailer"),
    ],
    "rmh-mixer": [
        ("vertimix", "Verti-Mix"),
        ("mix", "Mix"),
    ],
    "isk-mixer": [
        ("isk-10", "ИСК-10"),
        ("isk-12", "ИСК-12"),
    ],
    "amazone-spread": [
        ("za-v", "ZA-V"),
        ("za-ts", "ZA-TS"),
    ],
    "kuhn-spread": [
        ("mds", "MDS"),
        ("axis", "Axis"),
    ],
    "rauch-spread": [
        ("axis", "Axis"),
        ("mds", "MDS"),
    ],
    "sulky-spread": [
        ("dx", "DX"),
        ("x", "X"),
    ],
    "rmu-spread": [
        ("rmu-1000", "РМУ-1000"),
        ("rmu-500", "РМУ-500"),
    ],
    "bergmann-manure": [
        ("t", "T"),
        ("m", "M"),
    ],
    "strautmann-manure": [
        ("vs", "VS"),
        ("be", "BE"),
    ],
    "prt-manure": [
        ("prt-10", "ПРТ-10"),
        ("prt-7", "ПРТ-7"),
    ],
    "rozmiesz-manure": [
        ("n", "N"),
        ("h", "H"),
    ],
    "grimme-digger": [
        ("se", "SE"),
        ("gt", "GT"),
        ("varitron", "Varitron"),
    ],
    "bolko-digger": [
        ("ktn-2b", "КТН-2Б"),
        ("ktn-1a", "КТН-1А"),
    ],
    "ktn-digger": [
        ("ktn-2b", "КТН-2Б"),
        ("ktn-1b", "КТН-1Б"),
    ],
    "akpil-digger": [
        ("bulwa", "Bulwa"),
        ("zwierzyniec", "Zwierzyniec"),
    ],
    "double-l-digger": [
        ("8500", "8500"),
        ("9530", "9530"),
    ],
    "pku-kun": [
        ("pku-0-8", "ПКУ-0.8"),
        ("pku-0-9", "ПКУ-0.9"),
    ],
    "tur-kun": [
        ("tur-5", "ТУР-5"),
        ("tur-9", "ТУР-9"),
    ],
    "metal-fach-kun": [
        ("t229", "T229"),
        ("t229h", "T229H"),
    ],
    "stoll-kun": [
        ("classic", "Classic"),
        ("profiline", "Profiline"),
    ],
    "quicke-kun": [
        ("q", "Q"),
        ("x", "X"),
    ],
    "amkodor-kun": [
        ("352", "352"),
        ("527", "527"),
    ],
    "drobilka-std": [
        ("dk-1", "ДК-1"),
        ("dk-2", "ДК-2"),
    ],
    "hammer-mill": [
        ("9fq", "9FQ"),
        ("9ff", "9FF"),
    ],
    "mlyn-crusher": [
        ("dmr", "ДМР"),
        ("kd", "КД"),
    ],
    "farmet-crusher": [
        ("um", "UM"),
        ("fantom", "Fantom"),
    ],
    "zernomet-std": [
        ("zps-60", "ЗПС-60"),
        ("zps-100", "ЗПС-100"),
    ],
    "pzm-thrower": [
        ("pzm-120", "ПЗМ-120"),
        ("pzm-90", "ПЗМ-90"),
    ],
    "zps-thrower": [
        ("zps-60", "ЗПС-60"),
        ("zps-100", "ЗПС-100"),
    ],
    "petkus-cleaner": [
        ("gigant", "Gigant"),
        ("v", "V"),
    ],
    "crippen-cleaner": [
        ("h", "H"),
        ("s", "S"),
    ],
    "ovs-cleaner": [
        ("ovs-25", "ОВС-25"),
        ("ovs-50", "ОВС-50"),
    ],
    "zav-cleaner": [
        ("zav-20", "ЗАВ-20"),
        ("zav-40", "ЗАВ-40"),
    ],
    "plenka-layer": [
        ("1r", "1-рядный"),
        ("2r", "2-рядный"),
    ],
    "bed-former": [
        ("bf-1", "BF-1"),
        ("bf-2", "BF-2"),
    ],
    "hortitec-layer": [
        ("ht", "HT"),
        ("pro", "Pro"),
    ],
    "bugor-std": [
        ("2r", "2-рядный"),
        ("4r", "4-рядный"),
    ],
    "grimme-ridge": [
        ("gf", "GF"),
        ("gh", "GH"),
    ],
    "baselier-ridge": [
        ("fk", "FK"),
        ("ridge", "Ridge"),
    ],
}
