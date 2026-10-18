# JANA ADDRESS

Простой backend для хакатон-кейса: получает адрес одной строкой и возвращает
поля, которые требуются в задании. Основной разбор полностью локальный — он не
зависит от внешнего геокодера и не теряет записи, которые не удалось распознать.

## Автономный запуск через Docker

Compose поднимает весь проект локально:

- `frontend` — собранный React-интерфейс под Nginx;
- `backend` — FastAPI, который перед стартом применяет Alembic-миграции;
- `db` — PostgreSQL 16 с постоянным Docker-томом;
- все 210 276 записей справочника автоматически импортируются при первом
  создании базы.

Перед первым запуском, пока интернет доступен, создайте локальный `.env`,
укажите в нём `POSTGRES_PASSWORD` и один раз соберите образы:

```powershell
cd C:\jana_address
Copy-Item .env.example .env
# Откройте .env и замените change_me на локальный пароль.
docker compose build --pull
docker compose up -d
```

На подготовленном ноутбуке для последующих запусков без интернета выполните:

```powershell
cd C:\jana_address
docker compose up -d --no-build
docker compose ps
```

Все три контейнера должны получить статус `healthy`. После запуска доступны:

- интерфейс: `http://localhost:5173`;
- Swagger с локальными ресурсами, работающий без интернета:
  `http://localhost:5173/docs`;
- backend напрямую: `http://localhost:8000`;
- PostgreSQL для pgAdmin: `localhost:5433`, база `jana_address_db`;
- пользовательские адреса: `public.address_records`.

Остановить проект без удаления данных:

```powershell
cd C:\jana_address
docker compose down
```

Не добавляйте `--volumes`: эта опция удалит Docker-базу и сохранённые адреса.
Том `jana-address-postgres-data` переживает обычную остановку контейнеров и
перезагрузку ноутбука.

Если исходный код изменился и интернет доступен, пересоберите образы:

```powershell
cd C:\jana_address
docker compose build --pull
docker compose up -d
```

## Быстрый локальный запуск

В проекте используется созданная локальная PostgreSQL-база `jana_address_db`.
Параметры подключения находятся только в локальном `.env`; `.env.example`
содержит безопасный шаблон без настоящего пароля.

### 1. Backend

В первом терминале PowerShell:

```powershell
cd C:\jana_address
.\venv\Scripts\Activate.ps1

cd .\backend
alembic upgrade head
uvicorn app.main:app --reload
```

### 2. Frontend

Во втором терминале PowerShell:

```powershell
cd C:\jana_address\frontend
npm ci
npm run dev
```

После запуска:

- интерфейс: `http://localhost:5173`;
- Swagger: `http://localhost:8000/docs`;
- проверка сервера: `http://localhost:8000/api/v1/health`;
- основной batch-метод: `POST http://localhost:8000/api/v1/parse/batch`.

Полная smoke-проверка backend и справочника:

```powershell
cd C:\jana_address
.\scripts\smoke_test.ps1
```

## Главный запрос для жюри

Тело запроса — обычный JSON-массив. Одна входная запись всегда даёт одну
выходную запись в той же позиции.

```json
[
  {
    "id": "rec_00417",
    "raw_address": "город Алматы/Алматы қаласы, Мкр Аксай 3а, 59, кв 70"
  },
  {
    "id": "rec_00418",
    "raw_address": "66квартал 12дом 69квартира"
  }
]
```

Ответ `200 OK`:

```json
[
  {
    "record_id": "55ea3f16-3a71-4d10-9d8d-4ed9f3eb85b6",
    "id": "rec_00417",
    "raw_address": "город Алматы/Алматы қаласы, Мкр Аксай 3а, 59, кв 70",
    "province": "Алматы",
    "city": "Алматы",
    "district": "Әуезов ауданы",
    "living_area": "Аксай 3А",
    "street_type": "микрорайон",
    "street_name": "Аксай 3а",
    "house": "59",
    "apartment": "70",
    "entrance": null,
    "floor": null,
    "landmark": null,
    "confidence": 0.92,
    "needs_review": false
  },
  {
    "id": "rec_00418",
    "record_id": "9aa17bf7-3b58-45a6-ac49-f19db1a2cc6b",
    "raw_address": "66квартал 12дом 69квартира",
    "province": "Атырау облысы",
    "city": "Құлсары",
    "district": "Жылыой ауданы",
    "living_area": null,
    "street_type": "квартал",
    "street_name": "66",
    "house": "12",
    "apartment": "69",
    "entrance": null,
    "floor": null,
    "landmark": null,
    "confidence": 0.9,
    "needs_review": false
  }
]
```

## API для frontend

- `POST /api/v1/parse` — разобрать один объект `{id, raw_address}`;
- `POST /api/v1/parse/batch` — разобрать JSON-массив;
- `POST /api/v1/parse/file` — загрузить UTF-8 файл `.json` или `.csv`;
- `GET /api/v1/records` — загрузить сохранённые результаты из PostgreSQL;
- `PATCH /api/v1/records/{record_id}` — сохранить ручное исправление;
- `GET /api/v1/health` — проверить backend и PostgreSQL.

CSV должен иметь две колонки:

```csv
id,raw_address
rec_1,"Ул .Курильская 9 кв 1"
```

Каждый результат сохраняется в таблицу `address_records`. Поэтому после
обновления страницы frontend снова загружает историю, а ручные исправления не
теряются. Поле `record_id` — UUID записи PostgreSQL, а `needs_review` — готовый
признак для интерфейса.

Frontend показывает записи с `needs_review: true` как требующие уточнения. Для
нераспознанной строки backend возвращает исходные `id`,
`raw_address`, `null` в неизвестных полях и низкую уверенность — запись не
исчезает из результата.

Подробный контракт: [`docs/api-contract.md`](docs/api-contract.md).

Готовый текст для презентации: [`docs/presentation-summary.md`](docs/presentation-summary.md).

## Подготовка нового ноутбука

PostgreSQL должен быть запущен, а `DATABASE_URL` указан в `.env`.

```powershell
cd C:\jana_address
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\backend\requirements-dev.txt

Copy-Item .\.env.example .\.env
# Укажите в .env пароль локального PostgreSQL.

.\venv\Scripts\python.exe .\scripts\validate_reference.py .\data\reference
# Затем импортируйте справочник командой из раздела ниже.

cd .\backend
alembic upgrade head
uvicorn app.main:app --reload
```

В отдельном терминале установите зависимости и запустите frontend:

```powershell
cd C:\jana_address\frontend
npm ci
npm run dev
```

Локальный `.env` содержит пароль и не коммитится. Для синхронизации между
ноутбуками используются GitHub, `.env.example`, `requirements*.txt` и
`package-lock.json`.

## Таблица адресного справочника

`address_references` хранит иерархию в одной таблице:

- `kind` — `province`, `city`, `district`, `living_area` или `street`;
- `name` и `normalized_name` — исходное и нормализованное название;
- `parent_id` — родительская запись, например город для улицы;
- `code` — внешний код источника;
- `attributes` — дополнительные данные в JSON;
- `enabled` — активна ли запись.

Загрузчик JSON/CSV: `scripts/build_reference.py`.

### Справочник Казахстана из архива

Готовый справочник из OpenStreetMap расположен в `data/reference` и загружается
в отдельную схему PostgreSQL `jana_reference`. Он не заменяет таблицу
`address_references` и не удаляет данные приложения.

В схеме создаются таблицы: `regions`, `districts`, `settlements`, `places`,
`streets`, `living_areas`, `admin_areas` и `aliases`.

Проверка файлов и импорт выполняются из PowerShell в корне проекта:

```powershell
.\venv\Scripts\python.exe .\scripts\validate_reference.py .\data\reference

$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/jana_address_db"
.\venv\Scripts\python.exe .\scripts\import_to_postgres.py --data-dir .\data\reference
Remove-Item Env:DATABASE_URL
```

Не добавляйте `--replace` без необходимости: этот параметр очищает восемь
таблиц схемы `jana_reference` перед повторной загрузкой. Полная инструкция к
набору находится в [`docs/reference-bundle-README.md`](docs/reference-bundle-README.md).
Источник данных — OpenStreetMap; это не официальный справочник КАТО, поэтому при
публикации данных необходимо сохранить атрибуцию OpenStreetMap.

## Тесты

```powershell
cd C:\jana_address\backend
..\venv\Scripts\python.exe -m pytest -q
```
