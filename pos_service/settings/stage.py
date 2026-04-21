# settings/stage.py — Stage environment for POS service
import logging
import os

from corsheaders.defaults import default_headers

from .base import *

logger = logging.getLogger(__name__)

if not os.environ.get("DATABASE_URL"):
    raise ValueError("Stage requires DATABASE_URL (e.g. postgresql://USER:PASSWORD@db:5432/DB)")
DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}

DEBUG = False

# Service URLs for stage environment
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL", "http://quidpath-backend-stage:8004")
INVENTORY_SERVICE_URL = os.environ.get("INVENTORY_SERVICE_URL", "http://inventory-backend-stage:8000")
CRM_SERVICE_URL = os.environ.get("CRM_SERVICE_URL", "http://crm-backend-stage:8000")
HRM_SERVICE_URL = os.environ.get("HRM_SERVICE_URL", "http://hrm-backend-stage:8000")
PROJECTS_SERVICE_URL = os.environ.get("PROJECTS_SERVICE_URL", "http://projects-backend-stage:8007")

_default_hosts = "stage.quidpath.com,www.stage.quidpath.com,stage-pos.quidpath.com,stage-api.quidpath.com,localhost,127.0.0.1,0.0.0.0"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()]
if "pos-backend-stage" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("pos-backend-stage")

_env_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _env_csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _env_csrf.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://stage.quidpath.com",
        "https://www.stage.quidpath.com",
        "https://stage-pos.quidpath.com",
    ]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://stage.quidpath.com",
    "https://www.stage.quidpath.com",
    "https://stage-api.quidpath.com",
    "https://stage-pos.quidpath.com",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization", "content-type"]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
