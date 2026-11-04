# TRANSPORT V2.1 — Implementation Report

**Дата:** 2026-09-19  
**Режим:** dev only (production не трогали). Commit/push не выполнялись.

Спецификация: [`TRANSPORT_V2_1_FINAL.md`](./TRANSPORT_V2_1_FINAL.md)  
Сопоставление узлов: [`TRANSPORT_V2_1_NODE_DISPOSITION.md`](./TRANSPORT_V2_1_NODE_DISPOSITION.md)

---

## CODE / SCHEMA IMPLEMENTED

### Backend / PostgreSQL
- Константы и желаемое дерево: `app/seeds/transport_v2_1.py`
- Идемпотентная миграция (snapshot → apply → verify): `app/seeds/transport_v2_1_migration.py`
- CLI: `python -m scripts.migrate_transport_v2_1` (`--dry-run`, `--verify-only`)
- Seed loader: повторный seed **не** возвращает retired V2.1 ветки (`app/seeds/loader.py`)
- Alias retarget для автосвета → `transport-auto-parts-optika-fary-i-fonari`
- Обновлены resolver/visual_signals/action_compatibility ссылки (без нового обучения ИИ)
- Core fields + search filters для согласованных L1 веток (не car-sale): parts, tires, accessories, moto, electric, bicycles, cargo, buses, special, farm, water, trailers, rental

### Flutter
- L1 панель: ровно 14 подкатегорий, «Запчасти», без коммерческого / автоуслуг / скупки
- Панели видов: parts groups, tires×4, accessories V2.1, moto/electric/bicycles/cargo/buses(+автодома)/special/farm/water/trailers/rental
- Wiring в `home_feed_screen.dart` для новой ветки автобусов/автодомов
- Каталог UI по-прежнему label-driven; **единый SoT категорий — API/БД**, не независимая копия дерева для публикации

### Документация
- `TRANSPORT_V2_1_FINAL.md` (backend + копия в mobile/docs)
- Этот отчёт + disposition mapping

---

## DEV MIGRATION APPLIED

| Проверка | Результат |
|---|---|
| Preflight + apply | Выполнено на dev PostgreSQL |
| Snapshot | `.local/transport_v2_1_rollback/pre_v2_1_*.json` (каталог в `.gitignore`) |
| `l1_match` | `true` (14 slug в нужном порядке) |
| `forbidden_still_active` | `[]` |
| `parts_name` | «Запчасти» (slug `transport-auto-parts` сохранён) |
| Optics parent | = Кузов (`kuzov_id` / parent slug `transport-auto-parts-kuzovnye-detali`) |
| Автобусы/микроавтобусы | Перенесены под `transport-buses-microbuses-motorhomes`; автодома созданы |
| Повторный dry-run | Идемпотентен, дублей L1 нет |
| Активных transport-узлов | 128 active / 87 inactive (история сохранена, без массового DELETE) |
| Продажа авто listings | **96 active + 19 draft** — без потерь |

Docker `app` пересобран и перезапущен с кодом V2.1 (dev). Worker/production не деплоились отдельно как prod.

**LAN host для телефона:** машина сейчас `192.168.1.15` (правило `.20` с этой станции недоступно). API проверен на `http://192.168.1.15:8000`.

**Сопутствующий hotfix для поднятия Docker-образа:** в `app/api/deps.py` добавлен отсутствующий импорт `AssistantConversationService` (иначе uvicorn падал при старте свежего образа; к каталогу V2.1 не относится).

---

## AUTOMATED TESTS

| Команда / проверка | Результат |
|---|---|
| `pytest tests/test_transport_v2_1.py -q` | **1 passed** (L1 + optics + car-sale listings) |
| `python -m scripts.migrate_transport_v2_1 --verify-only` | `l1_match: true` |
| `python -m scripts.migrate_transport_v2_1 --dry-run` | идемпотентно OK |
| `GET /api/v1/health` (127.0.0.1 и 192.168.1.15) | `ok` |
| `GET /api/v1/categories/tree` → transport children | **14**, ожидаемые slug |
| Unit-only ≠ полный E2E формы | см. blockers |

Не переписывались frozen benchmark-результаты ради зелёного отчёта.

---

## MANUAL SAMSUNG

| Пункт | Статус |
|---|---|
| `flutter run -d RR8TA03RLJM` с `API_BASE_URL=http://192.168.1.15:8000` | **Deploy OK** (Syncing files / Flutter run key commands) |
| Ручной обход L1 / фильтров / черновика на SM A235F | **MANUAL PENDING** (агент не выполнял QA на телефоне) |

---

## REMAINING BLOCKERS / LIMITATIONS

1. **Услуги:** retired «Автоуслуги» / ремонт / аренда с водителем **не** перенесены в новые листья Services — целевые подразделы не утверждены. Узлы выведены из активного Транспорта; см. `SERVICES_PENDING` в `transport_v2_1.py` и disposition.
2. **Справочники:** полные мировые марки/модели спецтехники, OEM-совместимость запчастей, детальные enum-значения многих фильтров — **не** выдуманы; поля/фильтры созданы, наполнение значений — частично / зависит от существующих справочников.
3. **Flutter ↔ deep filters:** L1/L2 панели обновлены; полный цикл «все поля публикации → draft reopen → multi-filter search» для каждой не-car-sale ветки **не** закрыт отдельным E2E-автотестом на устройстве.
4. **IP:** авто-правило `.20` устарело относительно текущего LAN `.15` — телефон должен бить в актуальный хост.
5. **Детские товары:** отдельный существующий дубль велосипедов вне Транспорта в этом прогоне не инвентаризировался построчно; новые дубли не создавались.

---

## Что сознательно сохранено

- `transport-car-sale` целиком (ID, схемы, UI, объявления/черновики)
- Недвижимость / геобаза / дизайн / фото+intent / ручной override категории
- Параметр «Возможен обмен» в Продаже авто
- Исторические категории (`is_active=false`), без физического стирания

---

## Вердикт

| Слой | Оценка |
|---|---|
| Каталог L1 + retire/merge/move | **DONE (dev)** |
| Core fields / filters в БД для веток V2.1 | **DONE (базовый набор)** |
| Flutter L1/L2 labels | **DONE** |
| Полный E2E всех фильтров на Samsung | **MANUAL PENDING** |
| Услуги (перенос работ) | **НЕ ЗАВЕРШЕНО** (осознанная граница) |
| «Транспорт полностью готов» | **НЕТ** — каталог+базовые схемы да; полный продуктовый цикл фильтров и Services — нет |
