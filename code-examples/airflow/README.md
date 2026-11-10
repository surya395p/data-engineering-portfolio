# Runnable Airflow Inventory DAG

This is an independently written demonstration using **synthetic inventory records**. It does not connect to an external API, cloud bucket, employer system, or production database.

## Workflow

```mermaid
flowchart LR
    A[Read synthetic JSON] --> B[Validate records]
    B --> C[Idempotent SQLite upsert]
```

The DAG `synthetic_inventory_ingestion` runs daily and has three explicit tasks:

1. **extract_inventory** reads the JSON input and logs its filename and record count.
2. **validate_inventory** checks required fields, non-negative integer quantities, unique `(sku, location_id)` keys, and timezone-aware ISO-8601 timestamps. Timestamps are normalized to UTC.
3. **load_inventory** upserts into SQLite using `(sku, location_id)` as the primary key. Older source timestamps cannot overwrite newer target state.

The DAG configures two retries with a three-minute delay. The SQLite write is safe to repeat. Run metadata and row counts are written to the task logs.

## Prerequisites

- Python 3.10+
- Apache Airflow 2.4+ for DAG execution (install using the official Airflow constraints file matching your Python version and platform)
- No third-party packages are needed for the helper module or unit tests; SQLite is part of Python's standard library.

## Run the unit tests

From the repository root:

```bash
PYTHONPATH=code-examples/airflow/dags python -m unittest discover -s code-examples/airflow/tests -v
```

The tests do not import Airflow or connect to any external service. They cover valid/invalid records, duplicate keys, timestamp validation, repeated loads, and source timestamp precedence.

## Run with Airflow

After installing and initializing Airflow, point its DAG folder at this example and start the local Airflow environment:

```bash
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/code-examples/airflow/dags"
airflow standalone
```

Open the Airflow UI, enable `synthetic_inventory_ingestion`, and trigger it. The sample input is `code-examples/airflow/sample_data/inventory.json`.

Optional runtime configuration uses environment variables (no secrets are required):

```bash
export INVENTORY_INPUT_PATH="/absolute/path/to/inventory.json"
export INVENTORY_DB_PATH="/absolute/path/to/inventory.db"
```

If unset, the DAG uses the checked-in synthetic JSON file and creates a local SQLite database under `code-examples/airflow/data/`.

## Design notes and limitations

- The reusable validation and loading functions are kept separate from Airflow so they can be tested without an Airflow installation.
- XCom carries a small synthetic record set between tasks for demonstration. For large datasets, pass an object-storage URI or manifest through XCom instead of the records themselves.
- SQLite is intentionally used to keep the example local and dependency-free; it is not a recommendation for a multi-worker production Airflow deployment. Replace it with an appropriately managed database and connection/secret backend for a real workload.
- The DAG is designed for Airflow 2.4+ and has not been integration-tested against an installed Airflow scheduler in this environment.
- No credentials, internal URLs, customer data, or employer-owned code are included.
