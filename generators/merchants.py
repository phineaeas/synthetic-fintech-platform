"""
Generate synthetic raw.merchants source data.

Merchants are an independent entity (spec section 5) - no foreign keys in
or out at this layer. transactions.py will later link to merchant_id the
same way accounts.py links to customer_id: by reading merchants.jsonl.
"""

import json
import logging
import random
from pathlib import Path

from faker import Faker

# --- Configuration -----------------------------------------------------

SEED = 44  # distinct from customers.py (42) and accounts.py (43)
NUM_MERCHANTS = 1_000
BAD_DATA_RATE = 0.03

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_source"
OUTPUT_PATH = DATA_DIR / "merchants.jsonl"

# Same country pool as customers.py, for consistency across the dataset.
COUNTRIES = ["Germany", "France", "Spain", "Italy", "Netherlands", "Poland"]

CATEGORIES = [
    "grocery",
    "electronics",
    "restaurant",
    "fashion",
    "entertainment",
    "travel",
    "utilities",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generators.merchants")


def _build_clean_record(merchant_id: str, fake: Faker) -> dict:
    return {
        "merchant_id": merchant_id,
        "merchant_name": fake.company(),
        "category": random.choice(CATEGORIES),
        "country": random.choice(COUNTRIES),
    }


def _corrupt_record(record: dict, stats: dict) -> dict:
    record = dict(record)

    if random.random() < BAD_DATA_RATE:
        record["merchant_id"] = None
        stats["null_merchant_id"] += 1

    if random.random() < BAD_DATA_RATE:
        record["category"] = record["category"].upper()
        stats["inconsistent_category_case"] += 1

    return record


def generate_merchants() -> list[dict]:
    Faker.seed(SEED)
    random.seed(SEED)
    fake = Faker()

    stats = {
        "null_merchant_id": 0,
        "inconsistent_category_case": 0,
        "duplicated_rows": 0,
    }

    records: list[dict] = []

    for i in range(1, NUM_MERCHANTS + 1):
        merchant_id = f"MERCH{i:05d}"
        clean = _build_clean_record(merchant_id, fake)
        dirty = _corrupt_record(clean, stats)
        records.append(dirty)

        if random.random() < BAD_DATA_RATE:
            records.append(dict(dirty))
            stats["duplicated_rows"] += 1

    logger.info("records generated: %d (base target: %d)", len(records), NUM_MERCHANTS)
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
    logger.info("generation started: merchants")
    records = generate_merchants()
    write_jsonl(records, OUTPUT_PATH)
    logger.info("generation finished: merchants")


if __name__ == "__main__":
    main()
