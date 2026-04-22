# Generated migration to make session optional for online orders

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_add_payment_account_and_sync_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='posorder',
            name='session',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional: POS session (for in-store sales)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to='pos.possession'
            ),
        ),
    ]
