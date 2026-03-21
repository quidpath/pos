from django.contrib import admin
from .models import TransactionLog, Notification


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ["reference", "action", "user_id", "corporate_id", "state", "source_ip", "created_at"]
    list_filter = ["state", "action"]
    search_fields = ["reference", "message"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "recipient_id", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
