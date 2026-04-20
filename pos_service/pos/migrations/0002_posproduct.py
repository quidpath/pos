# Generated migration for POSProduct model

from django.db import migrations, models
import django.core.validators
from decimal import Decimal
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='POSProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('product_id', models.UUIDField(db_index=True, help_text='ID from inventory service', unique=True)),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(blank=True, db_index=True, max_length=100)),
                ('barcode', models.CharField(blank=True, db_index=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('category', models.CharField(blank=True, max_length=100)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('current_stock', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('synced_from_inventory', models.BooleanField(default=True)),
                ('last_synced_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('corporate_id', models.UUIDField(db_index=True)),
            ],
            options={
                'db_table': 'pos_products',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='posproduct',
            index=models.Index(fields=['corporate_id', 'is_active'], name='pos_product_corp_active_idx'),
        ),
        migrations.AddIndex(
            model_name='posproduct',
            index=models.Index(fields=['corporate_id', 'sku'], name='pos_product_corp_sku_idx'),
        ),
        migrations.AddIndex(
            model_name='posproduct',
            index=models.Index(fields=['corporate_id', 'barcode'], name='pos_product_corp_barcode_idx'),
        ),
    ]
