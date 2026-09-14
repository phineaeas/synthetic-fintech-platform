"""
Load data/raw_source/transactions.jsonl into raw.transactions (full refresh).

Largest of the four loaders (~103k rows) - this is where execute_values
batch insert (see common.py) actually matters for performance; a row-by-row
INSERT loop here would be noticeably slower.
"""

import logging
from pathlib import Path

from common import full_refresh_load, read_jsonl_tolerant
from db import get_connection

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_source" / "transactions.jsonl"

COLUMNS = [
    "transaction_id",
    "account_id",
    "merchant_id",
    "transaction_ts",
    "amount",
    "currency",
    "transaction_type",
    "status",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("loaders.transactions")


def main() -> None:
    logger.info("load started: transactions")

    records, invalid_count = read_jsonl_tolerant(DATA_PATH)
    logger.info("read %d valid records, %d invalid lines from %s", len(records), invalid_count, DATA_PATH)

    conn = get_connection()
    try:
        loaded_count = full_refresh_load(conn, "raw", "transactions", COLUMNS, records)
        logger.info("records loaded: %d", loaded_count)
    except Exception:
        logger.exception("load failed, transaction rolled back")
        raise
    finally:
        conn.close()

    logger.info("load finished: transactions")


if __name__ == "__main__":
    main()
