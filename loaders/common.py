"""
Shared utilities for loaders/load_*.py scripts.

Implements the two pieces of logic every loader needs, per spec sections
20-23:
- read source JSONL tolerantly: a malformed line is logged and skipped,
  it must not abort the whole batch.
- load into RAW using the full-refresh idempotency strategy: TRUNCATE the
  target table, then batch-insert everything in one transaction. This
  guarantees re-running a loader never duplicates rows, since generators
  are deterministic (same input file -> same rows every time).
"""

import json
import logging
from pathlib import Path

from psycopg2.extras import execute_values

logger = logging.getLogger("loaders.common")


def read_jsonl_tolerant(path: Path) -> tuple[list[dict], int]:
    """Read a JSONL file, returning (valid_records, invalid_line_count).

    A line that isn't valid JSON is logged and skipped rather than raising -
    per spec section 23, a small number of bad source records should not
    abort the complete batch. Note this is about malformed JSON *syntax*;
    the intentionally "dirty" values our generators produce (NULLs, bad
    casing, wrong types, orphan FKs) are all still valid JSON and pass
    through here untouched - they're RAW's job to hold as-is, not this
    function's job to filter.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run the matching generator first.")

    records: list[dict] = []
    invalid_count = 0

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("invalid JSON at %s:%d - %s", path.name, line_number, e)
                invalid_count += 1

    return records, invalid_count


def full_refresh_load(conn, schema: str, table: str, columns: list[str], records: list[dict]) -> int:
    """TRUNCATE schema.table, then batch-insert `records` in one transaction.

    `columns` defines both the column order for the INSERT and which keys
    are read from each record dict (via .get(), so a missing key becomes
    NULL rather than raising).

    Returns the number of rows inserted. Raises and rolls back on error -
    a failed load should not leave the table half-truncated/half-loaded.
    """
    rows = [tuple(record.get(col) for col in columns) for record in records]

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {schema}.{table}")
        if rows:
            columns_sql = ", ".join(columns)
            execute_values(
                cur,
                f"INSERT INTO {schema}.{table} ({columns_sql}) VALUES %s",
                rows,
            )
    conn.commit()

    return len(rows)
