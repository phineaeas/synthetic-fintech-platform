-- Superset's own metadata (dashboards, charts, saved queries, users) lives
-- in a separate DATABASE from the warehouse - same reasoning as
-- postgres/init/03_airflow_db.sql for Airflow.
CREATE DATABASE superset;
