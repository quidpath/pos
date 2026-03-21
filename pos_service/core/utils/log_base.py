# core/utils/log_base.py
import logging
import uuid

from django.db import transaction

from pos_service.audit.models import TransactionLog
from pos_service.core.utils.request_parser import get_client_ip

logger = logging.getLogger(__name__)


class TransactionLogBase:
    """Logs important steps to audit.TransactionLog."""

    @classmethod
    def log(
        cls,
        action,
        user=None,
        message="",
        state_name="Active",
        extra=None,
        notification_resp=None,
        request=None,
    ):
        instance = cls()
        return instance._log_transaction(
            action=action,
            user=user,
            message=message,
            state_name=state_name,
            extra=extra,
            notification_resp=notification_resp,
            request=request,
        )

    def _log_transaction(
        self,
        action,
        user=None,
        message="",
        state_name="Active",
        extra=None,
        notification_resp=None,
        request=None,
    ):
        try:
            with transaction.atomic():
                user_id = None
                if user is not None:
                    user_id = getattr(user, "id", user) if not isinstance(user, int) else user
                source_ip = get_client_ip(request) if request else "0.0.0.0"
                details = extra or {}
                if request:
                    details["user_agent"] = request.META.get("HTTP_USER_AGENT", "")
                ref = str(uuid.uuid4())
                txn = TransactionLog.objects.create(
                    reference=ref,
                    action=action,
                    user_id=user_id,
                    corporate_id=getattr(request, "corporate_id", None) if request else None,
                    message=message,
                    state=state_name,
                    source_ip=source_ip,
                    extra=details,
                )
                logger.info(f"[TransactionLog] {action} | user={user_id} | state={state_name}")
                return txn
        except Exception as e:
            logger.exception(f"[TransactionLog] Failed logging {action}: {e}")
            return None
