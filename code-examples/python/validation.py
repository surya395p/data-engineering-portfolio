"""Dependency-free data quality example using synthetic inventory rows."""
from collections import Counter
from typing import Any

REQUIRED_FIELDS = ("sku", "location_id", "quantity")


def validate_inventory(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: Counter[tuple[str, str]] = Counter()

    for row_number, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_FIELDS if row.get(field) in (None, "")]
        if missing:
            errors.append(f"row {row_number}: missing required fields {missing}")
            continue

        try:
            quantity = int(row["quantity"])
        except (TypeError, ValueError):
            errors.append(f"row {row_number}: quantity must be an integer")
            continue

        if quantity < 0:
            errors.append(f"row {row_number}: quantity cannot be negative")

        key = (str(row["sku"]), str(row["location_id"]))
        seen[key] += 1
        if seen[key] > 1:
            errors.append(f"row {row_number}: duplicate business key {key}")

    return errors


if __name__ == "__main__":
    sample_rows = [
        {"sku": "SKU-100", "location_id": "LOC-01", "quantity": 12},
        {"sku": "SKU-200", "location_id": "LOC-01", "quantity": 0},
        {"sku": "SKU-100", "location_id": "LOC-01", "quantity": 12},
        {"sku": "SKU-300", "location_id": "LOC-02", "quantity": -1},
    ]
    for issue in validate_inventory(sample_rows):
        print(issue)
