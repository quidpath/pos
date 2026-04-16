from django.db import migrations


class Migration(migrations.Migration):
    """
    Safely ensures all POSOrder columns exist using IF NOT EXISTS.
    Works on both fresh DBs and existing ones where columns were already added.
    """

    dependencies = [
        ('pos', '0003_merge_0002_migrations'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS drafted_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_by UUID NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoice_id UUID NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS is_invoiced BOOLEAN NOT NULL DEFAULT FALSE;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_by UUID NULL;",
            ],
            reverse_sql=[
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS drafted_at;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS posted_at;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS posted_by;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS invoice_id;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS is_invoiced;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS invoiced_at;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS invoiced_by;",
            ],
        ),
        migrations.RunSQL(
            sql=[
                "CREATE INDEX IF NOT EXISTS posorder_state_idx ON pos_posorder (state);",
                "CREATE INDEX IF NOT EXISTS pos_posorde_custome_idx ON pos_posorder (customer_id, created_at);",
                "CREATE INDEX IF NOT EXISTS pos_posorde_is_invo_idx ON pos_posorder (is_invoiced, state);",
                "CREATE INDEX IF NOT EXISTS pos_posorder_invoice_id_idx ON pos_posorder (invoice_id);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS posorder_state_idx;",
                "DROP INDEX IF EXISTS pos_posorde_custome_idx;",
                "DROP INDEX IF EXISTS pos_posorde_is_invo_idx;",
                "DROP INDEX IF EXISTS pos_posorder_invoice_id_idx;",
            ],
        ),
    ]
