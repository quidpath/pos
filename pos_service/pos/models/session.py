"""POS Session model - cashier shift tracking"""
import uuid
from django.db import models
from .terminal import POSTerminal


class POSSession(models.Model):
    """Cashier session/shift"""
    STATE_CHOICES = [
        ('opening', 'Opening'),
        ('open', 'Open'),
        ('closing', 'Closing'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    terminal = models.ForeignKey(POSTerminal, on_delete=models.CASCADE, related_name='sessions')
    cashier_id = models.UUIDField(db_index=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='opening')
    opening_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_difference = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'pos_session'
        ordering = ['-opened_at']

    def __str__(self):
        return f"Session {self.terminal.name} - {self.opened_at.strftime('%Y-%m-%d %H:%M')}"
