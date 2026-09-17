# Synthetic Fintech Platform

Учебная data-платформа: позволяет увидеть, как устроен DWH изнутри,
как данные проходят через слои RAW → STAGING → CORE → MART и как именно
dbt их трансформирует на каждом шаге. Данные синтетические (клиенты,
счета, транзакции, мерчанты), намеренно с ~3% грязных записей.

## Архитектура

```text
Python-генераторы
       ↓
     JSONL
       ↓
 PostgreSQL RAW
       ↓
     dbt
       ↓
   STAGING
       ↓
     CORE
       ↓
     MART
       ↓
   Superset

Пайплайн оркестрируется Airflow.
```

![Архитектура проекта](docs/architecture.png)

## Что здесь можно увидеть

- **Как dbt строит граф зависимостей и трансформирует данные** — раздел
  "Посмотреть, как трансформируются данные" ниже показывает, как это
  увидеть вживую: числа по слоям и граф lineage в `dbt docs`.
- **Как меняется число строк на каждом слое** — RAW хранит данные "как
  есть" (с намеренным браком), STAGING их фильтрует и чистит, поэтому
  `raw.customers` и `core.dim_customer` содержат разное количество строк —
  разница и есть отфильтрованный брак (см. команды проверки ниже).
- **Граф оркестрации в Airflow UI** (вкладка Graph) — не прямая линия, а
  параллельные ветки генерации, сходящиеся перед загрузкой транзакций.
- **Superset подключён к тем же `mart_*`-таблицам** — готовых дашбордов
  нет специально: подключитесь к базе и соберите свои графики сами (см.
  раздел "Доступ к сервисам" ниже).

## Модель данных

- Customer
- Account
- Merchant
- Transaction

![ER-диаграмма core-слоя](docs/erd.png)

## Структура проекта

```text
generators/     # генерация исходных данных
loaders/        # загрузка данных в PostgreSQL
data/           # raw JSONL
postgres/       # инициализация PostgreSQL
dbt/            # трансформации и витрины
airflow/        # DAG-и
superset/       # конфигурация Superset
tests/          # тесты
```

## Требования

- Windows + WSL2 / macOS / Linux
- Docker Desktop (Windows/macOS) или Docker Engine + Compose (Linux)
- Git

## Запуск

Клонировать репозиторий:

```bash
git clone https://github.com/phineaeas/synthetic-fintech-platform.git
cd synthetic-fintech-platform
```

Настроить окружение (создаст `.env`, поправит права на `data/` и `dbt/`):

```bash
bash scripts/setup.sh
```

Поднять сервисы:

```bash
docker compose up -d
```

Проверить контейнеры:

```bash
docker compose ps
```

## Доступ к сервисам

**Airflow** — http://localhost:8080
Логин `admin`, пароль генерируется при первом запуске:

```bash
docker compose logs airflow 2>&1 | grep -i "password for user"
```

Разморозьте DAG `fintech_pipeline` и запустите вручную.

**Superset** — http://localhost:8088
Логин: `admin` / `admin`

Дашбордов внутри нет заранее, подключитесь к базе и создавайте графики
сами, как хочется 🙂 Всё уже готово, просто добавьте подключение:

1. **Settings → Database Connections → + Database → PostgreSQL**
   - Host: `postgres`
   - Port: `5432`
   - Database name: `fintech`
   - Username: `fintech`
   - Password: `fintech_local_pw` (или то, что задали в `.env`)
2. **Datasets → + Dataset** — выберите схему **`mart`** (не `raw`, не
   `staging` — в marts данные уже агрегированы и готовы для графиков) и
   любую из таблиц: `mart_daily_transactions`, `mart_customer_activity`,
   `mart_merchant_performance`.
3. **Charts → + Chart** — стройте что угодно поверх выбранного датасета:
   линии по дням, топ клиентов, разбивку по категориям мерчантов — сами
   решаете, что интересно посмотреть.
4. Соберите несколько графиков в **Dashboards → + Dashboard** — готово,
   ваш собственный дашборд поверх DWH, который вы только что построили
   с нуля.

## Пайплайн

```text
generate
   ↓
load_raw
   ↓
dbt run
   ↓
dbt test
```

Пайплайн запускается и оркестрируется через Airflow.

## Посмотреть, как трансформируются данные

Число строк отличается по слоям, RAW хранит всё как есть, staging
фильтрует записи с NULL-ключами и битыми внешними ключами:

```bash
docker exec -it fintech_postgres psql -U fintech -d fintech -c "
SELECT 'raw.customers' AS tbl, count(*) FROM raw.customers
UNION ALL SELECT 'core.dim_customer', count(*) FROM core.dim_customer
UNION ALL SELECT 'raw.transactions', count(*) FROM raw.transactions
UNION ALL SELECT 'core.fct_transaction', count(*) FROM core.fct_transaction;
"
```

Граф зависимостей и SQL каждой модели — через встроенную документацию dbt.
Требует локально установленный dbt (`pip install dbt-core dbt-postgres`) и
переменные окружения из `.env` в текущей сессии терминала:

```bash
export $(grep -v '^#' .env | xargs)
cd dbt
export DBT_PROFILES_DIR="$(pwd)"
dbt docs generate
dbt docs serve --port 8081
```
Откроется на http://localhost:8081 (порт 8080 занят Airflow, поэтому явно указываем другой) — вкладка **Lineage Graph** показывает всю цепочку `raw → staging → core → mart` визуально, с SQL каждой модели по клику.

## Сервисы

| Сервис | Назначение |
|---|---|
| PostgreSQL | хранение данных |
| Airflow | оркестрация |
| dbt | трансформации |
| Superset | визуализация |

## Остановка

```bash
docker compose down
```
