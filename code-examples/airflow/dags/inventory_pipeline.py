"""Pure-Python inventory pipeline helpers used by the Airflow demo DAG."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

LOGGER = logging.getLogger(__name__)
REQUIRED_FIELDS = ("sku", "location_id", "quantity", "source_updated_at")


def read_inventory(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSON array of synthetic inventory records."""
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        records = json.load(handle)
    if not isinstance(records, list):
        raise ValueError("Inventory input must be a JSON array")
    LOGGER.info("Read %d records from %s", len(records), source.name)
    return records


def validate_inventory(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate required fields, quantities, unique keys, and timestamps."""
    valid: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    errors: list[str] = []

    for row_number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            errors.append(f"row {row_number}: record must be an object")
            continue

        missing = [field for field in REQUIRED_FIELDS if record.get(field) in (None, "")]
        if missing:
            errors.append(f"row {row_number}: missing required fields {missing}")
            continue

        quantity = record["quantity"]
        if isinstance(quantity, bool):
            errors.append(f"row {row_number}: quantity must be a non-negative integer")
            continue
        try:
            parsed_quantity = int(quantity)
        except (TypeError, ValueError):
            errors.append(f"row {row_number}: quantity must be a non-negative integer")
            continue
        if str(parsed_quantity) != str(quantity) or parsed_quantity < 0:
            errors.append(f"row {row_number}: quantity must be a non-negative integer")
            continue

        key = (str(record["sku"]).strip(), str(record["location_id"]).strip())
        if not all(key):
            errors.append(f"row {row_number}: sku and location_id cannot be blank")
            continue
        if key in seen:
            errors.append(f"row {row_number}: duplicate business key {key}")
            continue
        seen.add(key)

        try:
            updated_at = datetime.fromisoformat(str(record["source_updated_at"]).replace("Z", "+00:00"))
            if updated_at.tzinfo is None:
                raise ValueError("timestamp must include a timezone")
            normalized_updated_at = updated_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            errors.append(f"row {row_number}: source_updated_at must be a timezone-aware ISO-8601 timestamp")
            continue

        valid.append({
            "sku": key[0],
            "location_id": key[1],
            "quantity": parsed_quantity,
            "source_updated_at": normalized_updated_at,
        })

    if errors:
        raise ValueError("Inventory validation failed: " + "; ".join(errors))

    LOGGER.info("Validated %d inventory records", len(valid))
    return valid


def upsert_inventory(records: Iterable[dict[str, Any]], database_path: str | Path) -> int:
    """Idempotently upsert inventory by (sku, location_id) into SQLite."""
    target = Path(database_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = list(records)

    with sqlite3.connect(target) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS inventory_current (
                sku TEXT NOT NULL,
                location_id TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                source_updated_at TEXT NOT NULL,
                PRIMARY KEY (sku, location_id)
            )"""
        )
        before = connection.total_changes
        connection.executemany(
            """INSERT INTO inventory_current
                   (sku, location_id, quantity, source_updated_at)
               VALUES (:sku, :location_id, :quantity, :source_updated_at)
               ON CONFLICT (sku, location_id) DO UPDATE SET
                   quantity = excluded.quantity,
                   source_updated_at = excluded.source_updated_at
               WHERE excluded.source_updated_at > inventory_current.source_updated_at
                  OR (excluded.source_updated_at = inventory_current.source_updated_at
                      AND excluded.quantity != inventory_current.quantity)""",
            rows,
        )
        changed = connection.total_changes - before

    LOGGER.info("Applied %d input records; %d rows inserted or updated", len(rows), changed)
    return changed
