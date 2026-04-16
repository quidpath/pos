# Generated migration for adding draft/posted timestamps to POSOrder

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS drafted_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_at TIMESTAMP WITH TIME ZONE NULL;",
                "ALTER TABLE pos_posorder ADD COLUMN IF NOT EXISTS posted_by UUID NULL;",
            ],
            reverse_sql=[
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS drafted_at;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS posted_at;",
                "ALTER TABLE pos_posorder DROP COLUMN IF EXISTS posted_by;",
            ],
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS posorder_state_idx ON pos_posorder (state);",
            reverse_sql="DROP INDEX IF EXISTS posorder_state_idx;",
        ),
    ]
