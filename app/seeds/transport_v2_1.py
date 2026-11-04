# -*- coding: utf-8 -*-
"""Transport V2.1 catalog constants and desired L1/L2 active tree."""
from __future__ import annotations

from pathlib import Path

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / ".local" / "transport_v2_1_rollback"
MIGRATION_MARKER = "transport_v2_1_applied"

# L2 under transport — desired active order (sort_order unique, *10)
L1_ACTIVE: list[tuple[str, str, int]] = [
    ("transport-car-sale", "Продажа авто", 10),
    ("transport-auto-parts", "Автозапчасти", 20),
    ("transport-accessories-tuning", "Аксессуары и тюнинг", 30),
    ("transport-tires-wheels", "Шины и диски", 40),
    ("transport-auto-services", "Автоуслуги", 50),
    ("transport-moto-tech", "Мототехника", 60),
    ("transport-electric", "Электротранспорт", 70),
    ("transport-bicycles", "Велосипеды", 80),
    ("transport-buses-microbuses-motorhomes", "Автобусы, микроавтобусы и автодома", 90),
    ("transport-special-equipment", "Спецтехника", 100),
    ("transport-cargo", "Грузовой транспорт", 110),
    ("transport-watercraft", "Водный транспорт", 120),
    ("transport-trailers", "Прицепы и полуприцепы", 130),
    ("transport-farm-machinery", "Сельхозтехника", 140),
    ("transport-rental", "Аренда транспорта", 150),
]

# Entire branches deactivated (is_active=false); history kept.
# transport-auto-services is canonical active L2 (V2 tree cleanup) — not retired.
RETIRE_BRANCH_ROOT_SLUGS: frozenset[str] = frozenset(
    {
        "transport-commercial",
        "transport-buyback-exchange",
    }
)

# Canonical auto-services L3 (must stay active with parent).
AUTO_SERVICES_CHILD_SLUGS: tuple[str, ...] = (
    "transport-auto-services-remont-i-obsluzhivanie",
    "transport-auto-services-avtoelektrika",
    "transport-auto-services-kuzovnoy-remont",
    "transport-auto-services-deteyling-i-uhod",
    "transport-auto-services-shinomontazh",
    "transport-auto-services-evakuatsiya-i-pomosch-na-doroge",
    "transport-auto-services-tyuning-i-doosnaschenie",
    "transport-auto-services-avtostekla",
    "transport-auto-services-proverka-i-oformlenie",
    "transport-auto-services-gbo-gazoballonnoe-oborudovanie",
)

# Buses L2 children (existing IDs preserved; commercial rows re-parented).
BUSES_L2_CHILD_SLUGS: tuple[str, ...] = (
    "transport-commercial-avtobusy",
    "transport-commercial-mikroavtobusy",
    "transport-buses-avtodoma",
)

# Individual nodes to deactivate (plus handled via branch retire).
RETIRE_LEAF_SLUGS: frozenset[str] = frozenset(
    {
        "transport-commercial-pikapy",
        "transport-commercial-spetsavtomobili",
        "transport-commercial-malotonnazhnye-gruzoviki",
        "transport-commercial-furgony",
        "transport-commercial-zapchasti",
        "transport-commercial-remont-i-obsluzhivanie",
        # Buyback legacy children (parent stays inactive; no live IPAC leak)
        "transport-buyback-exchange-skupka-avtomobiley",
        "transport-buyback-exchange-skupka-kommercheskogo-transporta",
        "transport-buyback-exchange-skupka-gruzovogo-transporta",
        "transport-buyback-exchange-skupka-spetstehniki",
        "transport-buyback-exchange-skupka-mototehniki",
        "transport-buyback-exchange-obmen-transporta",
        "transport-buyback-exchange-vykup-posle-dtp",
        "transport-buyback-exchange-vykup-na-zapchasti",
        "transport-accessories-tuning-avtosvet-i-tyuning-optiki",
        "transport-accessories-tuning-elektronika-i-bezopasnost",
        "transport-accessories-tuning-aksessuary-kuzova",
        # Off-road / technical reactivated as Tuning V2 sections — not retired.
        "transport-accessories-tuning-instrumenty-i-avtoaksessuary",
        "transport-accessories-tuning-avtomobilnye-prinadlezhnosti",
        "transport-accessories-tuning-ekipirovka-moto-velo",
        "transport-accessories-tuning-vodnye-prinadlezhnosti",
        "transport-accessories-tuning-avtozvuk-i-multimediya",  # legacy slug after → avtozvuk
        "transport-accessories-tuning-sportivnyy-tyuning",  # legacy slug after → tehnicheskiy
        "transport-auto-parts-universalnye-detali",
        # e-motorcycle / e-ATV re-parented under Electric (V2) — not deactivated.
        "transport-moto-tech-elektroskutery",  # duplicate of Electric e-scooter leaf
        "transport-moto-tech-zapchasti-dlya-mototehniki",
        "transport-moto-tech-motouslugi",
        "transport-electric-elektrobaggi",
        "transport-electric-elektrokarty",
        "transport-electric-elektrotrayki",
        "transport-electric-zapchasti-dlya-elektrotransporta",
        "transport-electric-remont-i-obsluzhivanie",
        "transport-bicycles-detskie",
        "transport-bicycles-skladnye-velosipedy",
        "transport-bicycles-velozapchasti",
        "transport-bicycles-veloservis",
        "transport-special-equipment-evakuatory",
        "transport-special-equipment-dorozhnaya-tehnika",
        "transport-special-equipment-betonotehnika",
        "transport-special-equipment-zapchasti-dlya-spetstehniki",
        "transport-special-equipment-remont-i-obsluzhivanie",
        "transport-cargo-spetsgruzoviki",
        "transport-cargo-zapchasti",
        "transport-cargo-remont-i-obsluzhivanie",
        "transport-watercraft-naduvnye-lodki",
        # Boat Motor V2: keep active under Water — do NOT retire.
        "transport-watercraft-pritsepy-dlya-vodnogo-transporta",
        "transport-watercraft-zapchasti-i-komplektuyuschie",
        "transport-watercraft-remont-i-obsluzhivanie",
        "transport-trailers-dlya-legkovyh-avtomobiley",
        "transport-trailers-gruzovye-pritsepy",
        "transport-trailers-samosvalnye-pritsepy",
        "transport-trailers-tentovannye-pritsepy",
        "transport-trailers-refrizheratornye-pritsepy",
        "transport-trailers-tsisterny",
        "transport-trailers-traly-i-nizkoramnye",
        "transport-trailers-spetsializirovannye-pritsepy",
        "transport-trailers-zapchasti-i-komplektuyuschie",
        "transport-trailers-remont-i-obsluzhivanie",
        # Farm V2: implement L3 + legacy umbrellas stay inactive.
        "transport-farm-machinery-posevnaya-tehnika",
        "transport-farm-machinery-kartofelesazhalki",
        "transport-farm-machinery-plugi",
        "transport-farm-machinery-borony",
        "transport-farm-machinery-kultivatory",
        "transport-farm-machinery-okuchniki",
        "transport-farm-machinery-arychniki",
        "transport-farm-machinery-mulchery",
        "transport-farm-machinery-kosilki",
        "transport-farm-machinery-motokosilki",
        "transport-farm-machinery-press-podborshchiki",
        "transport-farm-machinery-zhatki",
        "transport-farm-machinery-grabli",
        "transport-farm-machinery-kormorazdatchiki",
        "transport-farm-machinery-opryskivateli",
        "transport-farm-machinery-razbrasyvateli-udobreniy",
        "transport-farm-machinery-navozorazbrasyvateli",
        "transport-farm-machinery-kartofelekopalki",
        "transport-farm-machinery-kuny",
        "transport-farm-machinery-drobilki",
        "transport-farm-machinery-zernometateli",
        "transport-farm-machinery-zernoochistiteli",
        "transport-farm-machinery-plenkoukladchiki",
        "transport-farm-machinery-bugoroobrazovateli",
        "transport-farm-machinery-navesnoe-oborudovanie",
        "transport-farm-machinery-pochvoobrabatyvayuschaya-tehnika",
        "transport-farm-machinery-tehnika-dlya-zagotovki-kormov",
        "transport-farm-machinery-pritsepy-dlya-selhoztehniki",
        "transport-farm-machinery-zapchasti-dlya-selhoztehniki",
        "transport-farm-machinery-remont-i-obsluzhivanie",
        "transport-rental-vnedorozhniki-i-krossovery",
        "transport-rental-kommercheskiy-transport",
        "transport-rental-arenda-s-voditelem",
        "transport-rental-dolgosrochnaya-arenda",
        "transport-moto-tech-ekipirovka-i-aksessuary",
        "transport-electric-aksessuary-dlya-elektrotransporta",
        "transport-bicycles-veloaksessuary",
        "transport-watercraft-aksessuary-i-oborudovanie",
    }
)

# Merge listing category_id remaps (source_slug → target_slug) when source has listings.
MERGE_LISTING_REMAP: dict[str, str] = {
    "transport-special-equipment-evakuatory": "transport-cargo-evakuatory",
    "transport-special-equipment-betonotehnika": "transport-special-equipment-avtobetonomehalki",
    "transport-special-equipment-dorozhnaya-tehnika": "transport-special-equipment-kommunalnaya-tehnika",
    "transport-commercial-furgony": "transport-cargo-furgony",
    "transport-commercial-malotonnazhnye-gruzoviki": "transport-cargo-malotonnazhnye",
    "transport-accessories-tuning-avtosvet-i-tyuning-optiki": "transport-auto-parts-optika-fary-i-fonari",
    # Electric motorcycle/ATV keep Electric identity (V2) — do NOT remap to ICE.
    "transport-moto-tech-elektroskutery": "transport-electric-elektroskutery",
    "transport-electric-elektrobaggi": "transport-moto-tech-baggi",
    "transport-electric-elektrokarty": "transport-moto-tech-karty",
    "transport-electric-elektrotrayki": "transport-moto-tech-tritsikly",
    # Boat Motor V2: no remap to auto engine — sale leaf stays under Water.
    # Trailers V2: boat/farm trailers → Прицепы leaf (not parent).
    "transport-watercraft-pritsepy-dlya-vodnogo-transporta": (
        "transport-trailers-pritsepy"
    ),
    "transport-farm-machinery-pritsepy-dlya-selhoztehniki": (
        "transport-trailers-pritsepy"
    ),
    # Farm V2: tillage/forage umbrellas + implements → broad implement.
    "transport-farm-machinery-pochvoobrabatyvayuschaya-tehnika": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-tehnika-dlya-zagotovki-kormov": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-navesnoe-oborudovanie": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-posevnaya-tehnika": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-kartofelesazhalki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-plugi": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-borony": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-kultivatory": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-okuchniki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-arychniki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-mulchery": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-kosilki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-motokosilki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-press-podborshchiki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-zhatki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-grabli": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-kormorazdatchiki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-opryskivateli": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-razbrasyvateli-udobreniy": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-navozorazbrasyvateli": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-kartofelekopalki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-kuny": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-drobilki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-zernometateli": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-zernoochistiteli": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-plenkoukladchiki": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-farm-machinery-bugoroobrazovateli": (
        "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
    ),
    "transport-moto-tech-zapchasti-dlya-mototehniki": "transport-auto-parts",
    "transport-electric-zapchasti-dlya-elektrotransporta": "transport-auto-parts",
    "transport-bicycles-velozapchasti": "transport-auto-parts",
    "transport-commercial-zapchasti": "transport-auto-parts",
    "transport-cargo-zapchasti": "transport-auto-parts",
    "transport-special-equipment-zapchasti-dlya-spetstehniki": "transport-auto-parts",
    "transport-watercraft-zapchasti-i-komplektuyuschie": "transport-auto-parts",
    "transport-trailers-zapchasti-i-komplektuyuschie": "transport-auto-parts",
    "transport-farm-machinery-zapchasti-dlya-selhoztehniki": "transport-auto-parts",
}

# Body children move under kuzov parent (slug keep).
BODY_CHILD_SLUGS: tuple[str, ...] = (
    "transport-auto-parts-kabina-perednyaya-chast-nouskat",
    "transport-auto-parts-bampery-i-komplektuyuschie",
    "transport-auto-parts-dveri-i-komplektuyuschie",
    "transport-auto-parts-kapoty-i-kryshki-bagazhnika",
    "transport-auto-parts-zerkala-i-komplektuyuschie",
    "transport-auto-parts-stekla-i-komplektuyuschie",
    "transport-auto-parts-optika-fary-i-fonari",
    "transport-auto-parts-reshetki-zhabo-i-naruzhnyy-plastik",
    "transport-auto-parts-krylya-i-podkrylki",
    "transport-auto-parts-bryzgoviki-i-zaschita-dnischa",
    "transport-auto-parts-silovye-elementy-kuzova",
)

# New categories to create if missing: (parent_slug, slug, name, sort_order)
NEW_CATEGORIES: list[tuple[str, str, str, int]] = [
    (
        "transport",
        "transport-buses-microbuses-motorhomes",
        "Автобусы, микроавтобусы и автодома",
        90,
    ),
    (
        "transport-buses-microbuses-motorhomes",
        "transport-buses-avtodoma",
        "Автодома",
        30,
    ),
    (
        "transport-auto-parts",
        "transport-auto-parts-rabochaya-gidravlika-i-pnevmatika",
        "Рабочая гидравлика и пневматика",
        160,
    ),
    (
        "transport-auto-parts",
        "transport-auto-parts-rabochie-organy-i-detali-navesnogo",
        "Рабочие органы и детали навесного оборудования",
        170,
    ),
    (
        "transport-auto-parts",
        "transport-auto-parts-elektroprivod-i-tyagovye-batarei",
        "Электропривод и тяговые батареи",
        180,
    ),
    (
        "transport-accessories-tuning",
        "transport-accessories-tuning-videoregistratory-kamery-parktroniki",
        "Видеорегистраторы, камеры и парктроники",
        20,
    ),
    (
        "transport-accessories-tuning",
        "transport-accessories-tuning-signalizatsii-i-protivougonnye",
        "Сигнализации и противоугонные устройства",
        30,
    ),
    (
        "transport-accessories-tuning",
        "transport-accessories-tuning-vneshnie-aksessuary-i-dekor",
        "Внешние аксессуары и декор",
        60,
    ),
    (
        "transport-accessories-tuning",
        "transport-accessories-tuning-uhod-i-avtohimiya",
        "Уход и автохимия",
        70,
    ),
    (
        "transport-accessories-tuning",
        "transport-accessories-tuning-avtomobilnye-prinadlezhnosti",
        "Автомобильные принадлежности",
        80,
    ),
    (
        "transport-accessories-tuning",
        "transport-accessories-tuning-ekipirovka-moto-velo",
        "Экипировка для мото- и велотехники",
        90,
    ),
    (
        "transport-accessories-tuning",
        "transport-accessories-tuning-vodnye-prinadlezhnosti",
        "Водные принадлежности",
        100,
    ),
    (
        "transport-moto-tech",
        "transport-moto-tech-motorollery-muravey",
        "Мотороллеры «Муравей»",
        25,
    ),
    ("transport-moto-tech", "transport-moto-tech-tritsikly", "Трициклы", 50),
    ("transport-moto-tech", "transport-moto-tech-karty", "Картинги", 70),
    ("transport-moto-tech", "transport-moto-tech-drugaya-mototehnika", "Другая мототехника", 80),
    (
        "transport-electric",
        "transport-electric-elektroskutery",
        "Электроскутеры",
        15,
    ),
    (
        "transport-bicycles",
        "transport-bicycles-podrostkovye-velosipedy",
        "Подростковые",
        40,
    ),
    (
        "transport-bicycles",
        "transport-bicycles-elektrovelosipedy",
        "Электровелосипеды",
        45,
    ),
    ("transport-bicycles", "transport-bicycles-bmx", "BMX", 50),
    ("transport-bicycles", "transport-bicycles-drugie", "Другие велосипеды", 60),
    ("transport-cargo", "transport-cargo-refrizheratory", "Рефрижераторы", 45),
    ("transport-cargo", "transport-cargo-malotonnazhnye", "Легкий грузовой", 48),
    ("transport-cargo", "transport-cargo-tsisterny", "Цистерны", 50),
    ("transport-cargo", "transport-cargo-evakuatory", "Эвакуаторы", 60),
    ("transport-cargo", "transport-cargo-drugie-gruzoviki", "Другие грузовики", 70),
    (
        "transport-special-equipment",
        "transport-special-equipment-vilochnye-pogruzchiki",
        "Вилочные погрузчики",
        25,
    ),
    (
        "transport-special-equipment",
        "transport-special-equipment-avtobetonomehalki",
        "Автобетономешалки",
        95,
    ),
    (
        "transport-special-equipment",
        "transport-special-equipment-betononasosy",
        "Бетононасосы",
        96,
    ),
    (
        "transport-special-equipment",
        "transport-special-equipment-assenizatory",
        "Ассенизаторы",
        97,
    ),
    (
        "transport-special-equipment",
        "transport-special-equipment-mini-dumper",
        "Мини-думпер",
        105,
    ),
    (
        "transport-special-equipment",
        "transport-special-equipment-navesnoe-i-rabochee-oborudovanie",
        "Навесное и рабочее оборудование",
        130,
    ),
    (
        "transport-special-equipment",
        "transport-special-equipment-drugaya-spetstehnika",
        "Другая спецтехника",
        140,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-motobloki-i-motokultivatory",
        "Мотоблоки и мотокультиваторы",
        15,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-mini-traktory",
        "Мини-тракторы",
        12,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-agrodrony",
        "Агродроны",
        70,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-kartofelesazhalki",
        "Картофелесажалки",
        32,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-plugi",
        "Плуги",
        40,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-borony",
        "Бороны",
        41,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-kultivatory",
        "Культиваторы",
        42,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-okuchniki",
        "Окучники",
        43,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-arychniki",
        "Арычники",
        44,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-mulchery",
        "Мульчеры",
        45,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-kosilki",
        "Косилки",
        50,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-motokosilki",
        "Мотокосилки",
        51,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-press-podborshchiki",
        "Пресс-подборщики",
        52,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-zhatki",
        "Жатки",
        53,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-grabli",
        "Грабли",
        54,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-kormorazdatchiki",
        "Кормораздатчики",
        55,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-razbrasyvateli-udobreniy",
        "Разбрасыватели удобрений",
        61,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-navozorazbrasyvateli",
        "Навозоразбрасыватели",
        62,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-kartofelekopalki",
        "Картофелекопалки",
        63,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-kuny",
        "КУНы",
        64,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-drobilki",
        "Дробилки",
        65,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-zernometateli",
        "Зернометатели",
        66,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-zernoochistiteli",
        "Зерноочистители",
        67,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-plenkoukladchiki",
        "Пленкоукладчики и грядообразователи",
        68,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-bugoroobrazovateli",
        "Бугорообразователи",
        69,
    ),
    (
        "transport-farm-machinery",
        "transport-farm-machinery-drugaya-selhoztehnika",
        "Другая сельхозтехника",
        80,
    ),
    (
        "transport-watercraft",
        "transport-watercraft-drugoy-vodnyy-transport",
        "Другой водный транспорт",
        50,
    ),
    ("transport-trailers", "transport-trailers-pritsepy", "Прицепы", 10),
    (
        "transport-trailers",
        "transport-trailers-zhilye-pritsepy-kempery",
        "Жилые прицепы / кемперы",
        30,
    ),
]

# Rename display names (slug → new name); slug unchanged.
RENAME_NAMES: dict[str, str] = {
    "transport-auto-parts": "Автозапчасти",
    "transport-auto-parts-kuzovnye-detali": "Кузов и наружные детали",
    "transport-auto-parts-toplivnaya-sistema": "Топливная система и ГБО",
    "transport-auto-parts-krepezh-rezinki-i-melkie-detali": "Крепёж и монтажные материалы",
    "transport-auto-parts-masla-zhidkosti-i-rashodniki": "Масла, смазки и технические жидкости",
    "transport-auto-parts-drugoe": "Прочие запчасти",
    "transport-accessories-tuning-avtozvuk": "Автозвук",
    "transport-accessories-tuning-aksessuary-salona": "Салон и комфорт",
    "transport-accessories-tuning-bagazhniki-i-perevozka": "Багажные системы",
    "transport-accessories-tuning-drugoe": "Другие аксессуары",
    "transport-accessories-tuning-signalizatsii-i-protivougonnye": (
        "Охрана и противоугонные системы"
    ),
    "transport-accessories-tuning-vneshnie-aksessuary-i-dekor": (
        "Внешний тюнинг и аксессуары"
    ),
    "transport-accessories-tuning-uhod-i-avtohimiya": (
        "Уход, автохимия и полезные принадлежности"
    ),
    "transport-accessories-tuning-vnedorozhnyy-tyuning": (
        "Внедорожный тюнинг и защита"
    ),
    "transport-accessories-tuning-tehnicheskiy-tyuning": "Технический тюнинг",
    "transport-accessories-tuning-multimedia": "Мультимедиа",
    "transport-accessories-tuning-svet-i-dopolnitelnoe-osveschenie": (
        "Свет и дополнительное освещение"
    ),
    "transport-accessories-tuning-plenki-i-materialy": (
        "Плёнки и материалы для авто"
    ),
    "transport-electric-elektricheskie-mini-mobili": "Гольфкары и электрические мини-мобили",
    "transport-electric-drugoy-redkiy-elektrotransport": "Другой электротранспорт",
    "transport-electric-sigvei-i-mini-sigvei": "Сигвеи",
    "transport-bicycles-gornye-velosipedy": "Горные",
    "transport-bicycles-gorodskie-velosipedy": "Городские",
    "transport-bicycles-shosseynye-velosipedy": "Шоссейные",
    "transport-bicycles-podrostkovye-velosipedy": "Подростковые",
    "transport-bicycles-elektrovelosipedy": "Электровелосипеды",
    "transport-bicycles-bmx": "BMX",
    "transport-bicycles-drugie": "Другие велосипеды",
    "transport-special-equipment-drobilno-sortirovochnaya-tehnika": "Дробильно-сортировочная техника",
    "transport-special-equipment-kommunalnaya-tehnika": "Коммунальная и дорожная техника",
    "transport-commercial-avtobusy": "Автобусы",
    "transport-commercial-mikroavtobusy": "Микроавтобусы",
    "transport-cargo-malotonnazhnye": "Легкий грузовой",
    "transport-trailers-polupritsepy": "Полуприцепы",
    "transport-farm-machinery-posevnaya-tehnika": "Сеялки",
}

# Move existing nodes: slug → new_parent_slug
MOVE_PARENT: dict[str, str] = {
    "transport-commercial-avtobusy": "transport-buses-microbuses-motorhomes",
    "transport-commercial-mikroavtobusy": "transport-buses-microbuses-motorhomes",
}

# Alias retarget: alias text → category slug (for light)
ALIAS_RETARGET: dict[str, str] = {
    "фара": "transport-auto-parts-optika-fary-i-fonari",
    "оптика": "transport-auto-parts-optika-fary-i-fonari",
    "фонарь": "transport-auto-parts-optika-fary-i-fonari",
}

# Parts Step 1 — vehicle applicability (stable machine values + RU labels).
# One shared Запчасти catalog; selection is context, not a category tree fork.
PARTS_VEHICLE_APPLICABILITY_OPTIONS: list[tuple[str, str]] = [
    ("passenger_cars", "Легковые автомобили"),
    ("cargo", "Грузовой транспорт"),
    ("buses", "Автобусы"),
    ("special_equipment", "Спецтехника"),
    ("farm_machinery", "Сельхозтехника"),
    ("moto", "Мототехника"),
    ("electric", "Электротранспорт"),
    ("bicycles", "Велосипеды"),
    ("watercraft", "Водный транспорт"),
    ("trailers", "Прицепы"),
]


def parts_vehicle_applicability_options_json() -> dict:
    """JSONB shape for category_core_fields.options / category_filters.config."""
    return {
        "values": [
            {"value": value, "label": label}
            for value, label in PARTS_VEHICLE_APPLICABILITY_OPTIONS
        ]
    }


# Pending Services mapping notes (no new Services nodes created).
SERVICES_PENDING: dict[str, str] = {
    "transport-auto-services": "pending: Services transport maintenance leaf not approved",
    "transport-auto-services-shinomontazh": "pending: tire service leaf",
    "transport-auto-services-evakuatsiya-i-pomosch-na-doroge": "pending: roadside assistance leaf",
    "transport-rental-arenda-s-voditelem": "candidate: services-gruzoperevozki-i-pereezdy / passenger",
    "transport-special-equipment-remont-i-obsluzhivanie": "candidate: services-uslugi-spetstehniki",
}
