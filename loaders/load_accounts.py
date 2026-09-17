"""
Загружает data/raw_source/accounts.jsonl в raw.accounts (full refresh)
"""

import logging
from pathlib import Path

from common import full_refresh_load, read_jsonl_tolerant
from db import get_connection

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_source" / "accounts.jsonl"

COLUMNS = ["account_id", "customer_id", "account_type", "currency", "opened_at", "closed_at", "status"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("loaders.accounts")


def main() -> None:
    logger.info("load started: accounts")

    records, invalid_count = read_jsonl_tolerant(DATA_PATH)
    logger.info("read %d valid records, %d invalid lines from %s", len(records), invalid_count, DATA_PATH)

    conn = get_connection()
    try:
        loaded_count = full_refresh_load(conn, "raw", "accounts", COLUMNS, records)
        logger.info("records loaded: %d", loaded_count)
    except Exception:
        logger.exception("load failed, transaction rolled back")
        raise
    finally:
        conn.close()

    logger.info("load finished: accounts")


if __name__ == "__main__":
    main()
