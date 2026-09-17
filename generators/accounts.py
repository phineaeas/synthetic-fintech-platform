"""
Генерация синтетических исходных данных для raw.accounts, связанных с raw.customers.
 
- Читает data/raw_source/customers.jsonl (должен быть сгенерирован заранее),
  чтобы собрать пул валидных значений customer_id. "связность данных" достигается
  через файл на диске, а не через разделяемые переменные в памяти
  accounts.py можно перезапустить отдельно, пока customers.jsonl уже
  существует.
- Детерминизм рализован через тот же паттерн GENERATION_REFERENCE_DATE / seed, что в
  customers.py. 
- Искажение "невалидный FK" использует отдельный пул id, которые заведомо
  никогда не встретятся в customers.jsonl (CUST9xxxx, за пределами
  реального диапазона CUST00001-CUST05000), а не порчу уже существующего
  валидного id. Так "битый FK" и "NULL" остаются двумя разными,
  однозначно различимыми проблемами качества данных для последующего
  dbt-теста relationships.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

# --- Configuration -----------------------------------------------------

SEED = 43  # отличается от seed в customers.py, чтобы два генератора не
           # выдавали коррелирующие "случайные" значения
NUM_ACCOUNTS = 7_500
BAD_DATA_RATE = 0.03

GENERATION_REFERENCE_DATE = datetime(2026, 1, 1)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_source"
CUSTOMERS_PATH = DATA_DIR / "customers.jsonl"
OUTPUT_PATH = DATA_DIR / "accounts.jsonl"

ACCOUNT_TYPES = ["checking", "savings", "credit"]
CURRENCIES = ["EUR", "USD", "GBP", "PLN"]
STATUSES = ["active", "closed", "suspended"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generators.accounts")


def load_valid_customer_ids(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run generators/customers.py first - "
            "accounts.py depends on its output to link accounts to customers."
        )

    ids: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            customer_id = record.get("customer_id")
            if customer_id:  # пропускаем None/пустые, это намеренно битые строки
                ids.add(customer_id)

    logger.info("loaded %d distinct valid customer_id values from %s", len(ids), path)
    return sorted(ids)


def _build_clean_record(account_id: str, valid_customer_ids: list[str]) -> dict:
    status = random.choice(STATUSES)
    opened_at = GENERATION_REFERENCE_DATE - timedelta(days=random.randint(1, 5 * 365))

    closed_at = None
    if status == "closed":
        closed_at = opened_at + timedelta(days=random.randint(1, 3 * 365))
        if closed_at > GENERATION_REFERENCE_DATE:
            closed_at = GENERATION_REFERENCE_DATE

    return {
        "account_id": account_id,
        "customer_id": random.choice(valid_customer_ids),
        "account_type": random.choice(ACCOUNT_TYPES),
        "currency": random.choice(CURRENCIES),
        "opened_at": opened_at.isoformat(),
        "closed_at": closed_at.isoformat() if closed_at else None,
        "status": status,
    }


def _corrupt_record(record: dict, stats: dict) -> dict:
    record = dict(record)

    if random.random() < BAD_DATA_RATE:
        record["account_id"] = None
        stats["null_account_id"] += 1

    if random.random() < BAD_DATA_RATE:
        # Битый FK: строка в формате account_id, но за пределами реального
        # диапазона клиентов гарантированно никогда не совпадёт со
        # строкой в raw.customers.
        fake_customer_id = f"CUST9{random.randint(0, 9999):04d}"
        record["customer_id"] = fake_customer_id
        stats["invalid_customer_fk"] += 1

    if random.random() < BAD_DATA_RATE:
        record["currency"] = record["currency"].lower()
        stats["inconsistent_currency_case"] += 1

    if random.random() < BAD_DATA_RATE:
        record["status"] = record["status"].upper()
        stats["inconsistent_status_case"] += 1

    if random.random() < BAD_DATA_RATE:
        future_dt = GENERATION_REFERENCE_DATE + timedelta(days=random.randint(1, 365))
        record["opened_at"] = future_dt.isoformat()
        stats["future_opened_at"] += 1

    return record


def generate_accounts(valid_customer_ids: list[str]) -> list[dict]:
    random.seed(SEED)

    stats = {
        "null_account_id": 0,
        "invalid_customer_fk": 0,
        "inconsistent_currency_case": 0,
        "inconsistent_status_case": 0,
        "future_opened_at": 0,
        "duplicated_rows": 0,
    }

    records: list[dict] = []

    for i in range(1, NUM_ACCOUNTS + 1):
        account_id = f"ACC{i:06d}"
        clean = _build_clean_record(account_id, valid_customer_ids)
        dirty = _corrupt_record(clean, stats)
        records.append(dirty)

        if random.random() < BAD_DATA_RATE:
            records.append(dict(dirty))
            stats["duplicated_rows"] += 1

    logger.info("records generated: %d (base target: %d)", len(records), NUM_ACCOUNTS)
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
    logger.info("generation started: accounts")
    valid_customer_ids = load_valid_customer_ids(CUSTOMERS_PATH)
    records = generate_accounts(valid_customer_ids)
    write_jsonl(records, OUTPUT_PATH)
    logger.info("generation finished: accounts")


if __name__ == "__main__":
    main()
