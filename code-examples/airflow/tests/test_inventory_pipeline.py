"""Unit tests for the dependency-free inventory pipeline helpers."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from inventory_pipeline import read_inventory, upsert_inventory, validate_inventory


class InventoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid = [{
            "sku": "SKU-1", "location_id": "LOC-1", "quantity": 5,
            "source_updated_at": "2026-11-09T10:00:00Z",
        }]

    def test_accepts_valid_records(self):
        self.assertEqual(validate_inventory(self.valid)[0]["quantity"], 5)

    def test_rejects_missing_required_field(self):
        invalid = [{"sku": "SKU-1", "location_id": "LOC-1", "quantity": 5}]
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            validate_inventory(invalid)

    def test_rejects_negative_quantity(self):
        invalid = [dict(self.valid[0], quantity=-1)]
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            validate_inventory(invalid)

    def test_rejects_duplicate_business_key(self):
        with self.assertRaisesRegex(ValueError, "duplicate business key"):
            validate_inventory(self.valid + self.valid)

    def test_rejects_timestamp_without_timezone(self):
        invalid = [dict(self.valid[0], source_updated_at="2026-11-09T10:00:00")]
        with self.assertRaisesRegex(ValueError, "timezone-aware ISO-8601"):
            validate_inventory(invalid)

    def test_reads_synthetic_json_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.json"
            path.write_text('[{"sku":"SKU-1"}]', encoding="utf-8")
            self.assertEqual(read_inventory(path), [{"sku": "SKU-1"}])


class InventoryUpsertTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "inventory.db"
        self.record = {
            "sku": "SKU-1", "location_id": "LOC-1", "quantity": 5,
            "source_updated_at": "2026-11-09T10:00:00Z",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def fetch_rows(self):
        with closing(sqlite3.connect(self.database)) as connection:
            return connection.execute(
                "SELECT sku, location_id, quantity, source_updated_at FROM inventory_current"
            ).fetchall()

    def test_repeated_load_does_not_duplicate_or_change_rows(self):
        upsert_inventory([self.record], self.database)
        first_snapshot = self.fetch_rows()
        upsert_inventory([self.record], self.database)
        self.assertEqual(self.fetch_rows(), first_snapshot)
        self.assertEqual(len(self.fetch_rows()), 1)

    def test_newer_source_record_updates_existing_business_key(self):
        upsert_inventory([self.record], self.database)
        newer = dict(self.record, quantity=9, source_updated_at="2026-11-10T10:00:00Z")
        upsert_inventory([newer], self.database)
        self.assertEqual(self.fetch_rows()[0][2], 9)
        self.assertEqual(len(self.fetch_rows()), 1)

    def test_older_source_record_does_not_overwrite_newer_state(self):
        newer = dict(self.record, quantity=9, source_updated_at="2026-11-10T10:00:00Z")
        upsert_inventory([newer], self.database)
        upsert_inventory([self.record], self.database)
        self.assertEqual(self.fetch_rows()[0][2], 9)


if __name__ == "__main__":
    unittest.main()
