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
$PYTHON manage.py makemigrations --noinput
$PYTHON manage.py migrate --noinput
$PYTHON manage.py collectstatic --noinput
$PYTHON manage.py createsuperuser --noinput || true

exec gunicorn pos_service.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout 120
