"""
Общие утилиты для скриптов loaders/load_*.py
 
Реализует два блока логики, нужных каждому загрузчику 
- терпимое чтение исходного JSONL: битая строка логируется и пропускается,
  она не должна прерывать всю партию целиком.
- загрузка в RAW по стратегии идемпотентности full refresh: TRUNCATE
  целевой таблицы, затем пакетная вставка всего в одной транзакции. Это
  гарантирует, что повторный запуск загрузчика никогда не задваивает
  строки, так как генераторы детерминированы (один и тот же входной файл
  -> одни и те же строки при каждом запуске).
"""

import json
import logging
from pathlib import Path

from psycopg2.extras import execute_values

logger = logging.getLogger("loaders.common")


def read_jsonl_tolerant(path: Path) -> tuple[list[dict], int]:
    """Читает JSONL-файл, возвращает (valid_records, invalid_line_count).

    Строка, не являющаяся валидным JSON, логируется и пропускается, а не
    вызывает падение, небольшое число
    плохих исходных записей не должно прерывать всю партию. Речь именно
    о битом синтаксисе JSON, а не о намеренно испорченных данных
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
    """TRUNCATE schema.table, затем пакетная вставка `records` в одной транзакции.
 
    `columns` задаёт и порядок колонок в INSERT, и то, какие ключи читаются
    из каждого словаря-записи (через .get(), так что отсутствующий ключ
    превращается в NULL, а не вызывает ошибку).
 
    Возвращает число вставленных строк. При ошибке выбрасывает исключение
    и откатывает транзакцию, неудачная загрузка не должна оставлять
    таблицу в промежуточном состоянии "наполовину очищена, наполовину
    загружена"
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
