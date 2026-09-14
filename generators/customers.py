"""
Generate synthetic raw.customers source data.

Design decisions (see project README / technical spec section 9-10):
- Deterministic: fixed random seed so re-running produces byte-identical
  output. Required for the "full refresh" idempotency strategy: the loader
  will TRUNCATE + INSERT raw.customers on every pipeline run, so the
  generated data must not drift between runs.
- ~BAD_DATA_RATE of records get one or more intentional data-quality issues
  (NULL id, duplicate row, inconsistent casing, future timestamp). These are
  NOT flagged in the output - a real source system wouldn't tell you which
  records are bad. Flagging is only done in the console summary, for our
  own visibility while developing.
- Output is JSONL (one JSON object per line), written to
  data/raw_source/customers.jsonl, per spec section 9.
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

# Fixed anchor for all "relative to now" date generation. Using the real
# wall-clock time here would break determinism: the same seed still produces
# the same *sequence* of random draws, but if the date range's upper bound
# (e.g. "now") differs between two runs seconds apart, the resulting dates
# differ too. Anchoring to a fixed point removes that source of drift.
GENERATION_REFERENCE_DATE = datetime(2026, 1, 1)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_source" / "customers.jsonl"

# Fixed, small pools so downstream marts can group meaningfully
# (an unrestricted Faker country pool would give ~190 near-unique countries
# across 5000 rows, which is useless for grouping in mart_customer_activity).
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
    """Apply independent random corruptions to a copy of the record.

    Each corruption type gets its own independent BAD_DATA_RATE roll, so a
    single record can end up with zero, one, or (rarely) multiple issues -
    this mirrors how real-world dirty data tends to show up field by field,
    not record by record.
    """
    record = dict(record)  # don't mutate the caller's copy

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

        # Duplicate injection: append the exact same (already-corrupted) row
        # again, independent of the other corruption rolls above.
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
