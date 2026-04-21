import os
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_FILE = BASE_DIR / (".env.dev" if os.environ.get("DJANGO_ENV") == "dev" else ".env")
load_dotenv(ENV_FILE)

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-dev-key")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    "django_celery_results",
    "pos_service.core",
    "pos_service.audit",
    "pos_service.pos.apps.POSConfig",
    "pos_service.purchases.apps.PurchasesConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "pos_service.middleware.jwt_auth.JWTAuthenticationMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pos_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "pos_service" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "pos_service.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
    )
}

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)

# Service URLs for integration - set in environment-specific settings
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL")
INVENTORY_SERVICE_URL = os.environ.get("INVENTORY_SERVICE_URL")
CRM_SERVICE_URL = os.environ.get("CRM_SERVICE_URL")
HRM_SERVICE_URL = os.environ.get("HRM_SERVICE_URL")
PROJECTS_SERVICE_URL = os.environ.get("PROJECTS_SERVICE_URL")

# Service authentication - own secret
POS_SERVICE_SECRET = os.environ.get("POS_SERVICE_SECRET", "")
# Cross-service secrets (used when calling other services)
ERP_SERVICE_SECRET = os.environ.get("ERP_SERVICE_SECRET", "")
INVENTORY_SERVICE_SECRET = os.environ.get("INVENTORY_SERVICE_SECRET", "")
CRM_SERVICE_SECRET = os.environ.get("CRM_SERVICE_SECRET", "")
HRM_SERVICE_SECRET = os.environ.get("HRM_SERVICE_SECRET", "")
PROJECTS_SERVICE_SECRET = os.environ.get("PROJECTS_SERVICE_SECRET", "")
BILLING_SERVICE_SECRET = os.environ.get("BILLING_SERVICE_SECRET", "")
PROJECTS_SERVICE_SECRET = os.environ.get("PROJECTS_SERVICE_SECRET", "")
BILLING_SERVICE_SECRET = os.environ.get("BILLING_SERVICE_SECRET", "")
# Legacy alias
SERVICE_API_KEY = ERP_SERVICE_SECRET or POS_SERVICE_SECRET

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Nairobi"

USER_CACHE_TTL = int(os.environ.get("USER_CACHE_TTL", 3600))
CORPORATE_CACHE_TTL = int(os.environ.get("CORPORATE_CACHE_TTL", 86400))

MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY", "")
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "")
MPESA_BUSINESS_SHORT_CODE = os.environ.get("MPESA_BUSINESS_SHORT_CODE", "")
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY", "")
MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL", "")
MPESA_ENVIRONMENT = os.environ.get("MPESA_ENVIRONMENT", "production")

# Email Configuration
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@quidpath.com")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", "server@quidpath.com")
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", 10))

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser", "rest_framework.parsers.MultiPartParser"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = ["https://quidpath.com", "https://www.quidpath.com", "http://localhost:3000"]
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization"]
