# -*- coding: utf-8 -*-
"""Real Estate V2 — canonical property-leaf Backend SoT.

UX freeze: Недвижимость → property → deal → (commercial direction) → fields.
Canonical publishable homes are property leaves; deal_type is structured data.
Legacy deal categories (sale/rent/commercial) and unused skeletons are retired.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import CONTACT_METHOD_CHOICES

ROOT_SLUG = "real-estate"
ROOT_ID = 601

# Canonical property leaves (reuse existing IDs where safe).
APARTMENTS_ID = 863
APARTMENTS_SLUG = "real-estate-kvartiry"
HOUSES_ID = 864
HOUSES_SLUG = "real-estate-doma-i-kottedzhi"  # keep stable slug; display = «Дома» (UX)
ROOMS_ID = 866
ROOMS_SLUG = "real-estate-komnaty"
LAND_ID = 868
LAND_SLUG = "real-estate-zemelnye-uchastki"
COMMERCIAL_ID = 867
COMMERCIAL_SLUG = "real-estate-kommercheskaya-nedvizhimost"
# 869 was combined «Гаражи и парковки» → becomes Garages only.
GARAGES_ID = 869
GARAGES_SLUG = "real-estate-garazhi"
GARAGES_LABEL = "Гаражи"
# New Parking leaf (created in migration if missing).
PARKING_SLUG = "real-estate-parkovki"
PARKING_LABEL = "Парковки"

CANONICAL_LEAF_SLUGS: tuple[str, ...] = (
    APARTMENTS_SLUG,
    HOUSES_SLUG,
    ROOMS_SLUG,
    LAND_SLUG,
    COMMERCIAL_SLUG,
    GARAGES_SLUG,
    PARKING_SLUG,
)

CANONICAL_LEAF_LABELS: dict[str, str] = {
    APARTMENTS_SLUG: "Квартиры",
    HOUSES_SLUG: "Дома",
    ROOMS_SLUG: "Комнаты",
    LAND_SLUG: "Земельные участки",
    COMMERCIAL_SLUG: "Коммерческая недвижимость",
    GARAGES_SLUG: GARAGES_LABEL,
    PARKING_SLUG: PARKING_LABEL,
}

CANONICAL_LEAF_SORT: dict[str, int] = {
    APARTMENTS_SLUG: 10,
    HOUSES_SLUG: 20,
    ROOMS_SLUG: 40,
    LAND_SLUG: 60,
    COMMERCIAL_SLUG: 50,
    GARAGES_SLUG: 70,
    PARKING_SLUG: 75,
}

# Retired: legacy deal homes + unused skeletons (keep IDs, deactivate).
LEGACY_DEAL_SLUGS: frozenset[str] = frozenset(
    {
        "real-estate-sale",
        "real-estate-rent",
        "real-estate-commercial",
    }
)
LEGACY_DEAL_IDS: tuple[int, ...] = (602, 603, 604)

RETIRED_SKELETON_SLUGS: frozenset[str] = frozenset(
    {
        "real-estate-novostroyki",  # 865 → Apartment subtype new_build
        "real-estate-dachi-i-zagorodnaya-nedvizhimost",
        "real-estate-nedvizhimost-za-rubezhom",
        "real-estate-obmen-nedvizhimosti",
        "real-estate-garazhi-i-parkovki",  # old combined slug after rename
    }
)
RETIRED_SKELETON_IDS: tuple[int, ...] = (865, 870, 871, 872)

RETIRED_REAL_ESTATE_SLUGS: frozenset[str] = LEGACY_DEAL_SLUGS | RETIRED_SKELETON_SLUGS

# ---------------------------------------------------------------------------
# Option helpers
# ---------------------------------------------------------------------------


def _pair_choices(*pairs: tuple[str, str]) -> dict[str, Any]:
    items = [{"value": v, "label": lab} for v, lab in pairs]
    return {"choices": items, "values": items}


def _items_choices(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"choices": items, "values": items}


def _depends(field: str, show_values: list[str]) -> dict[str, Any]:
    return {"depends_on": {"field": field, "values": show_values}}


DEAL_LABELS: dict[str, dict[str, str]] = {
    "apartments": {
        "rent": "Квартиры в аренду",
        "sell": "Продажа квартир",
        "buy": "Куплю квартиру",
        "want_rent": "Сниму квартиру"
    },
    "houses": {
        "rent": "Дома в аренду",
        "sell": "Дома на продажу",
        "buy": "Куплю дом",
        "want_rent": "Сниму дом"
    },
    "rooms": {
        "rent": "Комнаты в аренду",
        "rent_bed": "Сдам койко-место",
        "want_rent": "Сниму комнату",
        "want_rent_bed": "Сниму койко-место"
    },
    "land": {
        "rent": "Участки в аренду",
        "sell": "Участки на продажу",
        "buy": "Куплю участок",
        "want_rent": "Сниму участок"
    },
    "commercial": {
        "rent": "Аренда коммерческой недвижимости",
        "sell": "Продажа коммерческой недвижимости",
        "buy": "Куплю коммерческую недвижимость",
        "want_rent": "Сниму коммерческую недвижимость"
    },
    "garages": {
        "rent": "Гаражи в аренду",
        "sell": "Гаражи на продажу",
        "buy": "Куплю гараж",
        "want_rent": "Сниму гараж"
    },
    "parking": {
        "rent": "Парковки в аренду",
        "sell": "Парковки на продажу",
        "buy": "Куплю парковку",
        "want_rent": "Сниму парковку"
    }
}

COMMERCIAL_DIRECTION_ITEMS: list[dict[str, Any]] = [
  {
    "value": "mall_boutique",
    "label": "Продажа бутиков и островков в торговых центрах",
    "label_by_deal": {
      "sell": "Продажа бутиков и островков в торговых центрах",
      "rent": "Аренда бутиков и островков в торговых центрах",
      "buy": "Куплю бутик или островок в торговом центре",
      "want_rent": "Сниму бутик или островок в торговом центре"
    }
  },
  {
    "value": "market_place",
    "label": "Продажа помещений, контейнеров и торговых мест на рынках",
    "label_by_deal": {
      "sell": "Продажа помещений, контейнеров и торговых мест на рынках",
      "rent": "Аренда помещений, контейнеров и торговых мест на рынках",
      "buy": "Куплю помещение, контейнер или торговое место на рынке",
      "want_rent": "Сниму помещение, контейнер или торговое место на рынке"
    }
  },
  {
    "value": "residential_commercial",
    "label": "Продажа коммерческих помещений в жилых домах",
    "label_by_deal": {
      "sell": "Продажа коммерческих помещений в жилых домах",
      "rent": "Аренда коммерческих помещений в жилых домах",
      "buy": "Куплю коммерческое помещение в жилом доме",
      "want_rent": "Сниму коммерческое помещение в жилом доме"
    }
  },
  {
    "value": "street_retail",
    "label": "Продажа уличных торговых точек",
    "label_by_deal": {
      "sell": "Продажа уличных торговых точек",
      "rent": "Аренда уличных торговых точек",
      "buy": "Куплю уличную торговую точку",
      "want_rent": "Сниму уличную торговую точку"
    }
  },
  {
    "value": "office_coworking",
    "label": "Продажа офисов, коворкингов и конференц-залов",
    "label_by_deal": {
      "sell": "Продажа офисов, коворкингов и конференц-залов",
      "rent": "Аренда офисов, коворкингов и конференц-залов",
      "buy": "Куплю офис, коворкинг или конференц-зал",
      "want_rent": "Сниму офис, место в коворкинге или конференц-зал"
    }
  },
  {
    "value": "beauty_salon_space",
    "label": "Продажа кабинетов, мест и помещений в салонах красоты",
    "label_by_deal": {
      "sell": "Продажа кабинетов, мест и помещений в салонах красоты",
      "rent": "Аренда кабинетов, мест и кресел в салонах красоты",
      "buy": "Куплю кабинет или помещение под салон красоты",
      "want_rent": "Сниму кабинет, место или кресло в салоне красоты"
    }
  },
  {
    "value": "medical_center_space",
    "label": "Продажа кабинетов и помещений в медицинских центрах",
    "label_by_deal": {
      "sell": "Продажа кабинетов и помещений в медицинских центрах",
      "rent": "Аренда кабинетов и мест в медицинских центрах",
      "buy": "Куплю кабинет или помещение под медицинский центр",
      "want_rent": "Сниму кабинет или место в медицинском центре"
    }
  },
  {
    "value": "auto_business_space",
    "label": "Продажа помещений для автобизнеса и автосервиса",
    "label_by_deal": {
      "sell": "Продажа помещений для автобизнеса и автосервиса",
      "rent": "Аренда помещений для автобизнеса и автосервиса",
      "buy": "Куплю помещение для автобизнеса или автосервиса",
      "want_rent": "Сниму помещение для автобизнеса или автосервиса"
    }
  },
  {
    "value": "production_facility",
    "label": "Продажа производственных помещений, цехов, заводов и фабрик",
    "label_by_deal": {
      "sell": "Продажа производственных помещений, цехов, заводов и фабрик",
      "rent": "Аренда производственных помещений, цехов, заводов и фабрик",
      "buy": "Куплю производственное помещение, цех, завод или фабрику",
      "want_rent": "Сниму производственное помещение, цех, завод или фабрику"
    }
  },
  {
    "value": "warehouse_logistics",
    "label": "Продажа складов и помещений для хранения и логистики",
    "label_by_deal": {
      "sell": "Продажа складов и помещений для хранения и логистики",
      "rent": "Аренда складов и помещений для хранения и логистики",
      "buy": "Куплю склад или помещение для хранения и логистики",
      "want_rent": "Сниму склад или помещение для хранения и логистики"
    }
  },
  {
    "value": "horeca",
    "label": "Продажа помещений под общепит, кафе, рестораны и банкетные залы",
    "label_by_deal": {
      "sell": "Продажа помещений под общепит, кафе, рестораны и банкетные залы",
      "rent": "Аренда помещений под общепит, кафе, рестораны и банкетные залы",
      "buy": "Куплю помещение под общепит, кафе, ресторан или банкетный зал",
      "want_rent": "Сниму помещение под общепит, кафе, ресторан или банкетный зал"
    }
  },
  {
    "value": "entertainment",
    "label": "Продажа помещений под развлекательные и игровые центры",
    "label_by_deal": {
      "sell": "Продажа помещений под развлекательные и игровые центры",
      "rent": "Аренда помещений под развлекательные и игровые центры",
      "buy": "Куплю помещение под развлекательный или игровой центр",
      "want_rent": "Сниму помещение под развлекательный или игровой центр"
    }
  },
  {
    "value": "sports_leisure",
    "label": "Продажа помещений для спорта, танцев и отдыха",
    "label_by_deal": {
      "sell": "Продажа помещений для спорта, танцев и отдыха",
      "rent": "Аренда помещений для спорта, танцев и отдыха",
      "buy": "Куплю помещение для спорта, танцев или отдыха",
      "want_rent": "Сниму помещение для спорта, танцев или отдыха"
    }
  },
  {
    "value": "education_space",
    "label": "Продажа помещений, кабинетов и классов для обучения",
    "label_by_deal": {
      "sell": "Продажа помещений, кабинетов и классов для обучения",
      "rent": "Аренда помещений, кабинетов и классов для обучения",
      "buy": "Куплю помещение для учебного центра или обучения",
      "want_rent": "Сниму помещение, кабинет или класс для обучения"
    }
  },
  {
    "value": "hospitality",
    "label": "Продажа гостиниц, хостелов и гостевых домов",
    "label_by_deal": {
      "sell": "Продажа гостиниц, хостелов и гостевых домов",
      "rent": "Аренда гостиниц, хостелов и гостевых домов",
      "buy": "Куплю гостиницу, хостел или гостевой дом",
      "want_rent": "Сниму гостиницу, хостел или гостевой дом"
    }
  },
  {
    "value": "building_parts",
    "label": "Продажа зданий, частей зданий, подвальных и цокольных помещений",
    "label_by_deal": {
      "sell": "Продажа зданий, частей зданий, подвальных и цокольных помещений",
      "rent": "Аренда зданий, частей зданий, подвальных и цокольных помещений",
      "buy": "Куплю здание, часть здания, подвальное или цокольное помещение",
      "want_rent": "Сниму здание, часть здания, подвальное или цокольное помещение"
    }
  },
  {
    "value": "base_territory",
    "label": "Продажа баз, территорий и площадок",
    "label_by_deal": {
      "sell": "Продажа баз, территорий и площадок",
      "rent": "Аренда баз, территорий и площадок",
      "buy": "Куплю базу, территорию или площадку",
      "want_rent": "Сниму базу, территорию или площадку"
    }
  },
  {
    "value": "free_purpose",
    "label": "Продажа помещений свободного назначения",
    "label_by_deal": {
      "sell": "Продажа помещений свободного назначения",
      "rent": "Аренда помещений свободного назначения",
      "buy": "Куплю помещение свободного назначения",
      "want_rent": "Сниму помещение свободного назначения"
    }
  },
  {
    "value": "other_commercial",
    "label": "Другая коммерческая недвижимость",
    "label_by_deal": {
      "sell": "Другая коммерческая недвижимость",
      "rent": "Другая коммерческая недвижимость",
      "buy": "Другая коммерческая недвижимость",
      "want_rent": "Другая коммерческая недвижимость"
    }
  }
]

DISTRICT_BY_CITY: dict[str, list[dict[str, str]]] = {
  "Бишкек": [
    {
      "value": "mkr_3",
      "label": "3 мкр."
    },
    {
      "value": "mkr_4",
      "label": "4 мкр."
    },
    {
      "value": "mkr_5",
      "label": "5 мкр."
    },
    {
      "value": "mkr_6",
      "label": "6 мкр."
    },
    {
      "value": "mkr_7",
      "label": "7 мкр."
    },
    {
      "value": "mkr_8",
      "label": "8 мкр."
    },
    {
      "value": "mkr_9",
      "label": "9 мкр."
    },
    {
      "value": "mkr_10",
      "label": "10 мкр."
    },
    {
      "value": "mkr_11",
      "label": "11 мкр."
    },
    {
      "value": "mkr_12",
      "label": "12 мкр."
    },
    {
      "value": "d011_42429",
      "label": "110 квартал"
    },
    {
      "value": "d012_52647",
      "label": "1000 мелочей"
    },
    {
      "value": "d013_16406",
      "label": "АУЦА"
    },
    {
      "value": "d014_88873",
      "label": "АЮ Гранд"
    },
    {
      "value": "d015_72324",
      "label": "ж/м Адилет"
    },
    {
      "value": "d016_36397",
      "label": "Академия наук"
    },
    {
      "value": "d017_35050",
      "label": "ж/м Ак-Бата"
    },
    {
      "value": "d018_79742",
      "label": "ж/м Ак-Босого"
    },
    {
      "value": "d019_43039",
      "label": "ж/м Ак-Жар"
    },
    {
      "value": "d020_27236",
      "label": "Ак-Кеме"
    },
    {
      "value": "d021_67801",
      "label": "ж/м Ак-Орго"
    },
    {
      "value": "d022_65240",
      "label": "ж/м Ак-Ордо 1"
    },
    {
      "value": "d023_92060",
      "label": "ж/м Ак-Ордо 2"
    },
    {
      "value": "d024_96286",
      "label": "ж/м Ак-Ордо 3"
    },
    {
      "value": "d025_41054",
      "label": "ж/м Ак-Тилек"
    },
    {
      "value": "d026_70297",
      "label": "Ак-Эмир рынок"
    },
    {
      "value": "d027_88572",
      "label": "ж/м Ала-Арча"
    },
    {
      "value": "d028_08079",
      "label": "ТРЦ Ала-Арча"
    },
    {
      "value": "d029_27986",
      "label": "ж/м Ала-Тоо"
    },
    {
      "value": "d030_92859",
      "label": "Мкр. Аламедин-1"
    },
    {
      "value": "d031_45685",
      "label": "Аламединский рынок"
    },
    {
      "value": "d032_68500",
      "label": "с. Аламудун"
    },
    {
      "value": "d033_84570",
      "label": "ж/м Алтын-Казык"
    },
    {
      "value": "d034_37161",
      "label": "ж/м Алтын-Ордо"
    },
    {
      "value": "d035_57256",
      "label": "ж/м Анар-Бак"
    },
    {
      "value": "d036_68802",
      "label": "ж/м Арча-Бешик"
    },
    {
      "value": "d037_85834",
      "label": "Мкр. Асанбай"
    },
    {
      "value": "d038_51453",
      "label": "ж/м Аска-Таш"
    },
    {
      "value": "d039_22730",
      "label": "ж/м Ата-Журт"
    },
    {
      "value": "d040_74962",
      "label": "Авторынок Азамат"
    },
    {
      "value": "d041_83664",
      "label": "Аэропорт Манас"
    },
    {
      "value": "d042_78468",
      "label": "БГУ"
    },
    {
      "value": "d043_84258",
      "label": "ж/м Бакай-Ата"
    },
    {
      "value": "d044_46213",
      "label": "Баткенский рынок"
    },
    {
      "value": "d045_97455",
      "label": "Бета Сторес"
    },
    {
      "value": "d046_37472",
      "label": "Бета Сторес 2"
    },
    {
      "value": "d047_69092",
      "label": "ж/м Биримдик-Кут"
    },
    {
      "value": "d048_72577",
      "label": "Бишкек Арена"
    },
    {
      "value": "d049_06865",
      "label": "ТРЦ Бишкек Парк"
    },
    {
      "value": "d050_15954",
      "label": "Ботанический сад"
    },
    {
      "value": "d051_92268",
      "label": "Браво коттеджный городок"
    },
    {
      "value": "d052_58359",
      "label": "ж/м Бугу-Эне-Багыш"
    },
    {
      "value": "d053_33781",
      "label": "ж/м Бугу-Эне-Сай"
    },
    {
      "value": "d054_56957",
      "label": "Бульвар Эркиндик"
    },
    {
      "value": "d055_11150",
      "label": "ВДНХ"
    },
    {
      "value": "d056_29075",
      "label": "Верхний Джал"
    },
    {
      "value": "d057_64986",
      "label": "с. Верхний Орок"
    },
    {
      "value": "d058_46027",
      "label": "ТРЦ Вефа"
    },
    {
      "value": "d059_18200",
      "label": "Вечёрка"
    },
    {
      "value": "d060_97443",
      "label": "с. Виноградное"
    },
    {
      "value": "d061_79949",
      "label": "Военный городок"
    },
    {
      "value": "d062_89536",
      "label": "Военторг"
    },
    {
      "value": "d063_32120",
      "label": "с. Восток"
    },
    {
      "value": "d064_72680",
      "label": "Мкр. Восток-5"
    },
    {
      "value": "d065_02985",
      "label": "Восточный автовокзал"
    },
    {
      "value": "d066_36587",
      "label": "Газ Городок"
    },
    {
      "value": "d067_89196",
      "label": "Гоин"
    },
    {
      "value": "d068_64939",
      "label": "Городок Айкол"
    },
    {
      "value": "d069_01823",
      "label": "Городок Энергетиков"
    },
    {
      "value": "d070_80216",
      "label": "Городок строителей"
    },
    {
      "value": "d071_06403",
      "label": "Городская больница №4"
    },
    {
      "value": "d072_95182",
      "label": "Городское ГАИ"
    },
    {
      "value": "d073_32704",
      "label": "Госрегистр"
    },
    {
      "value": "d074_79036",
      "label": "ГЭС-1"
    },
    {
      "value": "d075_77216",
      "label": "ГЭС-2"
    },
    {
      "value": "d076_98446",
      "label": "ГЭС-3"
    },
    {
      "value": "d077_40947",
      "label": "ГЭС-4"
    },
    {
      "value": "d078_51911",
      "label": "ГЭС-5"
    },
    {
      "value": "d079_38577",
      "label": "ГЭС-6"
    },
    {
      "value": "d080_30418",
      "label": "ГЭС-7"
    },
    {
      "value": "d081_59214",
      "label": "ГЭС-8"
    },
    {
      "value": "d082_17529",
      "label": "ГЭС-9"
    },
    {
      "value": "d083_08571",
      "label": "ГЭС-10"
    },
    {
      "value": "d084_78313",
      "label": "с. Дача СУ"
    },
    {
      "value": "d085_98273",
      "label": "Дворец спорта"
    },
    {
      "value": "d086_62921",
      "label": "Детский мир"
    },
    {
      "value": "d087_90372",
      "label": "Джал-15"
    },
    {
      "value": "d088_34110",
      "label": "Нижний Джал (Джал-23)"
    },
    {
      "value": "d089_83099",
      "label": "Джал-29"
    },
    {
      "value": "d090_08036",
      "label": "Джальская больница"
    },
    {
      "value": "d091_08639",
      "label": "Джунхай рынок"
    },
    {
      "value": "d092_24217",
      "label": "ж/м Дордой"
    },
    {
      "value": "d093_50073",
      "label": "ж/м Дордой-2"
    },
    {
      "value": "d094_13988",
      "label": "Дордой Моторс"
    },
    {
      "value": "d095_63616",
      "label": "ТРЦ Дордой Плаза"
    },
    {
      "value": "d096_49471",
      "label": "Дордой рынок"
    },
    {
      "value": "d097_62402",
      "label": "Мкр. Достук"
    },
    {
      "value": "d098_87086",
      "label": "с. Достук"
    },
    {
      "value": "d099_73913",
      "label": "Дубовый парк"
    },
    {
      "value": "d100_82225",
      "label": "с. Жаны жер"
    },
    {
      "value": "d101_19743",
      "label": "ЖД вокзал"
    },
    {
      "value": "d102_49645",
      "label": "ЗАГС / Цирк"
    },
    {
      "value": "d103_49448",
      "label": "Западный автовокзал"
    },
    {
      "value": "d104_59651",
      "label": "Заря"
    },
    {
      "value": "d105_12337",
      "label": "Золотой квадрат"
    },
    {
      "value": "d106_74866",
      "label": "Интергельпо"
    },
    {
      "value": "d107_15560",
      "label": "Ипподром"
    },
    {
      "value": "d108_17248",
      "label": "КНУ"
    },
    {
      "value": "d109_25040",
      "label": "ж/м Кайынды"
    },
    {
      "value": "d110_30375",
      "label": "с. Калтар"
    },
    {
      "value": "d111_22833",
      "label": "ж/м Калыс-Ордо"
    },
    {
      "value": "d112_37743",
      "label": "ж/м Кара-Жыгач"
    },
    {
      "value": "d113_71618",
      "label": "ТЦ Караван"
    },
    {
      "value": "d114_07171",
      "label": "Карагачёвая роща"
    },
    {
      "value": "d115_96065",
      "label": "Карпинка"
    },
    {
      "value": "d116_36998",
      "label": "с. Кашка-Баш"
    },
    {
      "value": "d117_99821",
      "label": "ж/м Келечек"
    },
    {
      "value": "d118_63565",
      "label": "ж/м Керемет"
    },
    {
      "value": "d119_81120",
      "label": "с. Кернивоз"
    },
    {
      "value": "d120_53143",
      "label": "Киргизия 1"
    },
    {
      "value": "d121_54993",
      "label": "ж/м Киргизия 2"
    },
    {
      "value": "d122_54513",
      "label": "Киркомстром"
    },
    {
      "value": "d123_64389",
      "label": "Кирпичный завод"
    },
    {
      "value": "d124_16873",
      "label": "Стадион Кожомкул"
    },
    {
      "value": "d125_88820",
      "label": "ж/м Кок-Жар"
    },
    {
      "value": "d126_28197",
      "label": "Мкр. Кок-Жар"
    },
    {
      "value": "d127_19597",
      "label": "ж/м Колмо"
    },
    {
      "value": "d128_15587",
      "label": "с. Комсомольское"
    },
    {
      "value": "d129_73283",
      "label": "Космос"
    },
    {
      "value": "d130_22166",
      "label": "ж/м Красный Строитель"
    },
    {
      "value": "d131_72654",
      "label": "ж/м Красный Строитель 2"
    },
    {
      "value": "d132_38590",
      "label": "Авторынок Кудайберген"
    },
    {
      "value": "d133_42723",
      "label": "Кызыл Аскер"
    },
    {
      "value": "d134_97001",
      "label": "ж/м Кырман"
    },
    {
      "value": "d135_71516",
      "label": "Лебединовка"
    },
    {
      "value": "d136_79542",
      "label": "с. Лесное"
    },
    {
      "value": "d137_19034",
      "label": "Мадина рынок"
    },
    {
      "value": "d138_35844",
      "label": "с. Маевка"
    },
    {
      "value": "d139_82200",
      "label": "с. Манас"
    },
    {
      "value": "d140_69092",
      "label": "ТЦ Мега Комфорт"
    },
    {
      "value": "d141_53003",
      "label": "Мед Академия"
    },
    {
      "value": "d142_44230",
      "label": "Молодая Гвардия"
    },
    {
      "value": "d143_99743",
      "label": "Моссовет"
    },
    {
      "value": "d144_51881",
      "label": "с. Мраморное"
    },
    {
      "value": "d145_64117",
      "label": "ж/м Мурас-Ордо"
    },
    {
      "value": "d146_71167",
      "label": "с. Мыкан"
    },
    {
      "value": "d147_62120",
      "label": "с. Нижний Орок"
    },
    {
      "value": "d148_04264",
      "label": "с. Нижняя Ала-Арча"
    },
    {
      "value": "d149_12599",
      "label": "Новая мечеть (центральный)"
    },
    {
      "value": "d150_58261",
      "label": "с. Новопавловка"
    },
    {
      "value": "d151_51374",
      "label": "с. Новопокровка"
    },
    {
      "value": "d152_31378",
      "label": "ж/м Нуркожо-Ата"
    },
    {
      "value": "d153_02107",
      "label": "с. Озёрное"
    },
    {
      "value": "d154_90879",
      "label": "ж/м Орок"
    },
    {
      "value": "d155_31306",
      "label": "с. Орто-Сай"
    },
    {
      "value": "d156_89029",
      "label": "Орто-Сайский рынок"
    },
    {
      "value": "d157_82639",
      "label": "ж/м Оскон-Ордо"
    },
    {
      "value": "d158_14643",
      "label": "Ошский рынок"
    },
    {
      "value": "d159_15357",
      "label": "Ошский рынок (новый)"
    },
    {
      "value": "d160_07758",
      "label": "Панорама"
    },
    {
      "value": "d161_82412",
      "label": "Парк Адинай"
    },
    {
      "value": "d162_41980",
      "label": "Парк Ататюрк"
    },
    {
      "value": "d163_68543",
      "label": "Парк Молодёжи"
    },
    {
      "value": "d164_53744",
      "label": "Парк Панфилова"
    },
    {
      "value": "d165_57984",
      "label": "Парк Победы"
    },
    {
      "value": "d166_84778",
      "label": "Парк Фучика"
    },
    {
      "value": "d167_28691",
      "label": "Парк Ынтымак"
    },
    {
      "value": "d168_61471",
      "label": "Пишпек"
    },
    {
      "value": "d169_24400",
      "label": "Площадь Ала-Тоо"
    },
    {
      "value": "d170_05453",
      "label": "Площадь Победы"
    },
    {
      "value": "d171_98944",
      "label": "Политех"
    },
    {
      "value": "d172_93262",
      "label": "ж/м Полицейский городок"
    },
    {
      "value": "d173_52173",
      "label": "с. Пригородное"
    },
    {
      "value": "d174_61955",
      "label": "Рабочий городок"
    },
    {
      "value": "d175_37699",
      "label": "ж/м Рухий Мурас"
    },
    {
      "value": "d176_20458",
      "label": "Рынок Баят / Азиз"
    },
    {
      "value": "d177_53550",
      "label": "Рынок Кызыл Ордо"
    },
    {
      "value": "d178_65742",
      "label": "с. Садовое"
    },
    {
      "value": "d179_95035",
      "label": "ж/м Салам-Алик"
    },
    {
      "value": "d180_34174",
      "label": "с. Сарбан"
    },
    {
      "value": "d181_50917",
      "label": "Сары-Озон Дыйкан рынок"
    },
    {
      "value": "d182_47861",
      "label": "ж/м Сары-Челек"
    },
    {
      "value": "d183_27416",
      "label": "Селекционное"
    },
    {
      "value": "d184_76502",
      "label": "Сквер Тоголок Молдо"
    },
    {
      "value": "d185_36156",
      "label": "Мкр. Совмина"
    },
    {
      "value": "d186_88627",
      "label": "Совхоз «Ала-Тоо»"
    },
    {
      "value": "d187_76125",
      "label": "Мкр. Солнечный"
    },
    {
      "value": "d188_35870",
      "label": "Средний Джал"
    },
    {
      "value": "d189_56908",
      "label": "Старая площадь"
    },
    {
      "value": "d190_09055",
      "label": "Старый аэропорт"
    },
    {
      "value": "d191_15213",
      "label": "Старый толчок рынок"
    },
    {
      "value": "d192_29812",
      "label": "с. Степное"
    },
    {
      "value": "d193_52283",
      "label": "ТЦ Таатан"
    },
    {
      "value": "d194_21821",
      "label": "ж/м Таш-Добо"
    },
    {
      "value": "d195_94400",
      "label": "ТРЦ Таш-Рабат"
    },
    {
      "value": "d196_46752",
      "label": "ж/м Тендик"
    },
    {
      "value": "d197_52248",
      "label": "Технопарк"
    },
    {
      "value": "d198_28996",
      "label": "Токольдош"
    },
    {
      "value": "d199_03486",
      "label": "ТРЦ I-Mall"
    },
    {
      "value": "d200_10003",
      "label": "Мкр. Тунгуч"
    },
    {
      "value": "d201_50939",
      "label": "Турбаза"
    },
    {
      "value": "d202_26801",
      "label": "ТЦ Весна"
    },
    {
      "value": "d203_87350",
      "label": "ТЭЦ"
    },
    {
      "value": "d204_85449",
      "label": "Мкр. Улан"
    },
    {
      "value": "d205_57805",
      "label": "Мкр. Улан-2"
    },
    {
      "value": "d206_84359",
      "label": "ж/м Умут"
    },
    {
      "value": "d207_70115",
      "label": "Мкр. Учкун"
    },
    {
      "value": "d208_02130",
      "label": "с. Учкун"
    },
    {
      "value": "d209_83157",
      "label": "Физкультурный (КГАФКиС)"
    },
    {
      "value": "d210_56936",
      "label": "Физприборы"
    },
    {
      "value": "d211_66648",
      "label": "Филармония"
    },
    {
      "value": "d212_56631",
      "label": "Центральная мечеть"
    },
    {
      "value": "d213_83651",
      "label": "Церковь"
    },
    {
      "value": "d214_81764",
      "label": "ЦУМ"
    },
    {
      "value": "d215_55224",
      "label": "Чекиш-Ата рынок"
    },
    {
      "value": "d216_65225",
      "label": "с. Чон-Арык"
    },
    {
      "value": "d217_48847",
      "label": "Шлагбаум"
    },
    {
      "value": "d218_83991",
      "label": "Шоро завод"
    },
    {
      "value": "d219_85964",
      "label": "ж/м Ынтымак"
    },
    {
      "value": "d220_82447",
      "label": "ж/м Энесай"
    },
    {
      "value": "d221_01802",
      "label": "Юбилейка"
    },
    {
      "value": "d222_73203",
      "label": "Мкр. Юг-2"
    },
    {
      "value": "d223_55678",
      "label": "Южные ворота"
    }
  ],
  "Ош": [
    {
      "value": "d001_30619",
      "label": "Центр"
    },
    {
      "value": "d002_51544",
      "label": "мкр. Черёмушки"
    },
    {
      "value": "d003_30283",
      "label": "мкр. Анар"
    },
    {
      "value": "d004_95337",
      "label": "мкр. Юго-Восток"
    },
    {
      "value": "d005_23318",
      "label": "Амир-Темур"
    },
    {
      "value": "d006_78582",
      "label": "Ак-Тилек"
    },
    {
      "value": "d007_39876",
      "label": "Сулайман-Тоо"
    },
    {
      "value": "d008_60658",
      "label": "Центральный рынок"
    },
    {
      "value": "d009_33774",
      "label": "Аэропорт"
    },
    {
      "value": "d010_83604",
      "label": "Автовокзал"
    }
  ],
  "Манас": [
    {
      "value": "manas_d001_bf03c",
      "label": "Центр"
    },
    {
      "value": "manas_d002_71661",
      "label": "мкр. Спутник"
    },
    {
      "value": "manas_d003_afa3f",
      "label": "мкр. Кок-Арт"
    },
    {
      "value": "manas_d004_755eb",
      "label": "мкр. Курманбек"
    },
    {
      "value": "manas_d005_f2de4",
      "label": "мкр. Достук"
    },
    {
      "value": "manas_d006_75a94",
      "label": "Центральный рынок"
    },
    {
      "value": "manas_d007_c3498",
      "label": "Автовокзал"
    },
    {
      "value": "manas_d008_45715",
      "label": "Курорт Джалал-Абад"
    }
  ],
  "Каракол": [
    {
      "value": "karakol_d001_4a3c4",
      "label": "Центр"
    },
    {
      "value": "karakol_d002_e21cf",
      "label": "Центральный рынок"
    },
    {
      "value": "karakol_d003_cdb4e",
      "label": "Автовокзал"
    },
    {
      "value": "karakol_d004_f7896",
      "label": "Аэропорт"
    },
    {
      "value": "karakol_d005_87839",
      "label": "Пристань-Пржевальск"
    }
  ],
  "Нарын": [
    {
      "value": "naryn_d001_b0d68",
      "label": "Центр"
    },
    {
      "value": "naryn_d002_300a5",
      "label": "Центральный рынок"
    },
    {
      "value": "naryn_d003_8ed9d",
      "label": "Автовокзал"
    },
    {
      "value": "naryn_d004_aab07",
      "label": "мкр. Ала-Тоо"
    },
    {
      "value": "naryn_d005_0e4b2",
      "label": "мкр. Москва"
    }
  ],
  "Талас": [
    {
      "value": "talas_d001_976ca",
      "label": "Центр"
    },
    {
      "value": "talas_d002_46155",
      "label": "Центральный рынок"
    },
    {
      "value": "talas_d003_55900",
      "label": "Автовокзал"
    },
    {
      "value": "talas_d004_8d5f5",
      "label": "Аэропорт"
    }
  ],
  "Баткен": [
    {
      "value": "batken_d001_6971b",
      "label": "Центр"
    },
    {
      "value": "batken_d002_ae690",
      "label": "Центральный рынок"
    },
    {
      "value": "batken_d003_bf7f7",
      "label": "Автовокзал"
    },
    {
      "value": "batken_d004_541a5",
      "label": "Аэропорт"
    }
  ],
  "Токмок": [
    {
      "value": "tokmok_d001_b3758",
      "label": "Центр"
    },
    {
      "value": "tokmok_d002_24df0",
      "label": "Центральный рынок"
    },
    {
      "value": "tokmok_d003_5661a",
      "label": "Автовокзал"
    },
    {
      "value": "tokmok_d004_cf3d5",
      "label": "с. Чуй"
    },
    {
      "value": "tokmok_d005_da97f",
      "label": "с. Шамшы"
    },
    {
      "value": "tokmok_d006_7ee3a",
      "label": "с. Кошой"
    },
    {
      "value": "tokmok_d007_f6a01",
      "label": "с. Кегети"
    }
  ],
  "Кант": [
    {
      "value": "kant_d001_62878",
      "label": "Центр"
    },
    {
      "value": "kant_d002_32a53",
      "label": "Центральный рынок"
    },
    {
      "value": "kant_d003_6e033",
      "label": "с. Люксембург"
    },
    {
      "value": "kant_d004_31fbf",
      "label": "с. Интернациональное"
    },
    {
      "value": "kant_d005_fbc59",
      "label": "с. Ивановка"
    }
  ],
  "Кара-Балта": [
    {
      "value": "kara_balta_d001_f5be1",
      "label": "Центр"
    },
    {
      "value": "kara_balta_d002_463ed",
      "label": "Центральный рынок"
    },
    {
      "value": "kara_balta_d003_4ec97",
      "label": "Автовокзал"
    },
    {
      "value": "kara_balta_d004_3ebcf",
      "label": "с. Сосновка"
    },
    {
      "value": "kara_balta_d005_1b4f5",
      "label": "с. Полтавка"
    },
    {
      "value": "kara_balta_d006_6c3f6",
      "label": "с. Новониколаевка"
    }
  ],
  "Кемин": [
    {
      "value": "kemin_d001_9c198",
      "label": "Центр"
    },
    {
      "value": "kemin_d002_fb6e0",
      "label": "с. Чон-Кемин"
    },
    {
      "value": "kemin_d003_b476a",
      "label": "с. Шабдан"
    },
    {
      "value": "kemin_d004_a1996",
      "label": "с. Кызыл-Октябрь"
    }
  ],
  "Орловка": [
    {
      "value": "orlovka_d001_32728",
      "label": "Центр"
    },
    {
      "value": "orlovka_d002_dfbea",
      "label": "с. Быстровка"
    },
    {
      "value": "orlovka_d003_02a97",
      "label": "с. Борду"
    },
    {
      "value": "orlovka_d004_1df33",
      "label": "с. Ильичевское"
    }
  ],
  "Кайынды": [
    {
      "value": "kayyngdy_d001_53452",
      "label": "Центр"
    },
    {
      "value": "kayyngdy_d002_78227",
      "label": "с. Панфиловское"
    },
    {
      "value": "kayyngdy_d003_8f5c5",
      "label": "с. Вознесеновка"
    },
    {
      "value": "kayyngdy_d004_56d77",
      "label": "с. Чалдыбар"
    }
  ],
  "Сокулук": [
    {
      "value": "sokuluk_d001_fda76",
      "label": "Центр"
    },
    {
      "value": "sokuluk_d002_357b9",
      "label": "Центральный рынок"
    },
    {
      "value": "sokuluk_d003_e38f5",
      "label": "с. Военно-Антоновка"
    }
  ],
  "Шопоков": [
    {
      "value": "shopokov_d001_fae4e",
      "label": "Центр"
    }
  ],
  "Беловодское": [
    {
      "value": "belovodskoe_d001_8fbc1",
      "label": "Центр"
    },
    {
      "value": "belovodskoe_d002_1767f",
      "label": "Центральный рынок"
    },
    {
      "value": "belovodskoe_d003_279c4",
      "label": "с. Александровка"
    },
    {
      "value": "belovodskoe_d004_b4dee",
      "label": "с. Петровка"
    }
  ],
  "Айдаркен": [
    {
      "value": "aidarken_d001_0de9e",
      "label": "Центральный рынок"
    },
    {
      "value": "aidarken_d002_bd825",
      "label": "район ДК"
    },
    {
      "value": "aidarken_d003_36a79",
      "label": "64й мкр"
    },
    {
      "value": "aidarken_d004_8d25f",
      "label": "Дружба"
    },
    {
      "value": "aidarken_d005_2d8f8",
      "label": "Шах-Шах"
    },
    {
      "value": "aidarken_d006_5c283",
      "label": "Кичи Айдаркен"
    },
    {
      "value": "aidarken_d007_611e2",
      "label": "с. Джал"
    },
    {
      "value": "aidarken_d008_cb117",
      "label": "с. Жаны Коргон"
    },
    {
      "value": "aidarken_d009_7a53c",
      "label": "с. Эшме"
    },
    {
      "value": "aidarken_d010_e25f9",
      "label": "с. Сур"
    },
    {
      "value": "aidarken_d011_7b5cd",
      "label": "с. Чечме"
    },
    {
      "value": "aidarken_d012_22b3b",
      "label": "с. Сырт"
    },
    {
      "value": "aidarken_d013_b128c",
      "label": "с. Сай"
    }
  ]
}


def _deal_options(property_key: str) -> dict[str, Any]:
    labels = DEAL_LABELS[property_key]
    items = [{"value": k, "label": lab} for k, lab in labels.items()]
    return _items_choices(items)


def _district_options() -> dict[str, Any]:
    return {
        "scoped_by": "city",
        "by_city": DISTRICT_BY_CITY,
        "choices": [],  # resolved at runtime / client by city
        "values": [],
    }


def _seller_options() -> dict[str, Any]:
    # Flatten unique seller roles; deal-specific first role via depends metadata.
    items = [
        {"value": "owner", "label": "Собственник", "for_deals": ["sell", "rent", "rent_bed"]},
        {"value": "buyer", "label": "Покупатель", "for_deals": ["buy"]},
        {"value": "renter", "label": "Арендатор", "for_deals": ["want_rent", "want_rent_bed"]},
        {"value": "realtor", "label": "Риелтор", "for_deals": ["sell", "rent", "buy", "want_rent", "rent_bed", "want_rent_bed"]},
        {"value": "agency", "label": "Агентство недвижимости", "for_deals": ["sell", "rent", "buy", "want_rent", "rent_bed", "want_rent_bed"]},
    ]
    return _items_choices(items)


def _field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None = None,
    hint: str | None = None,
) -> tuple[str, str, CategoryFieldType, bool, int, dict[str, Any] | None, str | None]:
    return (key, label, ftype, required, sort, options, hint)


def _closing_fields(start: int = 900) -> list:
    # Contact Methods: same shared Transport enum vocabulary/UX (not multi-select chips).
    return [
        _field("district", "Район", CategoryFieldType.enum, True, start, _district_options()),
        _field("seller_type", "Кто предлагает", CategoryFieldType.enum, True, start + 10, _seller_options()),
        _field("price", "Цена", CategoryFieldType.price, True, start + 20),
        _field(
            "negotiable",
            "Возможность торга",
            CategoryFieldType.enum,
            True,
            start + 30,
            _pair_choices(("yes", "Возможен торг"), ("no", "Цена окончательная")),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            start + 40,
            _pair_choices(*[(v, v) for v in CONTACT_METHOD_CHOICES]),
        ),
    ]


def _subtype_rent_term(sort: int = 20) -> tuple:
    opts = _pair_choices(
        ("long_term", "Долгосрочная аренда"),
        ("daily", "Посуточная аренда"),
    )
    opts["depends_on"] = {
        "field": "deal_type",
        "values": ["rent", "want_rent", "rent_bed", "want_rent_bed"],
    }
    return _field("subtype", "Тип аренды", CategoryFieldType.enum, True, sort, opts)


def _subtype_label_by_deal() -> dict[str, str]:
    return {
        "sell": "Тип",
        "buy": "Тип",
        "rent": "Тип аренды",
        "want_rent": "Тип аренды",
        "rent_bed": "Тип аренды",
        "want_rent_bed": "Тип аренды",
    }


def _subtype_apartment(sort: int = 20) -> tuple:
    items = [
        {"value": "secondary", "label": "Вторичный рынок", "for_deals": ["sell", "buy"]},
        {"value": "new_build", "label": "Новостройки", "for_deals": ["sell", "buy"]},
        {"value": "long_term", "label": "Долгосрочная аренда", "for_deals": ["rent", "want_rent"]},
        {"value": "daily", "label": "Посуточная аренда", "for_deals": ["rent", "want_rent"]},
    ]
    opts = _items_choices(items)
    opts["depends_on"] = {
        "field": "deal_type",
        "values": ["sell", "buy", "rent", "want_rent"],
    }
    opts["label_by_deal"] = _subtype_label_by_deal()
    return _field("subtype", "Тип", CategoryFieldType.enum, True, sort, opts)


def _subtype_house(sort: int = 20) -> tuple:
    items = [
        {"value": "private_house", "label": "Частные дома", "for_deals": ["sell", "buy"]},
        {"value": "cottage", "label": "Коттеджи", "for_deals": ["sell", "buy"]},
        {"value": "long_term", "label": "Долгосрочная аренда", "for_deals": ["rent", "want_rent"]},
        {"value": "daily", "label": "Посуточная аренда", "for_deals": ["rent", "want_rent"]},
    ]
    opts = _items_choices(items)
    opts["depends_on"] = {
        "field": "deal_type",
        "values": ["sell", "buy", "rent", "want_rent"],
    }
    opts["label_by_deal"] = _subtype_label_by_deal()
    return _field("subtype", "Тип", CategoryFieldType.enum, True, sort, opts)


def _subtype_room(sort: int = 20) -> tuple:
    items = [
        {
            "value": "long_term",
            "label": "Долгосрочная аренда",
            "for_deals": ["rent", "want_rent", "rent_bed", "want_rent_bed"],
        },
        {
            "value": "daily",
            "label": "Посуточная аренда",
            "for_deals": ["rent", "want_rent", "rent_bed", "want_rent_bed"],
        },
    ]
    opts = _items_choices(items)
    opts["depends_on"] = {
        "field": "deal_type",
        "values": ["rent", "want_rent", "rent_bed", "want_rent_bed"],
    }
    return _field("subtype", "Тип аренды", CategoryFieldType.enum, True, sort, opts)


def _subtype_land(sort: int = 20) -> tuple:
    return _field(
        "subtype",
        "Назначение участка",
        CategoryFieldType.enum,
        True,
        sort,
        _pair_choices(
            ("house_build", "Под строительство дома"),
            ("agriculture", "Сельхозназначение"),
            ("commercial", "Коммерческое"),
            ("industrial", "Промышленное"),
            ("other", "Другое"),
        ),
    )



def _plot_area_field(*, sort: int, required: bool = True) -> tuple:
    """Exact plot size in сотках. Unit is metadata; value is Decimal."""
    return _field(
        "plot_area",
        "Площадь участка",
        CategoryFieldType.decimal,
        required,
        sort,
        {
            "unit": "соток",
            "unit_label": "соток",
            "min": 0.01,
            "allow_decimal": True,
        },
        "Площадь участка в сотках",
    )


def _area_field(
    label: str,
    *,
    sort: int,
    required: bool = True,
    options: dict | None = None,
) -> tuple:
    """Canonical numeric area (m²). Value is Decimal; unit is metadata only."""
    opts = {
        "unit": "m2",
        "unit_label": "м²",
        "min": 0.1,
        "allow_decimal": True,
    }
    if options:
        opts.update(options)
    return _field(
        "area",
        label,
        CategoryFieldType.decimal,
        required,
        sort,
        opts,
        "Площадь в квадратных метрах",
    )


def _living_attrs(start: int = 100, *, with_series_floor: bool = True) -> list:
    fields = [
        _field(
            "rooms",
            "Комнаты",
            CategoryFieldType.enum,
            True,
            start,
            _pair_choices(
                ("studio", "Студия"),
                ("1", "1 комната"),
                ("2", "2 комнаты"),
                ("3", "3 комнаты"),
                ("4", "4 комнаты"),
                ("5", "5 комнат"),
                ("6_plus", "6 комнат и более"),
            ),
        ),
    ]
    if with_series_floor:
        fields.append(
            _field(
                "series",
                "Серия / Класс",
                CategoryFieldType.enum,
                True,
                start + 10,
                _pair_choices(
                    ("new_economy", "Эконом"),
                    ("new_comfort", "Комфорт"),
                    ("new_comfort_plus", "Комфорт+"),
                    ("new_business", "Бизнес"),
                    ("new_premium", "Премиум"),
                    ("series_103", "103 серия"),
                    ("series_104", "104 серия"),
                    ("series_105", "105 серия"),
                    ("series_106", "106 серия"),
                    ("series_106_improved", "106 серия (улучшенная)"),
                    ("series_107", "107 серия"),
                    ("series_108", "108 серия"),
                    ("individual", "Индивидуалка"),
                    ("khrushchevka", "Хрущёвка"),
                    ("stalinka", "Сталинка"),
                    ("hotel_type", "Гостиничный тип"),
                    ("small_family", "Малосемейка"),
                    ("dormitory", "Общежитие"),
                ),
            )
        )
        floor_pairs = [
            ("basement", "Подвальный этаж"),
            ("ground", "Цокольный этаж"),
            ("attic", "Мансарда"),
            ("penthouse", "Пентхаус"),
        ] + [(str(i), str(i)) for i in range(1, 31)]
        fields.append(
            _field(
                "floor",
                "Этаж",
                CategoryFieldType.enum,
                True,
                start + 20,
                _pair_choices(*floor_pairs),
            )
        )
    fields.extend(
        [
            _field(
                "renovation",
                "Ремонт",
                CategoryFieldType.enum,
                True,
                start + 30,
                _pair_choices(
                    ("cosmetic", "Косметический ремонт"),
                    ("euro", "Евроремонт"),
                    ("designer", "Дизайнерский ремонт"),
                    ("fresh", "Свежий ремонт"),
                    ("old", "Старый ремонт"),
                    ("needs_repair", "Требуется ремонт"),
                ),
            ),
            _field(
                "utilities",
                "Коммуникации",
                CategoryFieldType.multi_select,
                True,
                start + 40,
                _pair_choices(
                    ("cold_water", "Холодная вода"),
                    ("hot_water", "Горячая вода"),
                    ("sewer", "Канализация"),
                    ("gas", "Газ"),
                    ("electricity", "Электричество"),
                ),
            ),
            _field(
                "furniture",
                "Мебель",
                CategoryFieldType.enum,
                True,
                start + 50,
                _pair_choices(
                    ("full", "Мебель полностью"),
                    ("partial", "Мебель частично"),
                    ("none", "Без мебели"),
                ),
            ),
            _field(
                "appliances",
                "Бытовая техника",
                CategoryFieldType.enum,
                True,
                start + 60,
                _pair_choices(
                    ("full", "Есть всё"),
                    ("partial", "Есть частично"),
                    ("none", "Нет"),
                ),
            ),
        ]
    )
    return fields


def _apartment_fields() -> list:
    living = _living_attrs(100, with_series_floor=True)
    # Insert area after rooms (sort 105) — rooms → area → series/floor.
    rooms = living[0]
    rest = living[1:]
    return [
        _field("deal_type", "Тип сделки", CategoryFieldType.enum, True, 10, _deal_options("apartments")),
        _subtype_apartment(20),
        rooms,
        _area_field("Общая площадь, м²", sort=105, required=True),
        *rest,
        *_closing_fields(900),
    ]


def _house_fields() -> list:
    return [
        _field("deal_type", "Тип сделки", CategoryFieldType.enum, True, 10, _deal_options("houses")),
        _subtype_house(20),
        _field(
            "rooms",
            "Комнаты",
            CategoryFieldType.enum,
            True,
            100,
            _pair_choices(
                ("studio", "Студия"),
                ("1", "1 комната"),
                ("2", "2 комнаты"),
                ("3", "3 комнаты"),
                ("4", "4 комнаты"),
                ("5", "5 комнат"),
                ("6_plus", "6 комнат и более"),
            ),
        ),
        _area_field("Площадь дома, м²", sort=105, required=True),
        _plot_area_field(sort=110),
        _field(
            "renovation",
            "Ремонт",
            CategoryFieldType.enum,
            True,
            120,
            _pair_choices(
                ("cosmetic", "Косметический ремонт"),
                ("euro", "Евроремонт"),
                ("designer", "Дизайнерский ремонт"),
                ("fresh", "Свежий ремонт"),
                ("old", "Старый ремонт"),
                ("needs_repair", "Требуется ремонт"),
            ),
        ),
        _field(
            "utilities",
            "Коммуникации",
            CategoryFieldType.multi_select,
            True,
            130,
            _pair_choices(
                ("cold_water", "Холодная вода"),
                ("hot_water", "Горячая вода"),
                ("sewer", "Канализация"),
                ("gas", "Газ"),
                ("electricity", "Электричество"),
            ),
        ),
        _field(
            "furniture",
            "Мебель",
            CategoryFieldType.enum,
            True,
            140,
            _pair_choices(
                ("full", "Мебель полностью"),
                ("partial", "Мебель частично"),
                ("none", "Без мебели"),
            ),
        ),
        _field(
            "appliances",
            "Бытовая техника",
            CategoryFieldType.enum,
            True,
            150,
            _pair_choices(
                ("full", "Есть всё"),
                ("partial", "Есть частично"),
                ("none", "Нет"),
            ),
        ),
        *_closing_fields(900),
    ]


def _room_fields() -> list:
    # Rooms: rent/bed deals only; series+floor like apartments (no rooms count).
    # Area is OPTIONAL — bed-place (койко-место) must not require m².
    living_no_rooms = [f for f in _living_attrs(100, with_series_floor=True) if f[0] != "rooms"]
    area = _area_field(
        "Площадь комнаты, м²",
        sort=95,
        required=False,
        options={
            "depends_on": {
                "field": "deal_type",
                "values": ["rent", "want_rent"],
            },
        },
    )
    return [
        _field("deal_type", "Тип сделки", CategoryFieldType.enum, True, 10, _deal_options("rooms")),
        _subtype_room(20),
        area,
        *living_no_rooms,
        *_closing_fields(900),
    ]


def _land_fields() -> list:
    return [
        _field("deal_type", "Тип сделки", CategoryFieldType.enum, True, 10, _deal_options("land")),
        _subtype_land(20),
        _plot_area_field(sort=100),
        _field(
            "documents",
            "Документы",
            CategoryFieldType.enum,
            True,
            110,
            _pair_choices(
                ("red_book", "Красная книга"),
                ("sale_contract", "Договор купли-продажи"),
                ("gift_contract", "Договор дарения"),
                ("tech_passport", "Тех паспорт"),
                ("green_book", "Зеленая книга"),
                ("shared_construction", "Договор долевого участия"),
                ("power_of_attorney", "Генеральная доверенность"),
            ),
        ),
        _field(
            "utilities",
            "Коммуникации",
            CategoryFieldType.multi_select,
            True,
            120,
            _pair_choices(
                ("water_pipe", "Водопровод"),
                ("sewer", "Канализация"),
                ("gas", "Газ"),
                ("electricity", "Электричество"),
            ),
        ),
        *_closing_fields(900),
    ]


# Dependent commercial characteristics. One field, many directions.
# base_territory is an open site: no floor, entrance, condition, or ceiling.
_COMMERCIAL_FLOOR_DIRECTIONS = [
    "mall_boutique",
    "market_place",
    "residential_commercial",
    "street_retail",
    "office_coworking",
    "beauty_salon_space",
    "medical_center_space",
    "education_space",
    "horeca",
    "entertainment",
    "sports_leisure",
    "building_parts",
    "free_purpose",
    "other_commercial",
]
_COMMERCIAL_ENTRANCE_DIRECTIONS = [
    "mall_boutique",
    "market_place",
    "residential_commercial",
    "street_retail",
    "office_coworking",
    "beauty_salon_space",
    "medical_center_space",
    "education_space",
    "horeca",
    "hospitality",
    "building_parts",
    "free_purpose",
]
_COMMERCIAL_CONDITION_DIRECTIONS = [
    "mall_boutique",
    "market_place",
    "residential_commercial",
    "street_retail",
    "office_coworking",
    "beauty_salon_space",
    "medical_center_space",
    "education_space",
    "auto_business_space",
    "production_facility",
    "warehouse_logistics",
    "horeca",
    "entertainment",
    "sports_leisure",
    "hospitality",
    "building_parts",
    "free_purpose",
    "other_commercial",
]
_COMMERCIAL_CEILING_DIRECTIONS = [
    "warehouse_logistics",
    "production_facility",
    "auto_business_space",
    "sports_leisure",
]
_COMMERCIAL_TRUCK_DIRECTIONS = [
    "warehouse_logistics",
    "production_facility",
    "auto_business_space",
    "base_territory",
]


def _commercial_direction_options(pairs: tuple[tuple[str, str], ...], directions: list[str]) -> dict[str, Any]:
    opts = _pair_choices(*pairs)
    opts["depends_on"] = {"field": "commercial_direction", "values": list(directions)}
    return opts


def _commercial_fields() -> list:
    return [
        _field("deal_type", "Тип сделки", CategoryFieldType.enum, True, 10, _deal_options("commercial")),
        _field(
            "commercial_direction",
            "Направление",
            CategoryFieldType.enum,
            True,
            20,
            _items_choices(COMMERCIAL_DIRECTION_ITEMS),
        ),
        _area_field("Площадь помещения, м²", sort=30, required=True),
        _field(
            "floor_position",
            "Расположение",
            CategoryFieldType.enum,
            False,
            40,
            _commercial_direction_options(
                (
                    ("basement", "Подвал"),
                    ("ground", "Цоколь"),
                    ("first", "1 этаж"),
                    ("upper", "2 этаж и выше"),
                    ("whole_building", "Отдельное здание"),
                ),
                _COMMERCIAL_FLOOR_DIRECTIONS,
            ),
        ),
        _field(
            "entrance_type",
            "Вход",
            CategoryFieldType.enum,
            False,
            50,
            _commercial_direction_options(
                (
                    ("separate_street", "Отдельный вход с улицы"),
                    ("shared", "Общий вход"),
                    ("yard", "Вход со двора"),
                ),
                _COMMERCIAL_ENTRANCE_DIRECTIONS,
            ),
        ),
        _field(
            "property_condition",
            "Состояние помещения",
            CategoryFieldType.enum,
            False,
            60,
            _commercial_direction_options(
                (
                    ("ready", "Готово к использованию"),
                    ("needs_repair", "Требует ремонта"),
                    ("under_renovation", "В процессе ремонта"),
                    ("shell", "Без отделки"),
                ),
                _COMMERCIAL_CONDITION_DIRECTIONS,
            ),
        ),
        _field(
            "ceiling_height",
            "Высота потолков",
            CategoryFieldType.decimal,
            False,
            70,
            {
                "unit": "m",
                "unit_label": "м",
                "min": 0.1,
                "allow_decimal": True,
                "depends_on": {
                    "field": "commercial_direction",
                    "values": list(_COMMERCIAL_CEILING_DIRECTIONS),
                },
            },
            "Высота потолков в метрах",
        ),
        _field(
            "truck_access",
            "Подъезд транспорта",
            CategoryFieldType.enum,
            False,
            80,
            _commercial_direction_options(
                (
                    ("none", "Нет грузового подъезда"),
                    ("light", "Легковой или небольшая Газель"),
                    ("truck", "Грузовой транспорт"),
                    ("ramp", "Есть рампа"),
                ),
                _COMMERCIAL_TRUCK_DIRECTIONS,
            ),
        ),
        _field(
            "utilities",
            "Коммуникации",
            CategoryFieldType.multi_select,
            True,
            100,
            _pair_choices(
                ("cold_water", "Холодная вода"),
                ("hot_water", "Горячая вода"),
                ("sewer", "Канализация"),
                ("gas", "Газ"),
                ("electricity", "Электричество"),
                ("power_3phase", "Электроснабжения 3-ф"),
                ("ac", "Кондиционирования"),
                ("ventilation", "Вентиляция, вытяжка"),
                ("heating", "Отопление"),
            ),
        ),
        *_closing_fields(900),
    ]


def _garage_subtype(sort: int = 20) -> tuple:
    items = [
        {"value": "box", "label": "Отдельный бокс", "for_deals": ["sell", "buy"]},
        {"value": "space", "label": "Машиноместо", "for_deals": ["sell", "buy"]},
        {"value": "long_term", "label": "На долгий срок", "for_deals": ["rent", "want_rent"]},
        {"value": "daily", "label": "Посуточно", "for_deals": ["rent", "want_rent"]},
    ]
    opts = _items_choices(items)
    opts["depends_on"] = {"field": "deal_type", "values": ["sell", "buy", "rent", "want_rent"]}
    opts["label_by_deal"] = _subtype_label_by_deal()
    return _field("subtype", "Тип", CategoryFieldType.enum, True, sort, opts)


def _parking_subtype(sort: int = 20) -> tuple:
    return _garage_subtype(sort)


def _garage_fields() -> list:
    return [
        _field("deal_type", "Тип сделки", CategoryFieldType.enum, True, 10, _deal_options("garages")),
        _garage_subtype(20),
        _area_field("Площадь, м²", sort=30, required=False),
        _field(
            "utilities",
            "Коммуникации",
            CategoryFieldType.multi_select,
            True,
            100,
            _pair_choices(
                ("electricity", "Электричество"),
                ("cold_water", "Холодная вода"),
                ("sewer", "Канализация"),
            ),
        ),
        *_closing_fields(900),
    ]


def _parking_fields() -> list:
    return [
        _field("deal_type", "Тип сделки", CategoryFieldType.enum, True, 10, _deal_options("parking")),
        _parking_subtype(20),
        *_closing_fields(900),
    ]


RE_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    APARTMENTS_SLUG: _apartment_fields(),
    HOUSES_SLUG: _house_fields(),
    ROOMS_SLUG: _room_fields(),
    LAND_SLUG: _land_fields(),
    COMMERCIAL_SLUG: _commercial_fields(),
    GARAGES_SLUG: _garage_fields(),
    PARKING_SLUG: _parking_fields(),
}


def _filters_from_core(fields: list) -> list:
    """Search filter foundation: same keys/options as Create (no fake counts)."""
    out = []
    sort = 0
    for key, label, ftype, _req, _s, options, _hint in fields:
        # Ceiling is Create-only in this version. Area/plot stay range filters.
        if key == "ceiling_height":
            continue
        if key in {"price", "contact_methods"}:
            if key == "price":
                out.append((key, label, CategoryFilterType.range, sort, None))
                sort += 10
            continue
        if key == "area" or key == "plot_area" or ftype in {
            CategoryFieldType.decimal,
            CategoryFieldType.number,
        }:
            if key == "area":
                out.append(
                    (
                        key,
                        "Площадь, м²",
                        CategoryFilterType.range,
                        sort,
                        {"unit": "m2", "unit_label": "м²"},
                    )
                )
                sort += 10
            elif key == "plot_area":
                out.append(
                    (
                        key,
                        "Площадь участка",
                        CategoryFilterType.range,
                        sort,
                        {"unit": "соток", "unit_label": "соток"},
                    )
                )
                sort += 10
            continue
        if ftype in {
            CategoryFieldType.enum,
            CategoryFieldType.multi_select,
            CategoryFieldType.city,
        }:
            out.append((key, label, CategoryFilterType.select, sort, options))
            sort += 10
    return out


RE_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    slug: _filters_from_core(fields) for slug, fields in RE_CORE_FIELDS_BY_SLUG.items()
}


# Aliases → canonical property leaves (not legacy deal homes).
RE_ALIASES: list[tuple[str, str, int]] = [
    ("квартира", APARTMENTS_SLUG, 100),
    ("продам квартиру", APARTMENTS_SLUG, 110),
    ("куплю квартиру", APARTMENTS_SLUG, 110),
    ("сдам квартиру", APARTMENTS_SLUG, 110),
    ("сниму квартиру", APARTMENTS_SLUG, 110),
    ("дом", HOUSES_SLUG, 100),
    ("коттедж", HOUSES_SLUG, 100),
    ("участок", LAND_SLUG, 100),
    ("комната", ROOMS_SLUG, 100),
    ("койко-место", ROOMS_SLUG, 100),
    ("офис", COMMERCIAL_SLUG, 100),
    ("склад", COMMERCIAL_SLUG, 100),
    ("коммерческая", COMMERCIAL_SLUG, 100),
    ("сдам бутик", COMMERCIAL_SLUG, 110),
    ("гараж", GARAGES_SLUG, 100),
    ("парковка", PARKING_SLUG, 100),
    ("машиноместо", PARKING_SLUG, 100),
    ("недвижимость", APARTMENTS_SLUG, 50),
    ("аренда", APARTMENTS_SLUG, 40),
]
