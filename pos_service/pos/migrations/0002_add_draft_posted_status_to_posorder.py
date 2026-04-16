from django.db import migrations


class Migration(migrations.Migration):
    """No-op: columns already applied on prod DB from prior deployment."""

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = []
