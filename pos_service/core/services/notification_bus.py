"""Single entry point for email and in-app notifications."""

import logging

from pos_service.audit.models import Notification
from pos_service.audit.tasks import send_notification_email

logger = logging.getLogger(__name__)


class NotificationBus:
    def send(
        self,
        recipient_id,
        notification_type="email",
        title="",
        message="",
        data=None,
        corporate_id=None,
    ):
        data = data or {}
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            corporate_id=corporate_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data,
        )
        if notification_type == "email":
            send_notification_email.delay(str(notification.id))
        return notification

    def send_email(self, recipient_id, subject, body, destination_email=None, corporate_id=None):
        data = {}
        if destination_email:
            data["email"] = destination_email
        return self.send(
            recipient_id=recipient_id,
            notification_type="email",
            title=subject,
            message=body,
            data=data,
            corporate_id=corporate_id,
        )
