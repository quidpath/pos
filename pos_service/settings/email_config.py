"""
Email Configuration for Receipt Sending
Ensures emails are sent from user's email, not system email
"""
import os
from django.conf import settings

# Email Backend Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# SMTP Configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'

# Default system email (fallback only)
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@quidpath.com')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'server@quidpath.com')

# Email timeout
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', 10))

# For development/testing
if os.getenv('ENVIRONMENT') == 'development':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Email sending configuration
EMAIL_CONFIG = {
    'max_retries': 3,
    'retry_delay': 2,  # seconds
    'batch_size': 50,  # for bulk emails
}

# Template paths
EMAIL_TEMPLATE_DIR = os.path.join(settings.BASE_DIR, 'pos_service', 'templates', 'pos')

# Receipt email configuration
RECEIPT_EMAIL_CONFIG = {
    'subject_prefix': 'Receipt for Order',
    'include_logo': True,
    'include_qr_code': False,  # Future: QR code for order lookup
    'attach_pdf': False,  # Future: PDF attachment
}
