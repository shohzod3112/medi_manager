#!/bin/sh
set -e

echo "Waiting for database..."
while ! nc -z "$SUPERUSER_DB_HOST" "$SUPERUSER_DB_PORT"; do
  sleep 1
done

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput

  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

echo "Starting application..."
exec "$@"
