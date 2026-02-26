#!/bin/bash
set -e

PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"
LICENCE_DIR="/opt/media-manager/licence"
LOG_FILE="$PROJECT_ROOT/install.log"

log(){ echo "[INSTALL] $1" | tee -a "$LOG_FILE"; }
fail(){ echo "❌ $1"; exit 1; }

log "Starting installation"

command -v docker >/dev/null || fail "docker not found"
command -v docker >/dev/null && docker compose version >/dev/null || fail "docker compose missing"
command -v python3 >/dev/null || fail "python3 missing"
command -v 7z >/dev/null || fail "7z missing"

mkdir -p "$LICENCE_DIR"
chmod 755 "$LICENCE_DIR"

log "Generating HWID"
HWID=$(python3 "$BACKEND_DIR/hwid.py")
echo "HWID: $HWID"

echo "👉 Generate licence.json on DEV machine"
echo "👉 Copy to $LICENCE_DIR/licence.json"
read -p "Press ENTER when ready..."

[ -f "$LICENCE_DIR/licence.json" ] || fail "licence.json missing"

log "Starting containers"
docker compose -f "$COMPOSE_FILE" up -d --build

log "Waiting for backend HEALTHY"
for i in {1..30}; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' backend-web-1 2>/dev/null || true)
  [ "$STATUS" = "healthy" ] && break
  sleep 2
done

[ "$STATUS" = "healthy" ] || fail "Backend not healthy"

log "Archiving source"
PROTECTED="$PROJECT_ROOT/protected"
ARCHIVE="$PROJECT_ROOT/protected.7z"
PASS="MediaManager@123"

mkdir -p "$PROTECTED"
cp -r backend/apps backend/core backend/manage.py backend/hwid.py backend/check_licence.py "$PROTECTED/"
cp -r "$LICENCE_DIR" "$PROTECTED/licence"

7z a -t7z "$ARCHIVE" "$PROTECTED/*" -p"$PASS" -mhe=on >/dev/null

log "Wiping source"
rm -rf backend/apps backend/core backend/manage.py backend/hwid.py backend/check_licence.py

log "DONE 🔒"
echo "Archive: protected.7z"
echo "Password: $PASS"