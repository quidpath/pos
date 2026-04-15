import logging
import os

import jwt
from django.conf import settings
from django.http import JsonResponse

from pos_service.services.user_cache_service import UserCacheService

logger = logging.getLogger(__name__)

SERVICE_TO_SERVICE_PATHS = [
    "/api/pos/",
    "/api/purchases/",
]


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_service = UserCacheService()

    def __call__(self, request):
        if self._is_public_endpoint(request.path):
            return self.get_response(request)

        service_secret = os.environ.get("POS_SERVICE_SECRET") or getattr(settings, "POS_SERVICE_SECRET", "")
        if service_secret and self._is_service_to_service_path(request.path):
            key = request.META.get("HTTP_X_SERVICE_KEY", "").strip()
            if key and key == service_secret:
                request.service_call = True
                request.user_id = None
                request.corporate_id = None
                request.user_data = {}
                request.corporate_data = None
                return self.get_response(request)

        auth_header = request.META.get("HTTP_AUTHORIZATION", "").strip()
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Missing or invalid authorization header"}, status=401)

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return JsonResponse({"error": "Missing or invalid authorization header"}, status=401)

        try:
            secret_key = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
            payload = jwt.decode(token, secret_key, algorithms=["HS256"], issuer="quidpath-backend")
            request.service_call = False
            request.user_id = payload["user_id"]
            request.corporate_id = payload.get("corporate_id")
            request.user_data = {
                "id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "role": payload.get("role"),
                "is_staff": payload.get("is_staff", False),
            }
            try:
                enriched = self.cache_service.get_user_data(payload["user_id"])
                if enriched:
                    request.user_data.update(enriched)
                request.corporate_data = (
                    self.cache_service.get_corporate_data(request.corporate_id)
                    if request.corporate_id else None
                )
            except Exception as e:
                logger.warning("Failed to enrich user data: %s", e)
                request.corporate_data = None
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=401)
        except jwt.InvalidTokenError as e:
            return JsonResponse({"error": "Invalid token", "detail": str(e)}, status=401)
        except Exception as e:
            logger.error("Authentication failed: %s", e)
            return JsonResponse({"error": f"Authentication failed: {str(e)}"}, status=500)

        return self.get_response(request)

    def _is_public_endpoint(self, path):
        return any(path.startswith(p) for p in ["/health/", "/api/docs/", "/admin/", "/static/", "/media/", "/api/pos/webhooks/"])

    def _is_service_to_service_path(self, path):
        return any(path.startswith(p) for p in SERVICE_TO_SERVICE_PATHS)
