#!/bin/bash
set -e

log() { echo "[$(date +'%H:%M:%S')] $1"; }
error() { echo "ERROR: $1" >&2; exit 1; }

# 1. Ruxsatlarni to'g'rilash (faqat root bo'lsak)
if [ "$(id -u)" = "0" ]; then
    log "Fixing permissions as root..."
    mkdir -p /app/media /app/static /app/staticfiles /app/logs /tmp
    chown -R app:app /app/media /app/static /app/staticfiles /app/logs /tmp

    # Ruxsatlar to'g'rilangach, skriptni 'app' foydalanuvchisi sifatida qayta ishga tushiramiz
    log "Switching to user app..."
    exec app "$0" "$@"
fi

# ---- BU YERDAN PASTI FAQAT 'APP' FOYDALANUVCHISI UCHUN ISHLAYDI ----

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

# Xizmatlarni kutish
[ "$DATABASE" = "postgres" ] && wait_for_db
wait_for_redis

# Migratsiyalar faqat web server uchun
if [[ "$*" == *"gunicorn"* ]] || [[ "$*" == *"runserver"* ]] || [[ "$*" == *"manage.py"* ]]; then
    run_migrations
fi

log "Starting command: $*"
exec "$@"