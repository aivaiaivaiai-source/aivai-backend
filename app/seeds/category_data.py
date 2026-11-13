from __future__ import annotations

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
    CategoryRuleType,
    ModerationAction,
)

# (slug, name, entity_type, sort_order)
ROOT_CATEGORIES: list[tuple[str, str, CategoryEntityType, int]] = [
    ("real-estate", "Недвижимость", CategoryEntityType.object, 10),
    ("transport", "Транспорт", CategoryEntityType.object, 20),
    ("jobs", "Работа", CategoryEntityType.job, 30),
    ("services", "Услуги", CategoryEntityType.service, 40),
    ("repair-construction", "Ремонт и строительство", CategoryEntityType.construction, 50),
    ("electronics", "Техника и электроника", CategoryEntityType.object, 60),
    ("business-equipment", "Бизнес-оборудование", CategoryEntityType.equipment, 70),
    ("home-garden", "Дом и сад", CategoryEntityType.object, 80),
    ("kids", "Детские товары", CategoryEntityType.object, 90),
    ("medical", "Медтовары", CategoryEntityType.object, 100),
    ("food-agri", "Продукты, сельхозтовары и фермерская продукция", CategoryEntityType.food, 110),
    ("beauty", "Красота и личный уход", CategoryEntityType.object, 120),
    ("fashion", "Одежда, обувь и аксессуары", CategoryEntityType.object, 130),
    ("sports-hobby", "Спорт, отдых и хобби", CategoryEntityType.object, 140),
    ("stationery-books", "Канцтовары, книги и учебные товары", CategoryEntityType.object, 150),
    ("animals", "Животные", CategoryEntityType.animal, 160),
    ("materials", "Материалы, сырьё и товары для производства", CategoryEntityType.raw_material, 170),
    ("ready-business", "Готовый бизнес и франшизы", CategoryEntityType.business, 180),
    # free-exchange retired (user/Archi): not an AiVai category — see free_exchange_retirement.py
]

SUBCATEGORIES: dict[str, list[tuple[str, str, CategoryEntityType]]] = {
    # Real Estate V2: property leaves come from mobile_category_skeleton + real_estate_v2.
    # Legacy deal homes (sale/rent/commercial) are retired — do not re-seed as live SoT.
    "real-estate": [],
    # Transport L2 comes from mobile_category_skeleton (v2 canonical slugs).
    # Legacy v1 slugs (transport-cars, …) are retired — see catalog_canonical_map_v1.json.
    "transport": [],
    "jobs": [
        ("jobs-vacancies", "Вакансии", CategoryEntityType.job),
        ("jobs-resume", "Резюме", CategoryEntityType.job),
    ],
    "services": [
        ("services-transport", "Перевозки и доставка", CategoryEntityType.service),
        ("services-repair", "Ремонт техники", CategoryEntityType.service),
        ("services-beauty", "Красота и уход", CategoryEntityType.service),
        ("services-cleaning", "Уборка", CategoryEntityType.service),
        ("services-tutoring", "Обучение", CategoryEntityType.service),
        ("services-legal", "Юридические услуги", CategoryEntityType.service),
        ("services-it", "IT и digital", CategoryEntityType.service),
    ],
    # Repair V2: goods L2 from mobile_category_skeleton + repair_v2 overlay.
    # Legacy service-like L2 (repair-building / construction-work / repair-tools) retired.
    "repair-construction": [],
    # Electronics V2: goods L2 from mobile_category_skeleton + electronics_v2.
    # Legacy coarse L2 (phones/computers/appliances/tv) retired.
    "electronics": [],
    "business-equipment": [
        ("business-equipment-cafe", "Кафе и ресторан", CategoryEntityType.equipment),
        ("business-equipment-retail", "Торговое оборудование", CategoryEntityType.equipment),
        ("business-equipment-industrial", "Промышленное", CategoryEntityType.equipment),
    ],
    # Home-garden L2 comes from mobile_category_skeleton.
    # Legacy coarse L2 (home-furniture / home-decor / home-garden-plants) retired.
    "home-garden": [],
    "kids": [
        ("kids-toys", "Игрушки", CategoryEntityType.object),
        ("kids-clothes", "Одежда для детей", CategoryEntityType.object),
        ("kids-strollers", "Коляски и автокресла", CategoryEntityType.object),
    ],
    # Medical modern L2 comes from mobile_category_skeleton.
    # Legacy medical-devices / medical-care soft-retired by Medical V2 cleanup.
    "medical": [],
    "food-agri": [
        ("food-agri-products", "Продукты питания", CategoryEntityType.food),
        ("food-agri-farm", "Фермерская продукция", CategoryEntityType.food),
        ("food-agri-feed", "Корма", CategoryEntityType.food),
    ],
    # Beauty modern L2 come from mobile_category_skeleton + beauty_v2.
    # Legacy beauty-cosmetics / beauty-hair are soft-retired.
    "beauty": [],
    "fashion": [
        ("fashion-clothing", "Одежда", CategoryEntityType.object),
        ("fashion-shoes", "Обувь", CategoryEntityType.object),
        ("fashion-accessories", "Аксессуары", CategoryEntityType.object),
    ],
    # Sport modern L2 come from mobile_category_skeleton + sport_v2.
    # Legacy sports-equipment / sports-tourism / sports-music are soft-retired.
    "sports-hobby": [],
    "stationery-books": [
        ("books-fiction", "Книги", CategoryEntityType.object),
        ("books-study", "Учебники и канцтовары", CategoryEntityType.object),
    ],
    "animals": [
        ("animals-pets", "Домашние животные", CategoryEntityType.animal),
        ("animals-livestock", "Сельхоз животные", CategoryEntityType.animal),
        ("animals-birds", "Птица", CategoryEntityType.animal),
    ],
    "materials": [
        ("materials-textile", "Ткани и текстиль", CategoryEntityType.raw_material),
        ("materials-metal", "Металл и прокат", CategoryEntityType.raw_material),
        ("materials-chemical", "Химия и сырьё", CategoryEntityType.raw_material),
    ],
    # Ready Business modern L2 come from mobile_category_skeleton + ready_business_v2.
    # Legacy cafe/retail/online/franchise L2 are soft-retired (not recreated here).
    "ready-business": [],
    # free-exchange subtree soft-retired — not re-seeded as active SoT.
}

# field_key, label, field_type, ai_hint (None = skip dialogue hint)
_CORE = CategoryFieldType

CORE_FIELDS: dict[str, list[tuple[str, str, CategoryFieldType, str | None]]] = {
    # --- transport (canonical mobile v2) ---
    # transport-car-sale Create SoT: app.seeds.car_sale_v2 (loader overlay).
    "transport-car-sale": [],
    "transport-auto-parts": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("part_type", "Тип запчасти", _CORE.string, "Что за запчасть?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, "Новая или б/у?"),
    ],
    "transport-cargo": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("brand", "Марка", _CORE.brand, "Какая марка?"),
        ("year", "Год", _CORE.year, "Год выпуска?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, "Состояние?"),
    ],
    "transport-special-equipment": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("brand", "Марка", _CORE.brand, "Какая марка?"),
        ("year", "Год", _CORE.year, "Год выпуска?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, "Состояние?"),
    ],
    "transport-moto-tech": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("brand", "Марка", _CORE.brand, None),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "transport-watercraft": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Тип", _CORE.string, "Лодка, катер, яхта?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    # --- real estate (legacy deal homes retired; SoT in app.seeds.real_estate_v2) ---
    "real-estate-sale": [],
    "real-estate-rent": [],
    "real-estate-commercial": [],
    # --- jobs ---
    "jobs-vacancies": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("position", "Должность", _CORE.string, "Какая должность?"),
        ("salary", "Зарплата", _CORE.price, "Какая зарплата?"),
    ],
    "jobs-resume": [
        ("city", "Город", _CORE.city, "В каком городе ищете работу?"),
        ("position", "Специальность", _CORE.string, "Кем хотите работать?"),
        ("salary", "Ожидания", _CORE.price, "Желаемая зарплата?"),
    ],
    # --- services ---
    "services-transport": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("service_type", "Услуга", _CORE.string, "Что нужно перевезти?"),
        ("price", "Цена", _CORE.price, "Бюджет?"),
    ],
    "services-repair": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("service_type", "Ремонт", _CORE.string, "Что нужно отремонтировать?"),
        ("price", "Цена", _CORE.price, "Бюджет?"),
    ],
    "services-beauty": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("service_type", "Услуга", _CORE.string, "Какая услуга?"),
        ("price", "Цена", _CORE.price, "Цена?"),
    ],
    "services-cleaning": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("service_type", "Уборка", _CORE.string, "Квартира, офис, после ремонта?"),
        ("price", "Цена", _CORE.price, "Бюджет?"),
    ],
    "services-tutoring": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("subject", "Предмет", _CORE.string, "Чему учите?"),
        ("price", "Цена", _CORE.price, "Стоимость?"),
    ],
    "services-legal": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("service_type", "Услуга", _CORE.string, "Какая юридическая помощь?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "services-it": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("service_type", "Услуга", _CORE.string, "Сайт, приложение, реклама?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- repair & construction ---
    "repair-building": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("work_type", "Работы", _CORE.string, "Ремонт квартиры, офиса?"),
        ("price", "Цена", _CORE.price, "Бюджет?"),
    ],
    "construction-work": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("work_type", "Строительство", _CORE.string, "Дом, забор, фундамент?"),
        ("price", "Цена", _CORE.price, "Бюджет?"),
    ],
    "repair-tools": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Инструмент", _CORE.string, "Что продаёте?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    # --- electronics ---
    "electronics-phones": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("brand", "Бренд", _CORE.brand, None),
        ("model", "Модель", _CORE.model, None),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "electronics-computers": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Тип", _CORE.string, "Ноутбук, ПК, монитор?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "electronics-appliances": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Техника", _CORE.string, "Холодильник, стиралка?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "electronics-tv": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Тип", _CORE.string, "Телевизор, колонки?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- business equipment ---
    "business-equipment-cafe": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Оборудование", _CORE.string, "Кофемашина, холодильник?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "business-equipment-retail": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Оборудование", _CORE.string, "Что за оборудование?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "business-equipment-industrial": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Оборудование", _CORE.string, "Станок, линия?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- home & garden leaf fields: app.seeds.home_garden_filters (via loader) ---
    # --- kids ---
    "kids-toys": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Игрушка", _CORE.string, "Что за игрушка?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "kids-clothes": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("size", "Размер", _CORE.string, "Какой размер?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "kids-strollers": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Товар", _CORE.string, "Коляска, автокресло?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    # --- medical ---
    "medical-devices": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Прибор", _CORE.string, "Какой прибор?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "medical-care": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Товар", _CORE.string, "Что продаёте?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- food & agri ---
    "food-agri-products": [
        ("city", "Город", _CORE.city, "Город или село?"),
        ("product_type", "Продукт", _CORE.string, "Что продаёте?"),
        ("quantity", "Количество", _CORE.string, "Объём или вес?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
    ],
    "food-agri-farm": [
        ("city", "Город", _CORE.city, "Где находится?"),
        ("product_type", "Продукт", _CORE.string, "Молоко, мясо, курут?"),
        ("quantity", "Количество", _CORE.string, "Сколько?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "food-agri-feed": [
        ("city", "Город", _CORE.city, "Город или село?"),
        ("product_type", "Корм", _CORE.string, "Сено, комбикорм?"),
        ("quantity", "Количество", _CORE.string, None),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- beauty (legacy free-text cores removed; Package A SoT later) ---
    # --- fashion ---
    "fashion-clothing": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Тип", _CORE.string, "Платье, куртка?"),
        ("size", "Размер", _CORE.string, "Какой размер?"),
        ("condition", "Состояние", _CORE.enum, "Новое или б/у?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
    ],
    "fashion-shoes": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Обувь", _CORE.string, "Кроссовки, сапоги?"),
        ("size", "Размер", _CORE.string, "Размер?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "fashion-accessories": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Аксессуар", _CORE.string, "Сумка, часы?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- sports & hobby (legacy triad free-text cores retired; Package A SoT later) ---
    # --- books ---
    "books-fiction": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Книга", _CORE.string, "Жанр или название?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "books-study": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Товар", _CORE.string, "Учебник, канцтовары?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- animals ---
    "animals-pets": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("animal_type", "Животное", _CORE.string, "Собака, кошка?"),
        ("age", "Возраст", _CORE.string, "Возраст?"),
        ("purpose", "Цель", _CORE.enum, "Продажа или отдам?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "animals-livestock": [
        ("city", "Город", _CORE.city, "Где находится?"),
        ("animal_type", "Животное", _CORE.string, "Корова, овца?"),
        ("age", "Возраст", _CORE.string, None),
        ("purpose", "Назначение", _CORE.string, "Мясо, молоко, разведение?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "animals-birds": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("animal_type", "Птица", _CORE.string, "Куры, утки?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- materials (legacy triad cores retired; Package A SoT not seeded yet) ---
    # --- ready business (legacy free-text cores retired; Package A SoT not seeded yet) ---
    # --- free / exchange / found Create cores removed (root retired) ---
}

OPTIONAL_FIELDS: dict[str, list[tuple[str, str, CategoryFieldType]]] = {
    # Optional EAV for car-sale retired — V2 core schema in car_sale_v2.
    "transport-car-sale": [],
    "real-estate-sale": [],
    "real-estate-rent": [],
    "real-estate-commercial": [],
    "electronics-phones": [
        ("memory", "Память", _CORE.string),
        ("battery_health", "АКБ", _CORE.string),
    ],
    "fashion-clothing": [
        ("brand", "Бренд", _CORE.string),
        ("material", "Состав", _CORE.string),
    ],
    "food-agri-farm": [
        ("organic", "Органика", _CORE.boolean),
        ("delivery", "Доставка", _CORE.boolean),
    ],
    "animals-pets": [
        ("vaccinated", "Прививки", _CORE.boolean),
        ("documents", "Документы", _CORE.boolean),
    ],
}

CATEGORY_ALIASES: dict[str, list[str]] = {
    # transport (canonical mobile v2)
    "transport-car-sale": ["авто", "машина", "легковушка", "car", "автомобиль", "седан"],
    "transport-auto-parts": ["запчасти", "аккумулятор", "бампер"],
    "transport-auto-parts-optika-fary-i-fonari": ["фара", "оптика", "фонарь", "штатная фара"],
    "transport-accessories-tuning-multimedia": ["магнитола", "головное устройство"],
    "transport-accessories-tuning-avtozvuk": ["автозвук", "сабвуфер"],
    "transport-accessories-tuning-svet-i-dopolnitelnoe-osveschenie": [
        "led балка",
        "дополнительный свет",
    ],
    "transport-accessories-tuning-aksessuary-salona": [
        "коврики для машины",
        "автоковрики",
        "чехлы",
    ],
    "transport-accessories-tuning-signalizatsii-i-protivougonnye": ["сигнализация"],
    "transport-accessories-tuning-bagazhniki-i-perevozka": ["фаркоп", "багажник на крышу"],
    "transport-accessories-tuning-tehnicheskiy-tyuning": [
        "прямоток",
        "койловеры",
        "комплект гбо",
    ],
    "transport-accessories-tuning-plenki-i-materialy": [
        "тонировочная пленка",
        "шумоизоляционный материал",
    ],
    "transport-tires-wheels": ["шины", "диски"],
    "transport-cargo": ["грузовик", "камаз", "газель", "фура"],
    # Bus V2: leaf aliases (not parent 1201).
    "transport-commercial-avtobusy": ["автобус"],
    "transport-commercial-mikroavtobusy": ["микроавтобус"],
    "transport-buses-avtodoma": ["автодом"],
    "transport-special-equipment": ["спецтехника"],
    "transport-moto-tech": ["мото", "мотоцикл", "скутер", "байк"],
    "transport-bicycles": ["велосипед", "велик", "велосипеды"],
    # real estate V2 — aliases target canonical property leaves (see real_estate_v2.RE_ALIASES).
    "real-estate-kvartiry": [
        "квартира",
        "продам квартиру",
        "куплю квартиру",
        "сдам квартиру",
        "сниму квартиру",
        "недвижимость",
        "аренда",
    ],
    "real-estate-doma-i-kottedzhi": ["дом", "коттедж"],
    "real-estate-zemelnye-uchastki": ["участок"],
    "real-estate-komnaty": ["комната", "койко-место"],
    "real-estate-kommercheskaya-nedvizhimost": [
        "офис",
        "склад",
        "коммерческая",
        "сдам бутик",
    ],
    "real-estate-garazhi": ["гараж"],
    "real-estate-parkovki": ["парковка", "машиноместо"],
    # jobs
    "jobs-vacancies": ["вакансия", "работа", "ищу сотрудника", "требуется"],
    "jobs-resume": ["резюме", "ищу работу", "трудоустройство"],
    # services V2 — aliases target canonical leaves (legacy 7 retired).
    "services-gruzoperevozki-i-pereezdy": [
        "перевозка",
        "грузоперевозки",
        "привезти",
        "щебень",
        "песок",
        "чернозем",
    ],
    "services-kurerskie-uslugi": ["доставка"],
    "services-remont-tehniki": [
        "ремонт телефона",
        "ремонт айфона",
        "ремонт iphone",
        "ремонт ноутбука",
        "ремонт стиральной",
    ],
    "services-uslugi-krasoty-i-stilya": [
        "маникюр",
        "педикюр",
        "наращивание",
        "стрижка",
        "брови",
        "ресницы",
    ],
    "services-uborka-i-klining": ["уборка", "клининг", "химчистка"],
    "services-obuchenie-i-repetitorstvo": ["репетитор", "обучение", "курсы"],
    "services-yuridicheskie-uslugi": ["юрист", "адвокат", "нотариус"],
    "services-kompyutery-i-it-uslugi": ["разработка сайта"],
    "services-reklama-i-marketing": ["smm", "таргет"],
    "services-uslugi-dizayna-i-proektirovaniya": ["дизайн"],
    "services-rieltorskie-uslugi": ["риелтор", "риэлтор"],
    # repair construction V2 — goods words → goods leaves; work phrases → Services.
    "repair-construction-plitka-i-keramogranit": ["плитка"],
    "repair-construction-krovlya-i-vodostoki": ["кровля"],
    "repair-construction-zabory-vorota-i-ograzhdeniya": ["забор"],
    "repair-construction-elektroinstrumenty": ["перфоратор", "болгарка"],
    "repair-construction-instrumenty": ["стройинструмент"],
    "services-stroitelnye-i-remontnye-uslugi": [
        "ремонт квартиры",
        "строительные работы",
        "отделка",
        "строительство",
        "фундамент",
        "штукатурка",
    ],
    # electronics
    "electronics-phones": ["телефон", "айфон", "iphone", "смартфон", "android"],
    "electronics-computers": ["ноутбук", "компьютер", "пк", "macbook"],
    "electronics-appliances": ["холодильник", "стиральная", "плита", "кондиционер"],
    "electronics-tv": ["телевизор", "тв", "колонки", "саундбар"],
    # business equipment
    "business-equipment-cafe": ["кофемашина", "кофемолка", "барное", "кухонное оборудование"],
    "business-equipment-retail": ["витрина", "касса", "холодильник торговый"],
    "business-equipment-industrial": ["станок", "пресс", "конвейер"],
    # home — broad L2 aliases; leaf-specific remaps in HOME_GARDEN_FINAL_ALIAS_REMAP
    "home-garden-mebel-dlya-doma": [
        "диван",
        "шкаф",
        "кровать",
        "стол",
        "мебель",
        "кухня",
        "барная стойка",
        "основание кровати",
        "садовая мебель",
    ],
    "home-garden-mebel-dlya-doma-matrasy": ["матрас", "ортопедический матрас", "матрасы"],
    "home-garden-mebel-dlya-doma-mebelnye-garnitury-kuhonnye-garnitury": [
        "кухонный гарнитур",
        "кухонные гарнитуры",
    ],
    "home-garden-mebel-dlya-doma-komplekty-mebeli-stol-i-stulya": [
        "стол и стулья",
        "стол со стульями",
    ],
    "home-garden-tekstil-i-kovry": ["ковер", "коврик", "ковры"],
    "home-garden-postelnoe-bele-i-pledy": [
        "товары для сна",
        "постельное белье",
        "пододеяльник",
        "плед",
        "подушка",
        "одеяло",
        "наматрасник",
    ],
    "home-garden-shtory-zhalyuzi-i-karnizy": ["шторы", "жалюзи", "карниз"],
    "home-garden-posuda-kuhonnye-prinadlezhnosti": ["посуда", "сковорода", "кастрюля"],
    "home-garden-bytovaya-himiya-i-hoz-tovary": ["бытовая химия", "моющее средство", "хозтовары"],
    "home-garden-tovary-dlya-vannoy": ["аксессуары для ванной", "диспенсер", "коврик для ванной"],
    "home-garden-hranenie-i-organizatsiya": ["органайзер", "коробка для хранения", "вешалка"],
    "home-garden-dekor-i-interer": [
        "декор",
        "ваза",
        "фоторамка",
        "интерьер",
        "садовый декор",
        "садовая фигура",
        "новогодний декор",
        "ёлка искусственная",
        "гирлянда",
    ],
    "home-garden-zerkala": ["зеркало", "зеркало настенное"],
    "home-garden-komnatnye-rasteniya-i-tsvety": ["растения", "комнатные растения", "цветы"],
    "home-garden-iskusstvennye-tsvety-i-rasteniya": ["искусственные цветы", "искусственные растения"],
    "home-garden-sazhentsy-i-rassada": ["саженцы", "рассада"],
    "home-garden-semena-i-posadochnyy-material": ["семена", "газон", "посадочный материал"],
    "home-garden-gorshki-kashpo-i-grunty": ["горшок", "кашпо", "грунт", "почвосмесь"],
    "home-garden-udobreniya-dlya-rasteniy": ["удобрение", "подкормка"],
    "home-garden-sredstva-zaschity-rasteniy": ["пестицид", "защита растений"],
    "home-garden-teplitsy-i-parniki": ["теплица", "парник"],
    "home-garden-poliv-i-oroshenie": ["полив", "шланг", "капельный полив"],
    "home-garden-sadovyy-inventar": ["лопата", "грабли", "секатор"],
    "home-garden-sadovaya-tehnika": ["газонокосилка", "триммер", "садовая техника"],
    "home-garden-besedki-navesy-i-tovary-dlya-dachi": ["беседка", "навес", "дачи"],
    "home-garden-mangaly-barbekyu-tandyr-grili": ["мангал", "барбекю", "тандыр", "гриль"],
    "home-garden-basseyny-i-tovary-dlya-otdyha": [
        "бассейн",
        "надувной бассейн",
        "бассейны и аксессуары",
        "фильтр для бассейна",
    ],
    "home-garden-sadovye-kacheli-i-gamaki": [
        "качели",
        "садовые качели",
        "гамак",
        "гамаки",
    ],
    "home-garden-tovary-dlya-bani-i-sauny": ["баня", "сауна", "веник"],
    "home-garden-kaminy-pechi-i-aksessuary": ["камин", "печь", "каминный набор"],
    "home-garden-prochee-dlya-doma-i-sada": ["дом и сад", "для дома"],
    "repair-construction-elektrika-i-osveschenie": ["люстра", "бра", "торшер", "лампа", "освещение", "электрика"],
    # kids
    "kids-toys": ["игрушки", "конструктор", "кукла"],
    "kids-clothes": ["детская одежда", "комбинезон детский"],
    "kids-strollers": ["коляска", "автокресло"],
    # medical
    "medical-devices": ["тонометр", "глюкометр", "ингалятор"],
    "medical-care": ["бинт", "крем", "витамины", "бад"],
    "medical": ["медтовары", "аптека", "медицина"],
    # food
    "food-agri-products": ["продукты", "еда", "бакалея"],
    "food-agri-farm": ["молоко", "мясо", "курут", "сено", "ферма", "сельхоз", "яйцо", "мед"],
    "food-agri-feed": ["корм", "комбикорм", "силос"],
    # beauty products (modern L2)
    "beauty-kosmetika": ["гель-лак", "лак", "косметика", "помада", "крем"],
    "beauty-uhod-za-volosami": ["шампунь", "краска для волос"],
    "beauty-prochee-dlya-krasoty-i-uhoda": ["парик"],
    # fashion
    "fashion-clothing": ["платье", "куртка", "джинсы", "одежда", "пуховик"],
    "fashion-shoes": ["кроссовки", "ботинки", "обувь", "туфли"],
    "fashion-accessories": ["сумка", "часы", "ремень", "очки"],
    # sports
    "sports-equipment": ["лыжи", "мяч", "гантели", "гантель", "тренажёр"],
    "sports-tourism": ["палатка", "спальник", "рюкзак туристический"],
    "sports-music": ["гитара", "пианино", "синтезатор"],
    # books
    "books-fiction": ["книга", "книги", "роман"],
    "books-study": ["учебник", "канцтовары", "тетрадь"],
    # animals
    "animals-pets": ["щенок", "котенок", "собака", "кошка", "попугай"],
    "animals-livestock": ["корова", "бык", "теленок", "коза", "овца", "лошадь"],
    "animals-birds": ["курица", "утка", "гусь", "инкубатор"],
    # materials
    "materials-textile": ["ткань", "футер", "хлопок", "шелк", "трикотаж"],
    "materials-metal": ["металл", "арматура", "труба", "лист"],
    "materials-chemical": ["сырье", "реагент", "пластик гранула"],
    # ready business
    "ready-business-cafe": ["кофейня", "продам кафе", "ресторан", "бар"],
    "ready-business-retail": ["магазин", "продам бизнес", "торговая точка"],
    "ready-business-online": ["интернет магазин", "онлайн бизнес", "маркетплейс"],
    "ready-business-franchise": ["франшиза", "франчайзинг"],
    # free-exchange aliases removed — retired root must not resolve in production.
}

ROUTING_RULES: list[tuple[str, str, str, dict]] = [
    (
        "kamaz_delivery_sand_gravel",
        r"камаз.*(привез|достав|перевоз|щебен|песок|чернозем|чернозём)",
        "KAMAZ delivery → services-gruzoperevozki-i-pereezdy",
        {"target_category_slug": "services-gruzoperevozki-i-pereezdy"},
    ),
    (
        "kamaz_sale",
        r"прода.*камаз|камаз.*прода",
        "KAMAZ sale → transport-cargo",
        {"target_category_slug": "transport-cargo"},
    ),
    (
        "sell_cow",
        r"прода.*(коров|быка|телен|козы|овцы)",
        "livestock sale",
        {"target_category_slug": "animals-livestock"},
    ),
    (
        "farm_products",
        r"прода.*(молок|курут|сено|яйц|мед\b|фермер)",
        "farm products",
        {"target_category_slug": "food-agri-farm"},
    ),
    (
        "iphone_repair_service",
        r"ремонт.*(айфон|iphone|телефон|смартфон)",
        "phone repair service",
        {"target_category_slug": "services-remont-tehniki"},
    ),
    (
        "sell_iphone",
        r"прода.*(айфон|iphone|телефон|смартфон)",
        "phone sale",
        {"target_category_slug": "electronics-phones"},
    ),
    (
        "manicure_service",
        r"(делаю|оказываю|маникюр|педикюр|наращивание ногт)",
        "beauty service",
        {"target_category_slug": "services-uslugi-krasoty-i-stilya"},
    ),
    (
        "sell_gel_polish",
        r"прода.*(гель.?лак|лак для ногт|косметик)",
        "beauty products",
        {"target_category_slug": "beauty-kosmetika"},
    ),
    (
        "sell_coffee_machine",
        r"прода.*(кофемашин|кофемолк)",
        "cafe equipment",
        {"target_category_slug": "business-equipment-cafe"},
    ),
    (
        "sell_coffee_shop",
        r"прода.*(кофейн|кафе|ресторан|бар\b)",
        "ready business cafe",
        {"target_category_slug": "ready-business-kafe-restorany-i-obschepit"},
    ),
    (
        "sell_fabric",
        r"прода.*(ткан|футер|трикотаж)",
        "textile materials",
        {"target_category_slug": "materials-textile"},
    ),
    (
        "sell_dress",
        r"прода.*(платье|юбк|куртк|пуховик)",
        "clothing sale",
        {"target_category_slug": "fashion-clothing"},
    ),
]

MODERATION_RULES: list[tuple[str, str, str, ModerationAction, dict | None]] = [
    (
        "medical_antibiotics",
        r"(антибиотик|антибактериальн)",
        "MEDICAL_GUARDRAILS antibiotics",
        ModerationAction.block,
        {"guardrail": "medical"},
    ),
    (
        "medical_prescription",
        r"(рецептур|по\s+рецепту|rx\b)",
        "MEDICAL_GUARDRAILS prescription",
        ModerationAction.block,
        {"guardrail": "medical"},
    ),
    (
        "medical_hormones",
        r"(гормон|стероид|тестостерон|инсулин)",
        "MEDICAL_GUARDRAILS hormones",
        ModerationAction.block,
        {"guardrail": "medical"},
    ),
    (
        "medical_injections",
        r"(инъекц|укол|шприц|ампул)",
        "MEDICAL_GUARDRAILS injections",
        ModerationAction.block,
        {"guardrail": "medical"},
    ),
    (
        "medical_strong_drugs",
        r"(сильнодейств|психотроп|наркотическ)",
        "MEDICAL_GUARDRAILS strong",
        ModerationAction.block,
        {"guardrail": "medical"},
    ),
    (
        "business_mlm",
        r"(mlm|млм|сетевой\s+маркетинг)",
        "BUSINESS_MODERATION mlm",
        ModerationAction.moderation_queue,
        None,
    ),
    (
        "business_pyramid",
        r"(пирамид|пассивн.*доход|быстр.*прибыл|гарантированн.*доход)",
        "BUSINESS_MODERATION pyramid",
        ModerationAction.moderation_queue,
        None,
    ),
    (
        "trust_passport",
        r"(паспорт|passport)",
        "TRUST_AND_SAFETY passport",
        ModerationAction.moderation_queue,
        {"trust": "document"},
    ),
    (
        "trust_id_card",
        r"(\bid\s*карт|id\s*card|удостоверен)",
        "TRUST_AND_SAFETY id",
        ModerationAction.moderation_queue,
        {"trust": "document"},
    ),
    (
        "trust_bank_card",
        r"(банковск.*карт|bank\s*card|cvv|cvc)",
        "TRUST_AND_SAFETY bank card",
        ModerationAction.moderation_queue,
        {"trust": "document"},
    ),
    (
        "trust_driver_license",
        r"(водительск.*прав|driver\s*licen)",
        "TRUST_AND_SAFETY driver license",
        ModerationAction.moderation_queue,
        {"trust": "document"},
    ),
]

SEARCH_FILTERS: dict[str, list[tuple[str, str, CategoryFilterType]]] = {
    # Search SoT for car-sale: app.seeds.car_sale_v2 (loader overlay).
    "transport-car-sale": [],
    # Real Estate Search filters: app.seeds.real_estate_v2 (loader overlay).
    "real-estate-sale": [],
    "real-estate-rent": [],
    "real-estate-commercial": [],
    "electronics-phones": [
        ("price", "Цена", CategoryFilterType.range),
        ("brand", "Бренд", CategoryFilterType.select),
    ],
    "fashion-clothing": [
        ("price", "Цена", CategoryFilterType.range),
        ("size", "Размер", CategoryFilterType.select),
    ],
    "food-agri-farm": [
        ("price", "Цена", CategoryFilterType.range),
    ],
}

AI_DIALOGUE_HINTS: dict[str, str] = {
    "real-estate": "Недвижимость: город и тип обязательны.",
    "transport": "Транспорт: марка/модель только если не названы.",
    "jobs": "Работа: должность и город.",
    "services": "Услуга — действие. Не спрашивать advanced фильтры.",
    "repair-construction": "Ремонт/стройка: тип работ и город.",
    "electronics": "Техника: не дублировать память/модель если уже сказано.",
    "business-equipment": "Оборудование для бизнеса, не готовый бизнес.",
    "home-garden": "Дом и сад: тип товара и город.",
    "kids": "Детские товары: размер если одежда.",
    "medical": "Медтовары: MEDICAL_GUARDRAILS обязательны.",
    "food-agri": "Продукты/ферма: город/село и тип продукта.",
    "beauty": "Красота: товар vs услуга — уточнить при неясности.",
    "fashion": "Одежда: размер и состояние если не указаны.",
    "sports-hobby": "Спорт/хобби: тип инвентаря.",
    "stationery-books": "Книги/канцтовары.",
    "animals": "Животные: тип, возраст, город.",
    "materials": "Материалы и сырьё для производства: вид сырья.",
    "ready-business": "Готовый бизнес: не путать с оборудованием.",
}


def all_category_slugs() -> set[str]:
    from app.seeds.transport_canonical import TRANSPORT_CANONICAL_SLUGS

    slugs = {r[0] for r in ROOT_CATEGORIES}
    for subs in SUBCATEGORIES.values():
        slugs.update(s[0] for s in subs)
    slugs.update(TRANSPORT_CANONICAL_SLUGS)
    slugs.update(CORE_FIELDS.keys())
    return slugs


def seed_inventory_counts() -> dict[str, int]:
    """Pure-data counts for tests and reports."""
    sub_count = sum(len(v) for v in SUBCATEGORIES.values())
    alias_count = sum(len(v) for v in CATEGORY_ALIASES.values())
    core_count = sum(len(v) for v in CORE_FIELDS.values())
    optional_count = sum(len(v) for v in OPTIONAL_FIELDS.values())
    return {
        "root_categories": len(ROOT_CATEGORIES),
        "subcategories": sub_count,
        "category_aliases": alias_count,
        "core_field_definitions": core_count,
        "optional_field_definitions": optional_count,
        "routing_rules": len(ROUTING_RULES),
        "moderation_rules": len(MODERATION_RULES),
    }
