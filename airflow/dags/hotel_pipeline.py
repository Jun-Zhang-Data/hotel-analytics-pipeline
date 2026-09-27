from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/project"
DBT_DIR = f"{PROJECT_DIR}/dbt_hotel"

default_args = {
    "owner": "data-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="hotel_analytics_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    default_args=default_args,
    tags=["hotel", "analytics"],
) as dag:
    generate_source_data = BashOperator(
        task_id="generate_source_data",
        bash_command=f"cd {PROJECT_DIR} && python scripts/generate_data.py",
    )

    ingest_raw = BashOperator(
        task_id="ingest_raw",
        bash_command=f"cd {PROJECT_DIR} && python scripts/load_raw.py",
    )

    dbt_build_prod = BashOperator(
        task_id="dbt_build_prod",
        execution_timeout=timedelta(minutes=20),
        bash_command=f"cd {DBT_DIR} && dbt build --target prod --profiles-dir {DBT_DIR}",
    )

    generate_source_data >> ingest_raw >> dbt_build_prod
