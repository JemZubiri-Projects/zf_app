#!/usr/bin/env bash
set -e

# Wait for DB if DB_HOST is defined
if [ -n "$DB_HOST" ]; then
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
  echo "Database is up!"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "$DJANGO_COLLECTSTATIC" = "1" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

if [ "$DJANGO_USE_GUNICORN" = "1" ]; then
  echo "Starting Gunicorn..."
  # ⚠️ CHANGE "myproject" below to your Django project package (the one with settings.py)
  exec gunicorn myproject.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 3
else
  echo "Starting Django development server..."
  exec python manage.py runserver 0.0.0.0:8000
fi
