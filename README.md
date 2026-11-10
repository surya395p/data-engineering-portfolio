# Data Engineering Portfolio

**Data Engineer | Python · SQL · Apache Airflow · Google Cloud · BigQuery · PostgreSQL**

A collection of production-inspired data engineering workflow descriptions and independently written examples, focused on reliable batch ingestion, orchestration, data quality, and operational support.

> **Confidentiality:** These project descriptions are generalized summaries of documented workflow patterns. No employer-owned source code, credentials, customer records, internal URLs, or infrastructure identifiers are published. Code examples use synthetic data and are standalone demonstrations, not copies of production systems.

## Projects

| Project | Pattern | Key engineering topics |
|---|---|---|
| [Email-based inventory pipeline](projects/01-email-inventory-pipeline/README.md) | Email attachment → object storage → Airflow → relational database | OAuth mailbox access, file parsing, validation, deduplication, upsert |
| [SOAP/XML API pipeline](projects/02-soap-api-inventory-pipeline/README.md) | SOAP API → object storage → staging → current data | XML parsing, staging/promote, validation, monitoring |
| [Paginated API pipeline](projects/03-paginated-api-inventory-pipeline/README.md) | OAuth API → paginated extraction → object storage → database | Pagination, checkpoints, restartability, upsert |

## Engineering practices

- **Idempotency:** safe reprocessing through stable business keys and deterministic upserts.
- **Data quality:** required-field, schema, duplicate-key, record-count, and range checks.
- **Recoverability:** bounded retries and durable checkpoints for resumable extraction.
- **Observability:** run status, source/target counts, duration, and actionable failure context.
- **Security:** environment-specific configuration and managed secret storage.
- **Delivery:** version control and automated validation/deployment workflows.

## Repository structure

```text
.
├── README.md
├── skills/technical-skills.md
├── projects/
│   ├── 01-email-inventory-pipeline/
│   ├── 02-soap-api-inventory-pipeline/
│   └── 03-paginated-api-inventory-pipeline/
└── code-examples/
    ├── airflow/README.md
    ├── python/validation.py
    └── sql/inventory_upsert.sql
```

## Technology areas

Python, SQL, Apache Airflow, Google Cloud Storage, BigQuery, PostgreSQL, REST/SOAP APIs, OAuth 2.0, XML/CSV/delimited files, data quality, orchestration, CI/CD, logging, and alerting.

Start with the project pages for architecture and workflow context, then review the independent [Python validation example](code-examples/python/validation.py) and [SQL upsert example](code-examples/sql/inventory_upsert.sql).

*Portfolio documentation and demonstration code. Sample data is synthetic.*
