"""
Генерация синтетических исходных данных для raw.customers
 
- Детерминизм реализован через фиксированный random seed, чтобы повторный запуск давал
  побайтово идентичный результат. Загрузчик делает TRUNCATE + INSERT в raw.customers на
  каждом прогоне пайплайна, поэтому сгенерированные данные не должны
  плавать между запусками
- ~BAD_DATA_RATE записей получают одну или несколько намеренных проблем
  качества данных (NULL id, дубликат строки, разнобой регистра, дата в
  будущем). Это НЕ помечается в самом выводе и реальный источник данных
  тоже не подскажет, какие записи плохие. Пометка есть только в
  консольной сводке, для нашего собственного контроля при разработке.
- Вывод в формате JSONL (один JSON-объект на строку), пишется в
  data/raw_source/customers.jsonl
"""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

# --- Configuration -----------------------------------------------------

SEED = 42
NUM_CUSTOMERS = 5_000
BAD_DATA_RATE = 0.03

# Фиксированная точка отсчёта для всей генерации дат "относительно сейчас".
# Использование реального времени здесь сломало бы детерминизм: один и тот
# же seed всё ещё даёт одну и ту же *последовательность* случайных чисел,
# но если верхняя граница диапазона дат (например "сейчас") отличается
# между двумя запусками, разнесёнными во времени хотя бы на секунды —
# итоговые даты тоже отличаются. Фиксированная точка отсчёта убирает этот
# источник "дрейфа".
GENERATION_REFERENCE_DATE = datetime(2026, 1, 1)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_source" / "customers.jsonl"

# Небольшие фиксированные пулы, чтобы marts ниже по пайплайну могли
# осмысленно группировать данные 
COUNTRIES_AND_CITIES = {
    "Germany": ["Berlin", "Munich", "Hamburg", "Cologne"],
    "France": ["Paris", "Lyon", "Marseille", "Toulouse"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville"],
    "Italy": ["Rome", "Milan", "Naples", "Turin"],
    "Netherlands": ["Amsterdam", "Rotterdam", "Utrecht", "The Hague"],
    "Poland": ["Warsaw", "Krakow", "Gdansk", "Wroclaw"],
}

SEGMENTS = ["retail", "premium", "business"]
STATUSES = ["active", "inactive", "closed"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generators.customers")


def _build_clean_record(customer_id: str, fake: Faker) -> dict:
    country = random.choice(list(COUNTRIES_AND_CITIES.keys()))
    city = random.choice(COUNTRIES_AND_CITIES[country])

    return {
        "customer_id": customer_id,
        "created_at": fake.date_time_between(
            start_date=GENERATION_REFERENCE_DATE - timedelta(days=3 * 365),
            end_date=GENERATION_REFERENCE_DATE,
        ).isoformat(),
        "birth_date": fake.date_between_dates(
            date_start=(GENERATION_REFERENCE_DATE - timedelta(days=90 * 365)).date(),
            date_end=(GENERATION_REFERENCE_DATE - timedelta(days=18 * 365)).date(),
        ).isoformat(),
        "country": country,
        "city": city,
        "segment": random.choice(SEGMENTS),
        "status": random.choice(STATUSES),
    }


def _corrupt_record(record: dict, stats: dict) -> dict:
    """Применяет независимые случайные искажения к копии записи.
 
    Каждый тип искажения проверяется независимым броском вероятности
    BAD_DATA_RATE, поэтому одна запись может получить ноль, одно или
    (редко) сразу несколько искажений.
    """
    record = dict(record)  # не мутируем словарь вызывающего кода

    if random.random() < BAD_DATA_RATE:
        record["customer_id"] = None
        stats["null_customer_id"] += 1

    if random.random() < BAD_DATA_RATE:
        record["status"] = record["status"].upper()
        stats["inconsistent_status_case"] += 1

    if random.random() < BAD_DATA_RATE:
        record["country"] = record["country"].lower()
        record["city"] = record["city"].lower()
        stats["inconsistent_geo_case"] += 1

    if random.random() < BAD_DATA_RATE:
        future_dt = GENERATION_REFERENCE_DATE + timedelta(days=random.randint(1, 365))
        record["created_at"] = future_dt.isoformat()
        stats["future_created_at"] += 1

    return record


def generate_customers() -> list[dict]:
    Faker.seed(SEED)
    random.seed(SEED)
    fake = Faker()

    stats = {
        "null_customer_id": 0,
        "inconsistent_status_case": 0,
        "inconsistent_geo_case": 0,
        "future_created_at": 0,
        "duplicated_rows": 0,
    }

    records: list[dict] = []

    for i in range(1, NUM_CUSTOMERS + 1):
        customer_id = f"CUST{i:05d}"
        clean = _build_clean_record(customer_id, fake)
        dirty = _corrupt_record(clean, stats)
        records.append(dirty)

        # Дублирование: добавляем ту же (уже испорченную) строку ещё раз,
        # независимо от остальных бросков искажений выше.
        if random.random() < BAD_DATA_RATE:
            records.append(dict(dirty))
            stats["duplicated_rows"] += 1

    logger.info("records generated: %d (base target: %d)", len(records), NUM_CUSTOMERS)
    for issue, count in stats.items():
        logger.info("  %s: %d", issue, count)

    return records


def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")
    logger.info("wrote %d lines to %s", len(records), path)


def main() -> None:
    logger.info("generation started: customers")
    records = generate_customers()
    write_jsonl(records, OUTPUT_PATH)
    logger.info("generation finished: customers")


if __name__ == "__main__":
    main()
