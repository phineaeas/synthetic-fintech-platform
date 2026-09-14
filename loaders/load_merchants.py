"""
Load data/raw_source/merchants.jsonl into raw.merchants (full refresh).
"""

import logging
from pathlib import Path

from common import full_refresh_load, read_jsonl_tolerant
from db import get_connection

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_source" / "merchants.jsonl"

COLUMNS = ["merchant_id", "merchant_name", "category", "country"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("loaders.merchants")


def main() -> None:
    logger.info("load started: merchants")

    records, invalid_count = read_jsonl_tolerant(DATA_PATH)
    logger.info("read %d valid records, %d invalid lines from %s", len(records), invalid_count, DATA_PATH)

    conn = get_connection()
    try:
        loaded_count = full_refresh_load(conn, "raw", "merchants", COLUMNS, records)
        logger.info("records loaded: %d", loaded_count)
    except Exception:
        logger.exception("load failed, transaction rolled back")
        raise
    finally:
        conn.close()

    logger.info("load finished: merchants")


if __name__ == "__main__":
    main()
