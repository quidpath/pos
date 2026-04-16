import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class UserCacheService:
    def get_user_data(self, user_id):
        cache_key = f"user_{user_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        try:
            resp = requests.get(
                f"{settings.ERP_BACKEND_URL}/api/auth/users/{user_id}/",
                headers={"X-Service-Key": getattr(settings, 'ERP_SERVICE_SECRET', '') or getattr(settings, 'POS_SERVICE_SECRET', '')},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                cache.set(cache_key, data, settings.USER_CACHE_TTL)
                return data
        except Exception as e:
            logger.warning("Could not fetch user %s: %s", user_id, e)
        return None

    def get_corporate_data(self, corporate_id):
        cache_key = f"corporate_{corporate_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        try:
            resp = requests.get(
                f"{settings.ERP_BACKEND_URL}/api/auth/corporates/{corporate_id}/",
                headers={"X-Service-Key": getattr(settings, 'ERP_SERVICE_SECRET', '') or getattr(settings, 'POS_SERVICE_SECRET', '')},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                cache.set(cache_key, data, settings.CORPORATE_CACHE_TTL)
                return data
        except Exception as e:
            logger.warning("Could not fetch corporate %s: %s", corporate_id, e)
        return None
