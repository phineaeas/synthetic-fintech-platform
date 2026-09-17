"""
Генерация синтетических исходных данных для raw.transactions, связанных
одновременно с raw.accounts и raw.merchants.
 
- Читает accounts.jsonl и merchants.jsonl для пулов валидных FK, тот же
  паттерн, что в accounts.py при чтении customers.jsonl.
- Два новых вида искажений сверх того, что использовали предыдущие
  генераторы:
    * отрицательная сумма (amount * -1)
    * неверный тип (amount записан строкой вместо числа, это можно
      сделать только потому, что мы сами напрямую управляем сериализацией
      в JSON; это намеренно ломает предположение "amount - число",
      которое staging должен будет привести/проверить явным CAST)
- currency здесь выбирается независимо от валюты самого счёта. В реальной
  системе валюта транзакции обычно совпадала бы с валютой счёта (или
  проверялась бы на совпадение) 
"""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

# --- Configuration -----------------------------------------------------

SEED = 45  # отличается от customers.py (42), accounts.py (43), merchants.py (44)
NUM_TRANSACTIONS = 100_000
BAD_DATA_RATE = 0.03

GENERATION_REFERENCE_DATE = datetime(2026, 1, 1)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_source"
ACCOUNTS_PATH = DATA_DIR / "accounts.jsonl"
MERCHANTS_PATH = DATA_DIR / "merchants.jsonl"
OUTPUT_PATH = DATA_DIR / "transactions.jsonl"

CURRENCIES = ["EUR", "USD", "GBP", "PLN"]
TRANSACTION_TYPES = ["purchase", "refund", "transfer", "withdrawal"]
STATUSES = ["success", "failed", "pending"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generators.transactions")


def load_valid_ids(path: Path, id_field: str) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the generator for {path.stem} first - "
            "transactions.py depends on its output."
        )

    ids: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            value = record.get(id_field)
            if value:
                ids.add(value)

    logger.info("loaded %d distinct valid %s values from %s", len(ids), id_field, path)
    return sorted(ids)


def _build_clean_record(transaction_id: str, valid_account_ids: list[str], valid_merchant_ids: list[str]) -> dict:
    ts = GENERATION_REFERENCE_DATE - timedelta(
        days=random.randint(0, 2 * 365),
        seconds=random.randint(0, 86_400),
    )

    return {
        "transaction_id": transaction_id,
        "account_id": random.choice(valid_account_ids),
        "merchant_id": random.choice(valid_merchant_ids),
        "transaction_ts": ts.isoformat(),
        "amount": round(random.uniform(1, 2000), 2),
        "currency": random.choice(CURRENCIES),
        "transaction_type": random.choice(TRANSACTION_TYPES),
        "status": random.choice(STATUSES),
    }


def _corrupt_record(record: dict, stats: dict) -> dict:
    record = dict(record)

    if random.random() < BAD_DATA_RATE:
        record["transaction_id"] = None
        stats["null_transaction_id"] += 1

    if random.random() < BAD_DATA_RATE:
        record["account_id"] = f"ACC9{random.randint(0, 999999):06d}"
        stats["invalid_account_fk"] += 1

    if random.random() < BAD_DATA_RATE:
        record["merchant_id"] = f"MERCH9{random.randint(0, 99999):05d}"
        stats["invalid_merchant_fk"] += 1

    if random.random() < BAD_DATA_RATE:
        record["amount"] = -abs(record["amount"])
        stats["negative_amount"] += 1

    if random.random() < BAD_DATA_RATE:
        # Неверный тип: amount приходит строкой, а не числом. Может
        # накладываться на искажение "отрицательная сумма" выше
        # (независимые броски), как и в остальных генераторах
        record["amount"] = str(record["amount"])
        stats["wrong_type_amount"] += 1

    if random.random() < BAD_DATA_RATE:
        record["currency"] = record["currency"].lower()
        stats["inconsistent_currency_case"] += 1

    if random.random() < BAD_DATA_RATE:
        record["status"] = record["status"].upper()
        stats["inconsistent_status_case"] += 1

    return record


def generate_transactions(valid_account_ids: list[str], valid_merchant_ids: list[str]) -> list[dict]:
    random.seed(SEED)

    stats = {
        "null_transaction_id": 0,
        "invalid_account_fk": 0,
        "invalid_merchant_fk": 0,
        "negative_amount": 0,
        "wrong_type_amount": 0,
        "inconsistent_currency_case": 0,
        "inconsistent_status_case": 0,
        "duplicated_rows": 0,
    }

    records: list[dict] = []

    for i in range(1, NUM_TRANSACTIONS + 1):
        transaction_id = f"TXN{i:07d}"
        clean = _build_clean_record(transaction_id, valid_account_ids, valid_merchant_ids)
        dirty = _corrupt_record(clean, stats)
        records.append(dirty)

        if random.random() < BAD_DATA_RATE:
            records.append(dict(dirty))
            stats["duplicated_rows"] += 1

    logger.info("records generated: %d (base target: %d)", len(records), NUM_TRANSACTIONS)
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
    logger.info("generation started: transactions")
    valid_account_ids = load_valid_ids(ACCOUNTS_PATH, "account_id")
    valid_merchant_ids = load_valid_ids(MERCHANTS_PATH, "merchant_id")
    records = generate_transactions(valid_account_ids, valid_merchant_ids)
    write_jsonl(records, OUTPUT_PATH)
    logger.info("generation finished: transactions")


if __name__ == "__main__":
    main()
