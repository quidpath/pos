# Generated migration for POS-ERP integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='posorder',
            name='invoice_id',
            field=models.UUIDField(blank=True, db_index=True, help_text='Accounting Invoice ID', null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='is_invoiced',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='posorder',
            name='invoiced_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='invoiced_by',
            field=models.UUIDField(blank=True, help_text='User ID who converted to invoice', null=True),
        ),
        migrations.AlterField(
            model_name='posorder',
            name='customer_id',
            field=models.UUIDField(blank=True, db_index=True, help_text='CRM Contact ID', null=True),
        ),
        migrations.AlterField(
            model_name='posorder',
            name='tax_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Tax applied only when converted to invoice', max_digits=14),
        ),
        migrations.AddIndex(
            model_name='posorder',
            index=models.Index(fields=['customer_id', 'created_at'], name='pos_posorde_custome_idx'),
        ),
        migrations.AddIndex(
            model_name='posorder',
            index=models.Index(fields=['is_invoiced', 'state'], name='pos_posorde_is_invo_idx'),
        ),
    ]
