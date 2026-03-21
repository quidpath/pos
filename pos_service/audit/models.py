from django.db import models

from pos_service.core.base_models import BaseModel


class TransactionLog(BaseModel):
    STATE_CHOICES = [
        ("Active", "Active"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
        ("Pending", "Pending"),
    ]

    reference = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=100, db_index=True)
    user_id = models.PositiveIntegerField(null=True, blank=True)
    corporate_id = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField(blank=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default="Active")
    source_ip = models.CharField(max_length=45, blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "audit_transactionlog"

    def __str__(self):
        return f"{self.action} | {self.state}"


class Notification(BaseModel):
    recipient_id = models.PositiveIntegerField(db_index=True)
    corporate_id = models.PositiveIntegerField(null=True, blank=True)
    notification_type = models.CharField(max_length=30, default="email")
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "audit_notification"

    def __str__(self):
        return f"{self.title} -> user {self.recipient_id}"
