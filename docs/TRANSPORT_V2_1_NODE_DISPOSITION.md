# TRANSPORT V2.1 — Node disposition (old → new)

Источник ID/slug: live dev PostgreSQL до/после миграции V2.1.  
«Убрать» = `is_active=false` (история сохранена), не физический DELETE.

## L1 under `transport`

| Действие | Slug | Имя |
|---|---|---|
| KEEP | `transport-car-sale` | Продажа авто |
| RENAME (name only) | `transport-auto-parts` | Запчасти (было Автозапчасти) |
| KEEP | `transport-tires-wheels` | Шины и диски |
| KEEP | `transport-accessories-tuning` | Аксессуары и тюнинг |
| KEEP | `transport-moto-tech` | Мототехника |
| KEEP | `transport-electric` | Электротранспорт |
| KEEP | `transport-bicycles` | Велосипеды |
| KEEP | `transport-cargo` | Грузовой транспорт |
| CREATE | `transport-buses-microbuses-motorhomes` | Автобусы, микроавтобусы и автодома |
| KEEP | `transport-special-equipment` | Спецтехника |
| KEEP | `transport-farm-machinery` | Сельхозтехника |
| KEEP | `transport-watercraft` | Водный транспорт |
| KEEP | `transport-trailers` | Прицепы и полуприцепы |
| KEEP | `transport-rental` | Аренда транспорта |
| RETIRE branch | `transport-commercial` | Коммерческий транспорт |
| RETIRE branch | `transport-auto-services` | Автоуслуги → Services pending |
| RETIRE branch | `transport-buyback-exchange` | Скупка и обмен (целиком) |

## Ключевые leaf-решения

| Старый slug / тема | Итог |
|---|---|
| `transport-commercial-mikroavtobusy` / `…-avtobusy` | MOVE → parent `transport-buses-microbuses-motorhomes` |
| `transport-buses-avtodoma` | CREATE under buses |
| `transport-commercial-furgony` | MERGE listings → `transport-cargo-furgony`; RETIRE |
| `transport-commercial-pikapy` | RETIRE (покрыто Продажей авто / кузов) |
| `transport-commercial-spetsavtomobili` | RETIRE |
| `transport-cargo-spetsgruzoviki` | RETIRE; CREATE `transport-cargo-tsisterny`, `…-evakuatory` |
| `transport-special-equipment-dorozhnaya-tehnika` | RETIRE (катки/грейдеры остаются) |
| Манипуляторы | KEEP в спецтехнике |
| `…-avtosvet-i-tyuning-optiki` | MERGE → optics under кузов; RETIRE |
| Optics `…-optika-fary-i-fonari` | MOVE under `…-kuzovnye-detali` |
| `…-elektronika-i-bezopasnost` | RETIRE; CREATE камеры/парктроники + сигнализации |
| `…-aksessuary-kuzova` | RETIRE → CREATE внешние аксессуары и декор |
| `…-instrumenty-i-avtoaksessuary` | RETIRE → CREATE автомобильные принадлежности |
| Внедорожный / спортивный тюнинг | RETIRE (не места публикации) |
| Vehicle-specific `*-zapchasti*` | MERGE → `transport-auto-parts`; RETIRE |
| Электромото/скутер/квадро/багги/карты/трайки как отд. кат. | MERGE в базовый вид; RETIRE duplicate |
| `…-lodochnye-motory` | MERGE → `…-dvigatel-i-navesnoe`; RETIRE |
| Прицепы для водного / сельхоз | MERGE → `transport-trailers`; RETIRE |
| Надувные лодки как отд. кат. | RETIRE (конструкция ≠ отдельная публикация) |
| Сельхоз `…-navesnoe-oborudovanie` | RETIRE (агрегаты по функции + характеристика) |
| Аренда `…-kommercheskiy-transport`, `…-arenda-s-voditelem`, `…-dolgosrochnaya-arenda` | RETIRE (вид/долгосрочность/водитель → параметры или Services) |
| Ремонт-ветки в Транспорте | RETIRE; Services mapping **pending** |

## Alias retarget

| Alias | Target |
|---|---|
| фара / оптика / фонарь | `transport-auto-parts-optika-fary-i-fonari` |

## Services pending (не создавались новые листья)

См. `SERVICES_PENDING` в `app/seeds/transport_v2_1.py`:
- `transport-auto-services` (+ шиномонтаж, эвакуация)
- `transport-rental-arenda-s-voditelem`
- ремонты спецтехники / прочие repair leaves

## Полный перечень RETIRE_LEAF / MERGE / NEW / RENAME / MOVE

Канонический машинный список: `aivai_backend/app/seeds/transport_v2_1.py`  
(`RETIRE_BRANCH_ROOT_SLUGS`, `RETIRE_LEAF_SLUGS`, `MERGE_LISTING_REMAP`, `NEW_CATEGORIES`, `RENAME_NAMES`, `MOVE_PARENT`, `BODY_CHILD_SLUGS`).
