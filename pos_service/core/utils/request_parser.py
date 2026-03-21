# core/utils/request_parser.py
import json
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    if not request:
        return ""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_request_data(request):
    try:
        if request is None:
            return {}
        content_type = request.META.get("CONTENT_TYPE", "")
        method = request.method.upper()
        if "application/json" in content_type:
            return json.loads(request.body or "{}")
        if "multipart/form-data" in content_type:
            return request.POST.dict()
        if method == "GET":
            return request.GET.dict()
        if method == "POST":
            return request.POST.dict()
        if request.body:
            return json.loads(request.body)
        return {}
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        raise ValueError(f"Error parsing request data: {e}")


def get_data(request):
    data = get_request_data(request)
    metadata = {
        "ip_address": get_client_ip(request),
        "user_agent": request.META.get("HTTP_USER_AGENT") if request else "",
        "origin": request.META.get("HTTP_ORIGIN") if request else "",
    }
    return data, metadata


def get_clean_data(request):
    """Return (data, metadata). Metadata is populated from JWTAuthenticationMiddleware-set request attrs."""
    data = get_request_data(request)
    metadata = {
        "ip_address": get_client_ip(request),
        "user_agent": request.META.get("HTTP_USER_AGENT") if request else "",
        "origin": request.META.get("HTTP_ORIGIN") if request else "",
        "user_id": getattr(request, "user_id", None),
        "corporate_id": getattr(request, "corporate_id", None),
        "user_roles": getattr(request, "user_roles", []),
        "user_data": getattr(request, "user_data", {}),
        "corporate_data": getattr(request, "corporate_data", {}),
        "is_service_call": getattr(request, "is_service_call", False),
    }
    return data, metadata


def get_clean_data_safe(request, allowed_methods=None, require_json_body=True, max_body_length=1024 * 1024):
    """Returns (data, error_response). If error_response is not None, return it from the view."""
    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    from pos_service.core.utils.response import ResponseProvider

    if request.method not in allowed_methods:
        return None, ResponseProvider.method_not_allowed(allowed_methods)
    data = None
    if require_json_body and request.method in ("POST", "PUT", "PATCH") and request.body:
        if len(request.body) > max_body_length:
            return None, ResponseProvider.error_response("Request body too large", status=413)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("Invalid JSON body: %s", e)
            return None, ResponseProvider.error_response("Invalid JSON body", status=400)
        if not isinstance(data, dict):
            return None, ResponseProvider.error_response("JSON body must be an object", status=400)
    elif request.method == "GET":
        data = dict(request.GET.items())
    return data, None
