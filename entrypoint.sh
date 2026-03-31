#!/bin/bash
set -e

log() { echo "[$(date +'%H:%M:%S')] $1"; }
error() { echo "ERROR: $1" >&2; exit 1; }

# Fix permissions
log "Fixing permissions..."
mkdir -p /app/media /app/static /app/staticfiles /tmp
chown -R app:app /app/media /app/static /app/staticfiles /tmp

# Wait for DB
wait_for_db() {
    log "Waiting for database..."
    : "${DB_HOST:=db}"    # default host
    : "${DB_PORT:=5432}"  # default port
    timeout 60 bash -c "until nc -z $DB_HOST $DB_PORT; do sleep 1; done" || error "Database timeout"
    log "Database ready"
}

# Wait for Redis
wait_for_redis() {
    log "Waiting for Redis..."
    : "${REDIS_HOST:=redis}"
    : "${REDIS_PORT:=6379}"
    timeout 30 bash -c "until nc -z $REDIS_HOST $REDIS_PORT; do sleep 1; done" || error "Redis timeout"
    log "Redis ready"
}

# Run migrations
run_migrations() {
    log "Running migrations..."
    python manage.py migrate --noinput || error "Migration failed"

    log "Collecting static files..."
    python manage.py collectstatic --noinput || log "Static collection failed (continuing)"
}

# Main
log "Starting initialization..."
[ "$DATABASE" = "postgres" ] && wait_for_db
wait_for_redis
run_migrations

log "Starting: $*"
exec "$@"