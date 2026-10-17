# JANA ADDRESS

Простой backend для хакатон-кейса: получает адрес одной строкой и возвращает
поля, которые требуются в задании. Основной разбор полностью локальный — он не
зависит от внешнего геокодера и не теряет записи, которые не удалось распознать.

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
    "confidence": 0.92
  },
  {
    "id": "rec_00418",
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
    "confidence": 0.9
  }
]
```

## API для frontend

- `POST /api/v1/parse` — разобрать один объект `{id, raw_address}`;
- `POST /api/v1/parse/batch` — разобрать JSON-массив;
- `POST /api/v1/parse/file` — загрузить UTF-8 файл `.json` или `.csv`;
- `GET /api/v1/health` — проверить backend и PostgreSQL.

CSV должен иметь две колонки:

```csv
id,raw_address
rec_1,"Ул .Курильская 9 кв 1"
```

Frontend может показывать записи с низким `confidence` в таблице ручной
проверки. Для нераспознанной строки backend возвращает исходные `id`,
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
