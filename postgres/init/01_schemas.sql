-- Schema layout per spec section 11.
-- staging/core/mart schemas will effectively be (re)managed by dbt once that
-- phase starts, but we create them here so the database is self-describing
-- from the first `docker compose up`.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;
