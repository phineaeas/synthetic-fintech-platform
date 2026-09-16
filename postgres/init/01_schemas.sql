-- Схемы по слоям DWH.
-- Схемы staging/core/mart фактически будут пересоздаваться dbt на
-- соответствующих этапах, но мы создаём их здесь заранее, чтобы база
-- была "самоописывающейся" сразу после первого `docker compose up`.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;
