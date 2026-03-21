import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id):
    from pos_service.audit.models import Notification

    try:
        notification = Notification.objects.filter(id=notification_id).first()
        if not notification:
            return
        email = (notification.data or {}).get("email")
        if not email or notification.notification_type != "email":
            return
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@quidpath.com"),
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning("send_notification_email failed: %s", e)
        raise self.retry(exc=e)
