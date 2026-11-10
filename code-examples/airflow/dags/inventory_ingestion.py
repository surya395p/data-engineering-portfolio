"""Example Airflow DAG: synthetic inventory JSON -> validation -> SQLite upsert."""

from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

from inventory_pipeline import read_inventory, upsert_inventory, validate_inventory

LOGGER = logging.getLogger(__name__)
EXAMPLE_ROOT = Path(__file__).resolve().parents[1]


def extract_inventory(**_context):
    input_path = Path(os.environ.get("INVENTORY_INPUT_PATH", EXAMPLE_ROOT / "sample_data" / "inventory.json"))
    records = read_inventory(input_path)
    LOGGER.info("Extraction complete: source=%s records=%d", input_path.name, len(records))
    return records


def validate_inventory_task(ti):
    records = ti.xcom_pull(task_ids="extract_inventory")
    validated = validate_inventory(records)
    LOGGER.info("Validation complete: accepted=%d", len(validated))
    return validated


def load_inventory_task(ti):
    records = ti.xcom_pull(task_ids="validate_inventory")
    database_path = Path(os.environ.get("INVENTORY_DB_PATH", EXAMPLE_ROOT / "data" / "inventory.db"))
    changed = upsert_inventory(records, database_path)
    LOGGER.info("Load complete: input=%d changed=%d target=%s", len(records), changed, database_path.name)
    return {"input_records": len(records), "rows_changed": changed}


with DAG(
    dag_id="synthetic_inventory_ingestion",
    description="Validate and idempotently load synthetic inventory records",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"owner": "portfolio", "retries": 2, "retry_delay": timedelta(minutes=3)},
    max_active_runs=1,
    tags=["portfolio", "inventory", "synthetic-data"],
) as dag:
    extract = PythonOperator(task_id="extract_inventory", python_callable=extract_inventory)
    validate = PythonOperator(task_id="validate_inventory", python_callable=validate_inventory_task)
    load = PythonOperator(task_id="load_inventory", python_callable=load_inventory_task)

    extract >> validate >> load
