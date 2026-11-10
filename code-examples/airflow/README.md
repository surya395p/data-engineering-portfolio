# Airflow Example Notes

The project descriptions document Airflow orchestration patterns, including object-arrival/dataset-triggered workflows, task dependencies, retries, and operational visibility.

This folder is reserved for small, independently written DAG demonstrations. No employer DAGs or production configuration are included.

## Suggested DAG design
- Keep extraction/landing separate from downstream transformation.
- Make task boundaries explicit: parse → validate → load/promote.
- Set bounded retries and retry delays for transient failures.
- Keep credentials and environment configuration outside DAG source.
- Emit useful run metadata: source object, counts, duration, and status.
- Ensure downstream writes are idempotent so retries and manual re-runs are safe.

The project pages describe documented workflow behavior; this note lists portfolio design guidance.
