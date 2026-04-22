# Generated migration for payment account and accounting sync fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='posorder',
            name='payment_account_id',
            field=models.UUIDField(blank=True, db_index=True, help_text='Accounting account where payment was received', null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='accounting_synced',
            field=models.BooleanField(default=False, help_text='Whether order has been synced to accounting'),
        ),
        migrations.AddField(
            model_name='posorder',
            name='accounting_sync_error',
            field=models.TextField(blank=True, help_text='Error message if accounting sync failed'),
        ),
        migrations.AlterField(
            model_name='posorder',
            name='state',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('pending', 'Pending Payment'),
                    ('paid', 'Paid'),
                    ('invoiced', 'Invoiced'),
                    ('cancelled', 'Cancelled')
                ],
                default='draft',
                max_length=20
            ),
        ),
        migrations.AddIndex(
            model_name='posorder',
            index=models.Index(fields=['accounting_synced', 'state'], name='pos_order_acc_sync_idx'),
        ),
    ]
