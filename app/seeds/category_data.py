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
    ("free-exchange", "Отдам бесплатно, обмен и находки", CategoryEntityType.general, 190),
]

SUBCATEGORIES: dict[str, list[tuple[str, str, CategoryEntityType]]] = {
    "real-estate": [
        ("real-estate-sale", "Продажа", CategoryEntityType.object),
        ("real-estate-rent", "Аренда", CategoryEntityType.object),
        ("real-estate-commercial", "Коммерческая", CategoryEntityType.object),
    ],
    "transport": [
        ("transport-cars", "Легковые автомобили", CategoryEntityType.object),
        ("transport-parts", "Запчасти и аксессуары", CategoryEntityType.object),
        ("transport-trucks", "Грузовики и спецтехника", CategoryEntityType.object),
        ("transport-moto", "Мотоциклы", CategoryEntityType.object),
        ("transport-water", "Водный транспорт", CategoryEntityType.object),
    ],
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
    "repair-construction": [
        ("repair-building", "Ремонт помещений", CategoryEntityType.construction),
        ("construction-work", "Строительные работы", CategoryEntityType.construction),
        ("repair-tools", "Инструменты и оборудование", CategoryEntityType.construction),
    ],
    "electronics": [
        ("electronics-phones", "Телефоны", CategoryEntityType.object),
        ("electronics-computers", "Компьютеры", CategoryEntityType.object),
        ("electronics-appliances", "Бытовая техника", CategoryEntityType.object),
        ("electronics-tv", "ТВ и аудио", CategoryEntityType.object),
    ],
    "business-equipment": [
        ("business-equipment-cafe", "Кафе и ресторан", CategoryEntityType.equipment),
        ("business-equipment-retail", "Торговое оборудование", CategoryEntityType.equipment),
        ("business-equipment-industrial", "Промышленное", CategoryEntityType.equipment),
    ],
    "home-garden": [
        ("home-furniture", "Мебель", CategoryEntityType.object),
        ("home-decor", "Декор и текстиль", CategoryEntityType.object),
        ("home-garden-plants", "Сад и растения", CategoryEntityType.object),
    ],
    "kids": [
        ("kids-toys", "Игрушки", CategoryEntityType.object),
        ("kids-clothes", "Одежда для детей", CategoryEntityType.object),
        ("kids-strollers", "Коляски и автокресла", CategoryEntityType.object),
    ],
    "medical": [
        ("medical-devices", "Медицинские приборы", CategoryEntityType.object),
        ("medical-care", "Средства ухода", CategoryEntityType.object),
    ],
    "food-agri": [
        ("food-agri-products", "Продукты питания", CategoryEntityType.food),
        ("food-agri-farm", "Фермерская продукция", CategoryEntityType.food),
        ("food-agri-feed", "Корма", CategoryEntityType.food),
    ],
    "beauty": [
        ("beauty-cosmetics", "Косметика и уход", CategoryEntityType.object),
        ("beauty-hair", "Волосы и парики", CategoryEntityType.object),
    ],
    "fashion": [
        ("fashion-clothing", "Одежда", CategoryEntityType.object),
        ("fashion-shoes", "Обувь", CategoryEntityType.object),
        ("fashion-accessories", "Аксессуары", CategoryEntityType.object),
    ],
    "sports-hobby": [
        ("sports-equipment", "Спортивный инвентарь", CategoryEntityType.object),
        ("sports-tourism", "Туризм и отдых", CategoryEntityType.object),
        ("sports-music", "Музыкальные инструменты", CategoryEntityType.object),
    ],
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
    "ready-business": [
        ("ready-business-cafe", "Кафе и общепит", CategoryEntityType.business),
        ("ready-business-retail", "Магазин и торговля", CategoryEntityType.business),
        ("ready-business-online", "Онлайн-бизнес", CategoryEntityType.business),
        ("ready-business-franchise", "Франшизы", CategoryEntityType.business),
    ],
    "free-exchange": [
        ("free-give", "Отдам бесплатно", CategoryEntityType.general),
        ("free-exchange-swap", "Обмен", CategoryEntityType.general),
        ("free-found", "Находки", CategoryEntityType.general),
    ],
}

# field_key, label, field_type, ai_hint (None = skip dialogue hint)
_CORE = CategoryFieldType

CORE_FIELDS: dict[str, list[tuple[str, str, CategoryFieldType, str | None]]] = {
    # --- transport ---
    "transport-cars": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("brand", "Марка", _CORE.brand, "Какая марка?"),
        ("model", "Модель", _CORE.model, "Какая модель?"),
        ("year", "Год", _CORE.year, "Какой год выпуска?"),
        ("steering_side", "Руль", _CORE.enum, "Левый или правый руль?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, "Какое состояние?"),
    ],
    "transport-parts": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("part_type", "Тип запчасти", _CORE.string, "Что за запчасть?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, "Новая или б/у?"),
    ],
    "transport-trucks": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("brand", "Марка", _CORE.brand, "Какая марка?"),
        ("year", "Год", _CORE.year, "Год выпуска?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, "Состояние?"),
    ],
    "transport-moto": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("brand", "Марка", _CORE.brand, None),
        ("price", "Цена", _CORE.price, "Какая цена?"),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "transport-water": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Тип", _CORE.string, "Лодка, катер, яхта?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    # --- real estate ---
    "real-estate-sale": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("district", "Район", _CORE.string, "Какой район?"),
        ("deal_type", "Сделка", _CORE.enum, "Продажа или аренда?"),
        ("property_type", "Тип", _CORE.enum, "Квартира, дом или участок?"),
        ("rooms", "Комнаты", _CORE.number, "Сколько комнат?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
    ],
    "real-estate-rent": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("district", "Район", _CORE.string, "Какой район?"),
        ("property_type", "Тип", _CORE.enum, "Квартира, дом, комната?"),
        ("rooms", "Комнаты", _CORE.number, "Сколько комнат?"),
        ("price", "Цена", _CORE.price, "Цена аренды?"),
    ],
    "real-estate-commercial": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("property_type", "Тип", _CORE.string, "Офис, склад, помещение?"),
        ("price", "Цена", _CORE.price, "Какая цена?"),
    ],
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
    # --- home & garden ---
    "home-furniture": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Мебель", _CORE.string, "Диван, шкаф, стол?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "home-decor": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Товар", _CORE.string, "Что продаёте?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "home-garden-plants": [
        ("city", "Город", _CORE.city, "Город или село?"),
        ("item_type", "Растения", _CORE.string, "Что продаёте?"),
        ("price", "Цена", _CORE.price, None),
    ],
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
    # --- beauty ---
    "beauty-cosmetics": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Товар", _CORE.string, "Гель-лак, косметика?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, "Новое или б/у?"),
    ],
    "beauty-hair": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Товар", _CORE.string, "Парик, наращивание?"),
        ("price", "Цена", _CORE.price, None),
    ],
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
    # --- sports & hobby ---
    "sports-equipment": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Инвентарь", _CORE.string, "Что продаёте?"),
        ("price", "Цена", _CORE.price, None),
        ("condition", "Состояние", _CORE.enum, None),
    ],
    "sports-tourism": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Товар", _CORE.string, "Палатка, рюкзак?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "sports-music": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("item_type", "Инструмент", _CORE.string, "Гитара, барабан?"),
        ("price", "Цена", _CORE.price, None),
    ],
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
    # --- materials ---
    "materials-textile": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("material_type", "Материал", _CORE.string, "Ткань, футер?"),
        ("quantity", "Количество", _CORE.string, "Метраж или вес?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "materials-metal": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("material_type", "Металл", _CORE.string, "Что продаёте?"),
        ("quantity", "Количество", _CORE.string, None),
        ("price", "Цена", _CORE.price, None),
    ],
    "materials-chemical": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("material_type", "Сырьё", _CORE.string, "Что за товар?"),
        ("price", "Цена", _CORE.price, None),
    ],
    # --- ready business ---
    "ready-business-cafe": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("business_type", "Бизнес", _CORE.string, "Кофейня, ресторан?"),
        ("operating_period", "Срок работы", _CORE.string, "Сколько работает?"),
        ("included_assets", "Активы", _CORE.string, "Что входит?"),
        ("price", "Цена", _CORE.price, "Цена продажи?"),
    ],
    "ready-business-retail": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("business_type", "Бизнес", _CORE.string, "Магазин, пункт?"),
        ("operating_period", "Срок", _CORE.string, None),
        ("price", "Цена", _CORE.price, None),
    ],
    "ready-business-online": [
        ("city", "Город", _CORE.city, "Город регистрации?"),
        ("business_type", "Онлайн-бизнес", _CORE.string, "Ниша?"),
        ("price", "Цена", _CORE.price, None),
    ],
    "ready-business-franchise": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("business_type", "Франшиза", _CORE.string, "Какая франшиза?"),
        ("price", "Цена", _CORE.price, "Паушальный взнос?"),
    ],
    # --- free / exchange / found ---
    "free-give": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("district", "Район", _CORE.string, "Район или ориентир?"),
        ("announcement_type", "Тип", _CORE.enum, "Отдам бесплатно?"),
        ("item_type", "Вещь", _CORE.string, "Что отдаёте?"),
        ("condition", "Состояние", _CORE.string, "Состояние?"),
    ],
    "free-exchange-swap": [
        ("city", "Город", _CORE.city, "В каком городе?"),
        ("announcement_type", "Обмен", _CORE.string, "На что меняете?"),
        ("item_type", "Вещь", _CORE.string, "Что предлагаете?"),
    ],
    "free-found": [
        ("city", "Город", _CORE.city, "Где нашли?"),
        ("district", "Район", _CORE.string, "Район или место?"),
        ("announcement_type", "Находка", _CORE.enum, "Что нашли?"),
        ("item_type", "Предмет", _CORE.string, "Опишите находку"),
        ("condition", "Статус", _CORE.string, "Сдано в полицию?"),
    ],
}

OPTIONAL_FIELDS: dict[str, list[tuple[str, str, CategoryFieldType]]] = {
    "transport-cars": [
        ("mileage", "Пробег", _CORE.number),
        ("color", "Цвет", _CORE.string),
        ("vin", "VIN", _CORE.string),
        ("engine_volume", "Объём двигателя", _CORE.string),
    ],
    "real-estate-sale": [
        ("area", "Площадь", _CORE.decimal),
        ("floor", "Этаж", _CORE.number),
        ("total_floors", "Этажность", _CORE.number),
    ],
    "real-estate-rent": [
        ("area", "Площадь", _CORE.decimal),
        ("deposit", "Залог", _CORE.price),
    ],
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
    "ready-business-cafe": [
        ("revenue", "Выручка", _CORE.price),
        ("staff_count", "Персонал", _CORE.number),
    ],
    "animals-pets": [
        ("vaccinated", "Прививки", _CORE.boolean),
        ("documents", "Документы", _CORE.boolean),
    ],
}

CATEGORY_ALIASES: dict[str, list[str]] = {
    # transport
    "transport-cars": ["авто", "машина", "легковушка", "car", "автомобиль", "седан"],
    "transport-parts": ["запчасти", "шины", "диски", "аккумулятор", "бампер", "фара"],
    "transport-trucks": ["грузовик", "камаз", "газель", "фура", "спецтехника"],
    "transport-moto": ["мото", "мотоцикл", "скутер", "байк"],
    # real estate
    "real-estate-sale": ["квартира", "дом", "недвижимость", "участок", "продам квартиру"],
    "real-estate-rent": ["аренда", "сдам", "снять квартиру", "арендую"],
    "real-estate-commercial": ["офис", "склад", "коммерческая"],
    # jobs
    "jobs-vacancies": ["вакансия", "работа", "ищу сотрудника", "требуется"],
    "jobs-resume": ["резюме", "ищу работу", "трудоустройство"],
    # services
    "services-transport": [
        "перевозка",
        "доставка",
        "эвакуатор",
        "грузоперевозки",
        "привезти",
        "щебень",
        "песок",
        "чернозем",
    ],
    "services-repair": [
        "ремонт телефона",
        "ремонт айфона",
        "ремонт iphone",
        "ремонт ноутбука",
        "ремонт стиральной",
    ],
    "services-beauty": ["маникюр", "педикюр", "наращивание", "стрижка", "брови", "ресницы"],
    "services-cleaning": ["уборка", "клининг", "химчистка"],
    "services-tutoring": ["репетитор", "обучение", "курсы"],
    "services-legal": ["юрист", "адвокат", "нотариус"],
    "services-it": ["разработка сайта", "smm", "таргет", "дизайн"],
    # repair construction
    "repair-building": ["ремонт квартиры", "отделка", "штукатурка", "плитка"],
    "construction-work": ["строительство", "фундамент", "кровля", "забор"],
    "repair-tools": ["перфоратор", "болгарка", "стройинструмент"],
    # electronics
    "electronics-phones": ["телефон", "айфон", "iphone", "смартфон", "android"],
    "electronics-computers": ["ноутбук", "компьютер", "пк", "macbook"],
    "electronics-appliances": ["холодильник", "стиральная", "плита", "кондиционер"],
    "electronics-tv": ["телевизор", "тв", "колонки", "саундбар"],
    # business equipment
    "business-equipment-cafe": ["кофемашина", "кофемолка", "барное", "кухонное оборудование"],
    "business-equipment-retail": ["витрина", "касса", "холодильник торговый"],
    "business-equipment-industrial": ["станок", "пресс", "конвейер"],
    # home
    "home-furniture": ["диван", "шкаф", "кровать", "стол", "мебель"],
    "home-decor": ["шторы", "ковер", "люстра", "декор"],
    "home-garden-plants": ["растения", "саженцы", "газон"],
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
    # beauty products
    "beauty-cosmetics": ["гель-лак", "лак", "косметика", "помада", "крем"],
    "beauty-hair": ["шампунь", "краска для волос", "парик"],
    # fashion
    "fashion-clothing": ["платье", "куртка", "джинсы", "одежда", "пуховик"],
    "fashion-shoes": ["кроссовки", "ботинки", "обувь", "туфли"],
    "fashion-accessories": ["сумка", "часы", "ремень", "очки"],
    # sports
    "sports-equipment": ["велосипед", "лыжи", "мяч", "гантели"],
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
    # free exchange
    "free-give": ["отдам", "бесплатно", "даром", "отдам даром"],
    "free-exchange-swap": ["обмен", "меняю", "обменяю"],
    "free-found": ["нашел", "нашла", "находка", "потерял", "потеряла"],
}

ROUTING_RULES: list[tuple[str, str, str, dict]] = [
    (
        "kamaz_delivery_sand_gravel",
        r"камаз.*(привез|достав|перевоз|щебен|песок|чернозем|чернозём)",
        "KAMAZ delivery → services-transport",
        {"target_category_slug": "services-transport"},
    ),
    (
        "kamaz_sale",
        r"прода.*камаз|камаз.*прода",
        "KAMAZ sale → transport-trucks",
        {"target_category_slug": "transport-trucks"},
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
        {"target_category_slug": "services-repair"},
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
        {"target_category_slug": "services-beauty"},
    ),
    (
        "sell_gel_polish",
        r"прода.*(гель.?лак|лак для ногт|косметик)",
        "beauty products",
        {"target_category_slug": "beauty-cosmetics"},
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
        {"target_category_slug": "ready-business-cafe"},
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
    (
        "free_sofa",
        r"отдам.*(диван|шкаф|холодильник|вещ)",
        "free give",
        {"target_category_slug": "free-give"},
    ),
    (
        "found_documents",
        r"наш[её]л.*(паспорт|удостоверен|карт|права|id\b)",
        "found items trust",
        {"target_category_slug": "free-found"},
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
    "transport-cars": [
        ("year", "Год", CategoryFilterType.range),
        ("price", "Цена", CategoryFilterType.range),
        ("brand", "Марка", CategoryFilterType.select),
    ],
    "real-estate-sale": [
        ("price", "Цена", CategoryFilterType.range),
        ("rooms", "Комнаты", CategoryFilterType.range),
        ("area", "Площадь", CategoryFilterType.range),
    ],
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
    "materials": "Сырьё: материал и количество.",
    "ready-business": "Готовый бизнес: не путать с оборудованием.",
    "free-exchange": "Бесплатно/обмен/находки: TRUST_AND_SAFETY для документов.",
}


def all_category_slugs() -> set[str]:
    slugs = {r[0] for r in ROOT_CATEGORIES}
    for subs in SUBCATEGORIES.values():
        slugs.update(s[0] for s in subs)
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
