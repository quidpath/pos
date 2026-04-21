#!/bin/bash
set -euo pipefail
echo "Starting POS & Purchases Service"
APP_DIR="/app"
cd "$APP_DIR"

if [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"; value="${BASH_REMATCH[2]}"
      value="${value#\'}"; value="${value%\'}"; value="${value#\"}"; value="${value%\"}"
      if [[ -z "${!key:-}" ]]; then export "$key=$value"; fi
    fi
  done < .env
fi

PYTHON=$(command -v python3 || command -v python)
$PYTHON manage.py migrate --noinput
$PYTHON manage.py collectstatic --noinput

echo "Creating superuser..."
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  $PYTHON manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || echo "Superuser already exists"
else
  echo "Skipping superuser creation - environment variables not set"
fi

exec gunicorn pos_service.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout 120
