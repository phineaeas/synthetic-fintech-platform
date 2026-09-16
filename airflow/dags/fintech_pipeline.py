"""
fintech_pipeline: generate_raw -> load_raw -> dbt_run -> dbt_test
(spec section 18).

Operator choice follows spec section 19: generation tasks use the
TaskFlow API (@task) since they're our own Python logic; loaders and dbt
commands use BashOperator, since from Airflow's perspective they're
"existing scripts / CLI commands" to invoke, not logic to embed.

PROJECT_DIR is a fixed container path (see docker-compose.yml: the whole
project is bind-mounted to /opt/project) - this DAG only ever runs inside
the airflow container, so there's no host-path configurability to handle.

Task dependency shape is NOT a single straight line - it mirrors the real
data dependencies between generators (see generators/*.py docstrings):
  - generate_accounts reads customers.jsonl -> depends on generate_customers
  - generate_transactions reads accounts.jsonl AND merchants.jsonl ->
    depends on BOTH generate_accounts and generate_merchants
  - each load_* only depends on its own generate_* step finishing
  - dbt_run waits for ALL four loads (it reads from all four RAW tables)
"""

import subprocess
import sys
from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/project"


def _run_generator(script_name: str) -> None:
    subprocess.run(
        [sys.executable, f"{PROJECT_DIR}/generators/{script_name}"],
        check=True,
        cwd=PROJECT_DIR,
    )


@dag(
    dag_id="fintech_pipeline",
    description="generate_raw -> load_raw -> dbt_run -> dbt_test",
    schedule=None,  # manual trigger only for MVP (spec section 18)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["fintech", "mvp"],
)
def fintech_pipeline():

    @task
    def generate_customers():
        _run_generator("customers.py")

    @task
    def generate_accounts():
        _run_generator("accounts.py")

    @task
    def generate_merchants():
        _run_generator("merchants.py")

    @task
    def generate_transactions():
        _run_generator("transactions.py")

    load_customers = BashOperator(
        task_id="load_customers",
        bash_command=f"cd {PROJECT_DIR} && python loaders/load_customers.py",
    )
    load_accounts = BashOperator(
        task_id="load_accounts",
        bash_command=f"cd {PROJECT_DIR} && python loaders/load_accounts.py",
    )
    load_merchants = BashOperator(
        task_id="load_merchants",
        bash_command=f"cd {PROJECT_DIR} && python loaders/load_merchants.py",
    )
    load_transactions = BashOperator(
        task_id="load_transactions",
        bash_command=f"cd {PROJECT_DIR} && python loaders/load_transactions.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt run",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt test",
    )

    gen_customers = generate_customers()
    gen_accounts = generate_accounts()
    gen_merchants = generate_merchants()
    gen_transactions = generate_transactions()

    gen_customers >> [gen_accounts, load_customers]
    gen_accounts >> [load_accounts, gen_transactions]
    gen_merchants >> [load_merchants, gen_transactions]
    gen_transactions >> load_transactions

    [load_customers, load_accounts, load_merchants, load_transactions] >> dbt_run >> dbt_test


fintech_pipeline()
