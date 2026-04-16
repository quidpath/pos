# Generated migration for POS-ERP integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoice_id UUID NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS is_invoiced BOOLEAN NOT NULL DEFAULT FALSE;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_by UUID NULL;",
            ],
            reverse_sql=[
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS invoice_id;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS is_invoiced;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS invoiced_at;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS invoiced_by;",
            ],
        ),
        migrations.RunSQL(
            sql=[
                "CREATE INDEX IF NOT EXISTS pos_posorde_custome_idx ON pos_posorder (customer_id, created_at);",
                "CREATE INDEX IF NOT EXISTS pos_posorde_is_invo_idx ON pos_posorder (is_invoiced, state);",
                "CREATE INDEX IF NOT EXISTS pos_posorder_invoice_id_idx ON pos_posorder (invoice_id);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS pos_posorde_custome_idx;",
                "DROP INDEX IF EXISTS pos_posorde_is_invo_idx;",
                "DROP INDEX IF EXISTS pos_posorder_invoice_id_idx;",
            ],
        ),
    ]
