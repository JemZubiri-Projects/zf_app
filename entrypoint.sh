#!/usr/bin/env bash
set -e

# Default DB_PORT to 3306 if not set
DB_PORT=${DB_PORT:-3306}

# Wait for DB if DB_HOST is set
if [ -n "$DB_HOST" ]; then
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
  echo "Connection to db ($DB_HOST) $DB_PORT port [tcp/mysql] succeeded!"
  echo "Database is up!"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "$DJANGO_COLLECTSTATIC" = "1" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# 👉 If the user passed a command (e.g. `python manage.py import_zf ...`),
#    run THAT instead of starting the server.
if [ "$#" -gt 0 ]; then
  echo "Running custom command: $@"
  exec "$@"
fi

# Default behavior: start Django dev server or Gunicorn
if [ "$DJANGO_USE_GUNICORN" = "1" ]; then
  echo "Starting Gunicorn..."
  exec gunicorn zf_app.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 3
else
  echo "Starting Django development server..."
  exec python manage.py runserver 0.0.0.0:8000
fi
