#!/bin/bash
set -e

log() { echo "[$(date +'%H:%M:%S')] [ENTRYPOINT] $1"; }
error() { echo "ERROR: $1" >&2; exit 1; }

# 1. Litsenziyani tekshirish
log "Checking licence before starting..."
python3 /app/core/check_licence.py || { log "❌ Licence invalid, exiting"; exit 1; }
log "✅ Licence valid"

# 2. Ruxsatlarni to'g'rilash (Faqat root bo'lsa)
if [ "$(id -u)" = "0" ]; then
    log "Fixing permissions..."
    mkdir -p /app/media /app/static /app/staticfiles /app/logs /tmp
    chown -R app:app /app/media /app/static /app/staticfiles /app/logs /tmp
fi

# 3. Bazani kutish funksiyasi
wait_for_db() {
    log "Waiting for database ($DB_HOST:$DB_PORT)..."
    timeout 60 bash -c "until nc -z $DB_HOST $DB_PORT; do sleep 1; done" || error "Database timeout"
}

wait_for_redis() {
    log "Waiting for Redis..."
    timeout 30 bash -c "until nc -z redis 6379; do sleep 1; done" || error "Redis timeout"
}

# 4. Servislarni kutish
[ "$DATABASE" = "postgres" ] && wait_for_db
wait_for_redis

# 5. Migratsiya va Static yig'ish (Faqat web server ishga tushayotganda)
if [[ "$*" == *"manage.py"* ]] || [[ "$*" == *"gunicorn"* ]] || [[ "$*" == *"runserver"* ]]; then
    log "Running migrations..."
    python3 manage.py migrate --noinput || error "Migration failed"
    log "Collecting static files..."
    python3 manage.py collectstatic --noinput || log "Static collection failed (continuing)"
fi

# 6. Cron xizmatini yoqish (Agar kerak bo'lsa)
# Eslatma: 'service cron start' root huquqini talab qiladi
if [ "$(id -u)" = "0" ]; then
    service cron start || log "Cron start failed"
fi

log "Starting command: $*"

# 7. ASOSIY JARAYONNI BOSHLASH
# Bu yerda "$@" Dockerfile dagi CMD ni qabul qilib oladi
exec "$@"