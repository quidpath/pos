# Generated migration for payment account and accounting sync fields

from django.db import migrations, models


def check_and_add_fields(apps, schema_editor):
    """
    Safely add fields to pos_order table if it exists.
    This handles cases where the table might not exist yet.
    """
    with schema_editor.connection.cursor() as cursor:
        # Check if the table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pos_order'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Table doesn't exist yet, skip this migration
            return
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pos_order' 
            AND column_name IN ('payment_account_id', 'accounting_synced', 'accounting_sync_error');
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        # Add missing columns
        if 'payment_account_id' not in existing_columns:
            cursor.execute("""
                ALTER TABLE pos_order 
                ADD COLUMN payment_account_id UUID NULL;
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS pos_order_payment_account_id_idx 
                ON pos_order(payment_account_id);
            """)
        
        if 'accounting_synced' not in existing_columns:
            cursor.execute("""
                ALTER TABLE pos_order 
                ADD COLUMN accounting_synced BOOLEAN NOT NULL DEFAULT FALSE;
            """)
        
        if 'accounting_sync_error' not in existing_columns:
            cursor.execute("""
                ALTER TABLE pos_order 
                ADD COLUMN accounting_sync_error TEXT NOT NULL DEFAULT '';
            """)
        
        # Create composite index if it doesn't exist
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS pos_order_acc_sync_idx 
            ON pos_order(accounting_synced, state);
        """)


def reverse_migration(apps, schema_editor):
    """Reverse the migration by dropping the added columns"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pos_order'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("DROP INDEX IF EXISTS pos_order_acc_sync_idx;")
            cursor.execute("DROP INDEX IF EXISTS pos_order_payment_account_id_idx;")
            cursor.execute("ALTER TABLE pos_order DROP COLUMN IF EXISTS accounting_sync_error;")
            cursor.execute("ALTER TABLE pos_order DROP COLUMN IF EXISTS accounting_synced;")
            cursor.execute("ALTER TABLE pos_order DROP COLUMN IF EXISTS payment_account_id;")


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(check_and_add_fields, reverse_migration),
    ]
