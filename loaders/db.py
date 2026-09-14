"""
Shared PostgreSQL connection helper for loaders.

Loaders run on the host (WSL conda env), not inside the Docker network, so
we connect via the port docker-compose publishes to localhost - not via the
`postgres` service hostname (that only resolves inside the compose network).
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load the project's .env file explicitly. load_dotenv() searches the
# current directory and its parents by default, but being explicit here
# means loaders work correctly regardless of which directory they're
# invoked from.
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
