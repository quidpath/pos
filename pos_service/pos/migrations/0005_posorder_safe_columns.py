from django.db import migrations


class Migration(migrations.Migration):
    """Safely adds all POSOrder columns using IF NOT EXISTS."""

    dependencies = [
        ('pos', '0004_posorder_safe_columns'),
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
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=[
                "CREATE INDEX IF NOT EXISTS posorder_state_idx ON pos_posorder (state);",
                "CREATE INDEX IF NOT EXISTS pos_posorde_custome_idx ON pos_posorder (customer_id, created_at);",
                "CREATE INDEX IF NOT EXISTS pos_posorde_is_invo_idx ON pos_posorder (is_invoiced, state);",
                "CREATE INDEX IF NOT EXISTS pos_posorder_invoice_id_idx ON pos_posorder (invoice_id);",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
