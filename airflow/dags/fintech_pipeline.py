"""
задачи генерации используют TaskFlow API (@task), так как это наша собственная Python-
логика; загрузчики и dbt-команды используют BashOperator, так как с точки
зрения Airflow это "уже существующие скрипты / CLI-команды" для вызова, а
не логика для встраивания.
 
PROJECT_DIR - это фиксированный путь внутри контейнера (см.
docker-compose.yml: весь проект примонтирован в /opt/project) - этот DAG
выполняется только внутри airflow-контейнера, поэтому настраиваемости
пути с хоста тут не требуется.
 
Форма графа зависимостей задач НЕ прямая линия - она отражает реальные
зависимости по данным между генераторами (см. докстринги generators/*.py):
  - generate_accounts читает customers.jsonl -> зависит от generate_customers
  - generate_transactions читает accounts.jsonl И merchants.jsonl ->
    зависит СРАЗУ от generate_accounts и от generate_merchants
  - каждый load_* зависит только от завершения своего собственного generate_*
  - dbt_run ждёт завершения ВСЕХ четырёх загрузок (читает из всех четырёх RAW-таблиц)
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
    schedule=None,  # только ручной запуск
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
