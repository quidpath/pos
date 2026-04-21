from .base import *

DEBUG = TRUE
ALLOWED_HOSTS = ["*"]

# Service URLs for development environment
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL", "http://quidpath-backend-dev:8004")
INVENTORY_SERVICE_URL = os.environ.get("INVENTORY_SERVICE_URL", "http://inventory-backend-dev:8000")
CRM_SERVICE_URL = os.environ.get("CRM_SERVICE_URL", "http://crm-backend-dev:8000")
HRM_SERVICE_URL = os.environ.get("HRM_SERVICE_URL", "http://hrm-backend-dev:8000")
PROJECTS_SERVICE_URL = os.environ.get("PROJECTS_SERVICE_URL", "http://projects-backend-dev:8007")

CORS_ALLOW_ALL_ORIGINS = True
