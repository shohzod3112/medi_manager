#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Function to wait for database with timeout
wait_for_db() {
    log "Waiting for database at $DB_HOST:$DB_PORT..."
    local timeout=60
    local count=0
    
    while ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
        sleep 1
        count=$((count + 1))
        if [ $count -ge $timeout ]; then
            error "Database connection timeout after ${timeout}s"
        fi
    done
    log "Database is ready!"
}

# Function to wait for Redis with timeout
wait_for_redis() {
    log "Waiting for Redis..."
    local timeout=30
    local count=0
    
    while ! nc -z redis 6379 2>/dev/null; do
        sleep 1
        count=$((count + 1))
        if [ $count -ge $timeout ]; then
            error "Redis connection timeout after ${timeout}s"
        fi
    done
    log "Redis is ready!"
}

# Function to run Django management command with error handling
run_django_command() {
    local cmd="$1"
    local description="$2"
    
    log "Running: $description"
    if ! python manage.py $cmd; then
        error "Failed to run: $description"
    fi
    log "Completed: $description"
}

# Function to check if migrations are needed
check_migrations() {
    log "Checking if migrations are needed..."
    if python manage.py showmigrations --list | grep -q "\[ \]"; then
        return 0  # Migrations needed
    else
        return 1  # No migrations needed
    fi
}

# Function to run migrations with lock
run_migrations_with_lock() {
    log "Checking for migration lock..."
    local lock_file="/tmp/django_migrations.lock"
    local max_wait=300  # 5 minutes max wait
    
    # Wait for lock to be released
    local wait_count=0
    while [ -f "$lock_file" ] && [ $wait_count -lt $max_wait ]; do
        log "Waiting for migration lock to be released... ($wait_count/$max_wait)"
        sleep 5
        wait_count=$((wait_count + 5))
    done
    
    if [ -f "$lock_file" ]; then
        error "Migration lock timeout after ${max_wait}s"
    fi
    
    # Create lock file
    echo $$ > "$lock_file"
    log "Acquired migration lock"
    
    # Check if migrations are needed
    if check_migrations; then
        log "Migrations needed, running them..."
        run_django_command "migrate --noinput" "Database migrations"
    else
        log "No migrations needed"
    fi
    
    # Remove lock file
    rm -f "$lock_file"
    log "Released migration lock"
}

# Function to collect static files with proper permissions
collect_static_files() {
    log "Collecting static files..."
    
    # Create static directory if it doesn't exist
    mkdir -p /app/static
    
    # Set proper permissions
    chmod -R 755 /app/static
    
    # Run collectstatic
    if ! python manage.py collectstatic --noinput; then
        warn "Static files collection failed, but continuing..."
    else
        log "Static files collected successfully"
    fi
}

# Function to check for superuser (only after migrations)
check_superuser() {
    log "Checking for superuser..."
    # Only check if django_migrations table exists
    if python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"SELECT to_regclass('django_migrations')\")
    result = cursor.fetchone()
    if result[0]:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            print('No superuser found. Create one with: python manage.py createsuperuser')
        else:
            print('Superuser exists')
    else:
        print('Database not migrated yet')
" 2>/dev/null; then
        log "Superuser check completed"
    else
        warn "Could not check superuser status"
    fi
}

# Main execution
log "Starting application initialization..."

# Wait for services if database is postgres
if [ "$DATABASE" = "postgres" ]; then
    wait_for_db
fi

wait_for_redis

# Only run migrations if this is the web container
if [ "$1" = "python" ] && [[ "$2" == *"manage.py"* ]] && [[ "$2" == *"runserver"* ]]; then
    run_migrations_with_lock
    collect_static_files
    check_superuser
fi

log "Application initialization completed successfully!"
log "Starting application with command: $*"

# Execute the main command
exec "$@"