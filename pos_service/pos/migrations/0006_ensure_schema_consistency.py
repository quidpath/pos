# Generated migration to ensure schema consistency
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    This migration ensures the database schema matches the model definition
    without attempting to add columns that already exist.
    """

    dependencies = [
        ('pos', '0005_posorder_safe_columns'),
    ]

    operations = [
        # Use raw SQL to safely ensure all columns exist without conflicts
        migrations.RunSQL(
            sql=[
                # Ensure all POSOrder columns exist (using IF NOT EXISTS to avoid conflicts)
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS drafted_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_at TIMESTAMP WITH TIME ZONE NULL;", 
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_by UUID NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoice_id UUID NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS is_invoiced BOOLEAN NOT NULL DEFAULT FALSE;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS invoiced_by UUID NULL;",
                
                # Ensure all indexes exist
                "CREATE INDEX IF NOT EXISTS pos_posorder_invoice_id_idx ON pos_posorder (invoice_id);",
                "CREATE INDEX IF NOT EXISTS pos_posorder_is_invoiced_state_idx ON pos_posorder (is_invoiced, state);",
                "CREATE INDEX IF NOT EXISTS pos_posorder_customer_created_idx ON pos_posorder (customer_id, created_at);",
                "CREATE INDEX IF NOT EXISTS pos_posorder_state_idx ON pos_posorder (state);",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]