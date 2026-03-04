#!/bin/sh
set -e

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Creating superuser (skipped if already exists or env vars not set)..."
python manage.py createsuperuser --noinput 2>/dev/null || true

echo "==> Starting Gunicorn..."
exec gunicorn portfolio.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
