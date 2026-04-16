from django.db import migrations


class Migration(migrations.Migration):
    """No-op: already applied on prod DB from prior deployment."""

    dependencies = [
        ('pos', '0003_merge_0002_migrations'),
    ]

    operations = []
