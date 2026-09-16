-- Airflow's own operational metadata (DAG runs, task instances, connections,
-- etc.) lives in a separate DATABASE from the warehouse data, not just a
-- separate schema - orchestrator bookkeeping and analytical data shouldn't
-- share a database, even though both happen to run on the same Postgres
-- instance for this local MVP setup.
CREATE DATABASE airflow;
