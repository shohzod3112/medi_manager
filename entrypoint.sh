#!/bin/bash
set -e

log() { echo "[$(date +'%H:%M:%S')] $1"; }
error() { echo "ERROR: $1" >&2; exit 1; }

# Wait for database
wait_for_db() {
    log "Waiting for database ($DB_HOST)..."
    timeout 60 bash -c "until nc -z $DB_HOST $DB_PORT; do sleep 1; done" || error "Database timeout"
}

# Wait for Redis
wait_for_redis() {
    log "Waiting for Redis..."
    timeout 30 bash -c "until nc -z redis 6379; do sleep 1; done" || error "Redis timeout"
}

run_migrations() {
    log "Running migrations..."
    python manage.py migrate --noinput || error "Migration failed"
    log "Collecting static files..."
    python manage.py collectstatic --noinput || log "Static collection failed"
}

# Initialization
[ "$DATABASE" = "postgres" ] && wait_for_db
wait_for_redis

if [[ "$*" == *"gunicorn"* ]] || [[ "$*" == *"runserver"* ]] || [[ "$*" == *"manage.py"* ]]; then
    run_migrations
fi

log "Starting command: $*"
exec "$@"