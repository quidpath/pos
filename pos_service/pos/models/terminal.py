"""POS Terminal model"""
import uuid
from django.db import models
from .store import Store


class POSTerminal(models.Model):
    """POS terminal/register"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='terminals')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pos_terminal'
        ordering = ['store', 'name']

    def __str__(self):
        return f"{self.store.name} - {self.name}"
