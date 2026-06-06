# AiVai Backend

API на **FastAPI** с асинхронным **SQLAlchemy 2.0** и **PostgreSQL** (asyncpg). Слои: модели → репозитории → сервисы → эндпоинты (Clean Architecture для HTTP: API → Service → Repository).

## Требования

- Python **3.11+** (для приложения в Docker см. Dockerfile)
- Docker и Docker Compose (для БД и контейнерного приложения)

## Переменные окружения (`.env`)

Скопируйте [.env.example](.env.example) в `.env` и при необходимости отредактируйте.

| Переменная | Назначение | Пример |
| ---------- | ---------- | ------ |
| `POSTGRES_USER` | Пользователь БД | `aivai` |
| `POSTGRES_PASSWORD` | Пароль БД | _(сильный пароль)_ |
| `POSTGRES_DB` | Имя базы | `aivai` |
| `POSTGRES_SERVER` | Хост БД | `localhost` или `db` в Compose |
| `POSTGRES_PORT` | Порт БД | `5432` |
| `JWT_SECRET_KEY` | Секрет подписи JWT | _(длинная случайная строка)_ |
| `ALGORITHM` | Алгоритм JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL access-токена | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | TTL refresh-токена | `7` |
| `MEDIA_ROOT` | Каталог для загруженных файлов | `media` |
| `MEDIA_URL` | URL-префикс для раздачи медиа | `/media/` |
| `OPENAI_API_KEY` | Ключ OpenAI API для Whisper STT (`/voice/audio`); опционально | _(пусто — аудио-эндпоинт вернёт 502)_ |
| `LOG_LEVEL` | Уровень логов (`DEBUG`, `INFO`, …) | `INFO` |
| `LOG_JSON` | Флаг JSON-логов: `1`, `true` или `yes` | _(пусто → key=value)_ |

## Локальная разработка

1. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Поднимите PostgreSQL (или используйте Docker Compose только для `db`).

3. Примените миграции:

   ```bash
   alembic upgrade head
   ```

4. Запуск приложения:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Docker Compose

Из корня проекта:

```bash
docker compose up --build
```

Сервис приложения слушает порт **8000**. После первого запуска примените миграции внутри контейнера приложения:

```bash
docker compose exec app alembic upgrade head
```

## Проверка готовности

- **`GET /api/v1/health`** — сервис/репозиторий выполняет `SELECT 1` в текущей сессии.
- **`GET /ready`** — то же для readiness-проб.
- Ответ успеха: `{"status":"ok"}`. При ошибках БД срабатывают общие обработчики ошибок приложения.

## Ошибки и запрос

Ошибочные ответы в едином формате:

```json
{
  "detail": "сообщение",
  "code": "ERROR_CODE",
  "status": 400,
  "request_id": "uuid"
}
```

В заголовках ответа присутствует **`X-Request-ID`**; при желании передайте свой `X-Request-ID` во входящем запросе.

## Автоматические тесты

После установки зависимостей из `requirements.txt`:

```bash
pytest tests/
```

Используется **`httpx.AsyncClient`** и **dependency overrides** (без обязательного запуска PostgreSQL; `docker-compose` не меняется). Маркер `@pytest.mark.integration` зарегистрирован в `pytest.ini` для возможных регрессий с реальной БД.

## Документация API

После запуска: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Ограничение частоты (auth)

Эндпоинты **`POST /api/v1/auth/login`** и **`POST /api/v1/auth/refresh`** ограничены **5 запросами в минуту на IP** через in-memory rate limiter (без Redis).

## Voice AI (текст и аудио)

### Текстовые команды

Эндпоинт **`POST /api/v1/voice/command`**, только с **Bearer access-токеном** (`get_current_user`).

- Тело: `{"text": "<команда>"}`. Пустая строка или длина текста **> 1000** символов → **400** с `detail`: «Некорректная длина текста».
- Ответ: `intent` (rule-based RegEx), `message`, опционально `data`.
- Намерения: **`create_listing`** (черновик без `category_id` или создание через `ListingService`), **`save_search`** (при отсутствии параметров поиска — без записи в БД), **`search_listings`** (лента через `ListingService.get_feed`).
- Владелец объявления и сохранённого поиска всегда берётся из **текущего пользователя** (`owner_id` / `user_id` не из текста команды).

### Voice AI Audio (Speech-to-Text)

Эндпоинт **`POST /api/v1/voice/audio`**: multipart, поле файла **`file`** (wav / mp3 / m4a), размер **до 10 МБ**, с **Bearer access-токеном**.

Транскрибация через **OpenAI Whisper** (`whisper-1`) по HTTPS (**`httpx`**, без пакета `openai`). Установите в окружении **`OPENAI_API_KEY`** (см. таблицу ниже и `.env.example`). Приложение **стартует и без ключа**; попытка вызвать `/voice/audio` без ключа или при ошибке API → **502**, `detail`: «Сервис распознавания речи временно недоступен». Пустой текст после транскрибации → **400**, `detail`: «Не удалось распознать речь». После успешного STT ответ совпадает с **`VoiceCommandResponse`** из текстового потока (тот же `handle_command`).

#### Pipeline обработки аудио

`audio` → `STT (Whisper)` → `text` → `VoiceService` → `intent` → `действие`

#### Пример запроса (`curl`)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/voice/audio" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@./sample-command.m4a"
```

#### Пример ответа (`JSON`)

```json
{
  "intent": {
    "intent": "create_listing",
    "confidence": 0.91,
    "extracted": {
      "title": "iPhone 13 128GB",
      "price": 42000,
      "currency": "KGS",
      "category_id": 12
    }
  },
  "message": "Объявление создано.",
  "data": {
    "listing": {
      "id": 101,
      "title": "iPhone 13 128GB",
      "price": "42000",
      "currency": "KGS",
      "status": "draft"
    }
  }
}
```

Важно: endpoint **`/voice/audio`** НЕ содержит бизнес-логики. Вся обработка происходит через **`VoiceService`**.

Важно: **`OPENAI_API_KEY`** используется только на backend и никогда не передаётся на клиент.
