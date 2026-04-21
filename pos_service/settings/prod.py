import os
from corsheaders.defaults import default_headers
from .base import *

print("Using Production Settings")

if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(default=os.environ.get("DATABASE_URL"), conn_max_age=600)
    }
    DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": "5432",
            "OPTIONS": {"sslmode": "disable"},
        }
    }

DEBUG = False

# Service URLs for production environment
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL", "http://quidpath-backend-prod:8004")
INVENTORY_SERVICE_URL = os.environ.get("INVENTORY_SERVICE_URL", "http://inventory-backend:8000")
CRM_SERVICE_URL = os.environ.get("CRM_SERVICE_URL", "http://crm-backend:8000")
HRM_SERVICE_URL = os.environ.get("HRM_SERVICE_URL", "http://hrm-backend:8000")
PROJECTS_SERVICE_URL = os.environ.get("PROJECTS_SERVICE_URL", "http://projects-backend:8007")

_default_hosts = "pos.quidpath.com,api.quidpath.com,quidpath.com,www.quidpath.com,localhost,127.0.0.1,0.0.0.0"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()]
if "pos-backend" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("pos-backend")

CSRF_TRUSTED_ORIGINS = ["https://quidpath.com", "https://www.quidpath.com", "https://*.quidpath.com"]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ["https://quidpath.com", "https://www.quidpath.com"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization", "content-type"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
