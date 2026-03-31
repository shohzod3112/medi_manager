#!/bin/bash
set -e

log() {
    echo "[ENTRYPOINT] $1"
}

# Agar root bo‘lsa — ruxsatlarni to‘g‘rilaymiz
if [ "$(id -u)" = "0" ]; then
    log "Fixing permissions..."

    mkdir -p /app/media /app/static /app/staticfiles /app/logs /tmp
    chown -R app:app /app/media /app/static /app/staticfiles /app/logs /tmp

else
    log "Running as $(whoami)"
    exec "$@"
fi

# ---- endi app user ichidamiz ----

# Simple logging
log() { echo "[$(date +'%H:%M:%S')] $1"; }
error() { echo "ERROR: $1" >&2; exit 1; }

# Wait for database
wait_for_db() {
    log "Waiting for database..."
    timeout 60 bash -c "until nc -z $DB_HOST $DB_PORT; do sleep 1; done" || error "Database timeout"
    log "Database ready"
}

# Wait for Redis
wait_for_redis() {
    log "Waiting for Redis..."
    timeout 30 bash -c "until nc -z redis 6379; do sleep 1; done" || error "Redis timeout"
    log "Redis ready"
}

# Run migrations (simple approach)
run_migrations() {
    log "Running migrations..."
    python manage.py migrate --noinput || error "Migration failed"

    log "Collecting static files..."
    python manage.py collectstatic --noinput || log "Static collection failed (continuing)"
}

# Main execution
log "Starting initialization..."

# Wait for services
[ "$DATABASE" = "postgres" ] && wait_for_db
wait_for_redis

# Run setup for web server and any management commands
if [[ "$*" == *"runserver"* ]] || [[ "$*" == *"runsslserver"* ]] || [[ "$*" == *"manage.py"* ]]; then
    run_migrations
fi

log "Starting: $*"