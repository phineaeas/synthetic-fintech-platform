"""
Superset configuration, mounted into the official image at
/app/pythonpath/superset_config.py (Superset's documented extension point -
any .py file placed there is imported automatically at startup).

Like Airflow, Superset's own metadata (dashboards, charts, saved queries,
users) lives in a SEPARATE DATABASE from the warehouse - not the raw/
staging/core/mart schemas. Superset connects to the warehouse separately,
as a normal "database connection" configured through its own UI once it's
running (Admin -> Database Connections), not through this config file.
"""

import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@postgres:5432/superset"
)
