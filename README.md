# Synthetic Fintech Platform

Batch data platform for processing synthetic fintech data.

## Architecture

```text
Python Generators
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

Airflow orchestrates the pipeline.
```

## Data Domain

- Customer
- Account
- Merchant
- Transaction

## Project Structure

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

## Requirements

- Windows + WSL2 / Linux
- Docker Desktop
- Docker Compose
- Git

## Run

Clone repository:

```bash
git clone https://github.com/phineaeas/synthetic-fintech-platform.git
cd synthetic-fintech-platform
```

Start services:

```bash
docker compose up -d
```

Check containers:

```bash
docker compose ps
```

## Pipeline

```text
generate
   ↓
load_raw
   ↓
dbt run
   ↓
dbt test
```

Pipeline запускается и оркестрируется через Airflow.

## Services

| Service | Purpose |
|---|---|
| PostgreSQL | хранение данных |
| Airflow | оркестрация |
| dbt | трансформации |
| Superset | визуализация |

## Stop

```bash
docker compose down
```
