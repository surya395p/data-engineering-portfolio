-- PostgreSQL example: promote validated staging rows into current state.
-- Assumes a unique constraint on (sku, location_id).
-- All values are synthetic; adapt the business key only for a real data model.

INSERT INTO inventory_current AS target (
    sku, location_id, quantity, source_updated_at
)
SELECT
    sku, location_id, quantity, source_updated_at
FROM inventory_staging
WHERE validation_status = 'VALID'
ON CONFLICT (sku, location_id)
DO UPDATE SET
    quantity = EXCLUDED.quantity,
    source_updated_at = EXCLUDED.source_updated_at
WHERE target.source_updated_at IS NULL
   OR EXCLUDED.source_updated_at >= target.source_updated_at;
