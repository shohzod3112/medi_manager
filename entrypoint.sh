#!/bin/bash
set -e

log() { echo "[$(date +'%H:%M:%S')] $1"; }

echo "🔐 Checking licence..."
# PYTHONPATH orqali /app papkasini modullar qidiruvi uchun majburiy ko'rsatamiz
PYTHONPATH=/app python3 core/check_licence.py || exit 1

log "Waiting for database..."
: "${DB_HOST:=db}"
: "${DB_PORT:=5432}"
until nc -z $DB_HOST $DB_PORT; do sleep 1; done
log "Database ready"

log "Waiting for Redis..."
: "${REDIS_HOST:=redis}"
: "${REDIS_PORT:=6379}"
until nc -z $REDIS_HOST $REDIS_PORT; do sleep 1; done
log "Redis ready"

log "Running migrations..."
python manage.py migrate --noinput

log "Collecting static..."
python manage.py collectstatic --noinput

log "Starting app: $@"
exec "$@"