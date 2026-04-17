-- SQL script to manually fix POS migration issues
-- Run this script if you need to manually fix the database state

-- First, check what columns exist in pos_posorder
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'pos_posorder' 
AND column_name IN ('drafted_at', 'posted_at', 'posted_by', 'invoice_id', 'is_invoiced', 'invoiced_at', 'invoiced_by')
ORDER BY column_name;

-- Add missing columns safely (only if they don't exist)
ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS drafted_at TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_at TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_by UUID NULL;
ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoice_id UUID NULL;
ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS is_invoiced BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_at TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_by UUID NULL;

-- Create indexes safely
CREATE INDEX IF NOT EXISTS pos_posorder_invoice_id_idx ON pos_posorder (invoice_id);
CREATE INDEX IF NOT EXISTS pos_posorder_is_invoiced_state_idx ON pos_posorder (is_invoiced, state);
CREATE INDEX IF NOT EXISTS pos_posorder_customer_created_idx ON pos_posorder (customer_id, created_at);
CREATE INDEX IF NOT EXISTS pos_posorder_state_idx ON pos_posorder (state);

-- Mark the migration as applied to prevent Django from trying to apply it again
INSERT INTO django_migrations (app, name, applied) 
VALUES ('pos', '0006_ensure_schema_consistency', NOW())
ON CONFLICT (app, name) DO NOTHING;

-- Verify the migration state
SELECT name, applied FROM django_migrations WHERE app = 'pos' ORDER BY name;