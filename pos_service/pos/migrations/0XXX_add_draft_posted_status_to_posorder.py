# Generated migration for adding draft/posted timestamps to POSOrder

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0XXX_previous_migration'),  # Update with actual previous migration
    ]

    operations = [
        migrations.AddField(
            model_name='posorder',
            name='drafted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='posted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='posted_by',
            field=models.UUIDField(blank=True, null=True, help_text='User ID who posted the order'),
        ),
        migrations.AddIndex(
            model_name='posorder',
            index=models.Index(fields=['state'], name='posorder_state_idx'),
        ),
    ]
