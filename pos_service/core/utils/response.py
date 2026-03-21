import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.files.base import File
from django.db import models
from django.http import JsonResponse


def comprehensive_serializer(obj):
    """Comprehensive serializer that handles all common Django/Python objects."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, models.Model):
        result = {}
        for field in obj._meta.fields:
            field_name = field.name
            field_value = getattr(obj, field_name)
            if isinstance(field_value, models.Model):
                result[f"{field_name}_id"] = str(field_value.pk) if field_value.pk else None
            elif isinstance(field_value, (datetime, date)):
                result[field_name] = field_value.isoformat() if field_value else None
            elif isinstance(field_value, UUID):
                result[field_name] = str(field_value)
            elif isinstance(field_value, Decimal):
                result[field_name] = float(field_value)
            elif isinstance(field_value, File):
                result[field_name] = field_value.url if field_value else None
            else:
                result[field_name] = field_value
        return result
    if isinstance(obj, File):
        return obj.url if obj else None
    if isinstance(obj, (list, tuple)):
        return [comprehensive_serializer(item) for item in obj]
    if isinstance(obj, dict):
        return {key: comprehensive_serializer(value) for key, value in obj.items()}
    if isinstance(obj, set):
        return list(obj)
    try:
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)
    except Exception:
        return str(obj)


class ResponseProvider:
    """Provides standardized JSON responses. Status: 400 Bad Request, 200 Success, 401 Unauthorized, 500 Internal Server Error."""

    def __init__(self, data=None, message=None, code=None):
        self.data = data or {}
        if message:
            self.data["code"] = code
            self.data["message"] = message

    def _response(self, status):
        return JsonResponse(
            self.data,
            status=status,
            json_dumps_params={"default": comprehensive_serializer},
            safe=False,
        )

    def success(self):
        try:
            serialized_data = json.loads(json.dumps(self.data, default=comprehensive_serializer))
            return JsonResponse(serialized_data, status=200, json_dumps_params={"default": comprehensive_serializer}, safe=False)
        except Exception as e:
            return JsonResponse({"code": 500, "message": "Serialization error occurred", "error": str(e)}, status=500)

    def bad_request(self):
        return self._response(status=400)

    def unauthorized(self):
        return self._response(status=401)

    def exception(self):
        return self._response(status=500)

    @staticmethod
    def success_response(data=None, message=None, status=200):
        payload = {"success": True}
        if data is not None:
            payload["data"] = data
        if message is not None:
            payload["message"] = message
        try:
            serialized = json.loads(json.dumps(payload, default=comprehensive_serializer))
            return JsonResponse(serialized, status=status)
        except Exception:
            return JsonResponse({"success": True, "message": message or "OK"}, status=status)

    @staticmethod
    def error_response(message, status=400, data=None):
        payload = {"success": False, "message": message}
        if data is not None:
            payload["data"] = data
        return JsonResponse(payload, status=status)

    @staticmethod
    def method_not_allowed(allowed_methods):
        return JsonResponse(
            {"success": False, "message": "Method not allowed", "allowed": allowed_methods},
            status=405,
        )

    @staticmethod
    def raw_response(body, status=200):
        return JsonResponse(body, status=status)
