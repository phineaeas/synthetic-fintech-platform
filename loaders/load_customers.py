"""
Загружает data/raw_source/customers.jsonl в raw.customers (full refresh)
"""

import logging
from pathlib import Path

from common import full_refresh_load, read_jsonl_tolerant
from db import get_connection

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_source" / "customers.jsonl"

# Порядок колонок здесь должен совпадать с порядком колонок в INSERT - но
# не обязан совпадать с порядком ключей в JSONL (словари ищутся по ключу,
# а не по позиции)
COLUMNS = ["customer_id", "created_at", "birth_date", "country", "city", "segment", "status"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("loaders.customers")


def main() -> None:
    logger.info("load started: customers")

    records, invalid_count = read_jsonl_tolerant(DATA_PATH)
    logger.info("read %d valid records, %d invalid lines from %s", len(records), invalid_count, DATA_PATH)

    conn = get_connection()
    try:
        loaded_count = full_refresh_load(conn, "raw", "customers", COLUMNS, records)
        logger.info("records loaded: %d", loaded_count)
    except Exception:
        logger.exception("load failed, transaction rolled back")
        raise
    finally:
        conn.close()

    logger.info("load finished: customers")


if __name__ == "__main__":
    main()
