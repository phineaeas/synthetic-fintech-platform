"""
Общий помощник для подключения к PostgreSQL, используется всеми загрузчиками.
 
Загрузчики запускаются на хосте (conda-окружение в WSL), а не внутри
Docker-сети, поэтому подключаемся через порт, который docker-compose
публикует на localhost, а не по имени сервиса `postgres` (оно резолвится
только внутри сети compose).
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Явно загружаем .env файл проекта. load_dotenv() по умолчанию ищет файл в
# текущей директории и родительских, но явное указание пути гарантирует,
# что загрузчики работают корректно независимо от того, из какой папки их
# запустили.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )
