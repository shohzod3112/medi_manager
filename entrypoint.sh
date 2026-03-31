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

## Create superuser if it doesn't exist
#create_superuser() {
#    log "Checking for superuser..."
#
#    # Set default values if environment variables are not set
#    export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-shosh}
#    export DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-shoh@example.com}
#    export DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-SuperSecretP@ss123$}
#
#    # Temporarily disable exit on error for this function
#    set +e
#
#    # Check if superuser already exists
#    check_result=$(python manage.py shell -c "
#  from django.contrib.auth import get_user_model
#  User = get_user_model()
#  try:
#      user = User.objects.get(username='$DJANGO_SUPERUSER_USERNAME')
#      print('EXISTS')
#  except User.DoesNotExist:
#      print('NOT_EXISTS')
#  except Exception as e:
#      print('ERROR')
#  " 2>/dev/null)
#
#    # Re-enable exit on error
#    set -e
#
#    case "$check_result" in
#        "EXISTS")
#            log "Superuser '$DJANGO_SUPERUSER_USERNAME' already exists, skipping creation"
#            ;;
#        "NOT_EXISTS")
#            log "Creating superuser '$DJANGO_SUPERUSER_USERNAME'..."
#            # Temporarily disable exit on error for superuser creation
#            set +e
#            python manage.py createsuperuser --noinput 2>/dev/null
#            create_exit_code=$?
#            set -e
#
#            if [ $create_exit_code -eq 0 ]; then
#                log "Superuser created successfully"
#            else
#                log "Superuser creation failed (continuing anyway)"
#            fi
#            ;;
#        *)
#            log "Could not determine superuser status, attempting to create..."
#            set +e
#            python manage.py createsuperuser --noinput 2>/dev/null
#            create_exit_code=$?
#            set -e
#
#            if [ $create_exit_code -eq 0 ]; then
#                log "Superuser created successfully"
#            else
#                log "Superuser creation failed (continuing anyway)"
#            fi
#            ;;
#    esac
#}

# Run migrations (simple approach)
run_migrations() {
    log "Running migrations..."
    python manage.py migrate --noinput || error "Migration failed"

    log "Collecting static files..."
    python manage.py collectstatic --noinput || log "Static collection failed (continuing)"

    # Create superuser after migrations
    create_superuser
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
exec "$@"