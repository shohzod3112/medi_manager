#!/bin/bash
set -e

PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"
LICENCE_DIR="/opt/media-manager/licence"
DIST_DIR="$PROJECT_ROOT/dist" # Shifrlangan kod papkasi [cite: 176, 265]

LOG_FILE="$PROJECT_ROOT/install.log"

log(){ echo "[INSTALL] $1" | tee -a "$LOG_FILE"; }
fail(){ echo "❌ $1"; exit 1; }

log "Starting installation"

# Kerakli dasturlarni tekshirish
command -v docker >/dev/null || fail "docker not found"
command -v docker >/dev/null && docker compose version >/dev/null || fail "docker compose missing"
command -v python3 >/dev/null || fail "python3 missing"
command -v 7z >/dev/null || fail "7z missing"
command -v poetry >/dev/null || fail "poetry missing. Run: curl -sSL https://install.python-poetry.org | python3 -"

mkdir -p "$LICENCE_DIR"
chmod 755 "$LICENCE_DIR"

log "Generating HWID"
HWID=$(tr -d '\n' < /etc/machine-id | sha256sum | awk '{print $1}')
echo "HWID: $HWID" [cite: 57, 207, 387]

echo "👉 Generate licence.json on DEV machine"
echo "👉 Copy to $LICENCE_DIR/licence.json"
read -p "Press ENTER when ready..."

[ -f "$LICENCE_DIR/licence.json" ] || fail "licence.json missing" [cite: 58, 208]

echo "🔍 Checking licence..."
python3 core/check_licence.py || {
  echo "❌ Licence invalid. Build to‘xtatildi."
  exit 1
} [cite: 58, 194, 209]

# --- SHIFRLASH BOSQICHI ---
log "Encrypting source code with PyArmor via Poetry..." [cite: 112, 180, 220, 283]
# PyArmor-ni loyihaga qo'shish va shifrlangan 'dist' papkasini yaratish
poetry add --group dev pyarmor || fail "Poetry failed to add PyArmor" [cite: 232, 410, 424]
rm -rf "$DIST_DIR"
poetry run pyarmor gen -O "$DIST_DIR" -r apps core manage.py || fail "Encryption failed" [cite: 164, 357, 389, 416]
[ -d "$DIST_DIR" ] || fail "dist directory was not created!" [cite: 422, 430]
# --------------------------

log "Starting containers"
sudo docker compose -f "$COMPOSE_FILE" up -d --build [cite: 59, 167, 181, 285]

log "Waiting for backend HEALTHY"
for i in {1..30}; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' media_manager_web 2>/dev/null || true)

  echo "Attempt $i - Health: $STATUS" [cite: 60, 211]

  if [ "$STATUS" = "healthy" ]; then
    echo "Backend is healthy!"
    # Nginx 502 Bad Gateway xatosini bartaraf etish [cite: 315, 330, 347]
    log "Refreshing Nginx connections to fix 502 error..."
    sudo docker compose restart nginx [cite: 322, 333, 408]
    break
  fi

  sleep 2
done

[ "$STATUS" = "healthy" ] || fail "Backend not healthy" [cite: 61, 212]

log "Archiving source"
PROTECTED="$PROJECT_ROOT/protected"
ARCHIVE="$PROJECT_ROOT/protected.7z"
PASS="MediaManager@123"

mkdir -p "$PROTECTED"
cp -r apps core manage.py core/check_licence.py "$PROTECTED/" [cite: 62, 213]
cp -r "$LICENCE_DIR" "$PROTECTED/licence"

7z a -t7z "$ARCHIVE" "$PROTECTED/*" -p"$PASS" -mhe=on >/dev/null [cite: 63, 213]

log "Wiping source"
# Asl kodlarni va vaqtinchalik 'dist' papkasini o'chirish [cite: 114, 156, 182, 447]
rm -rf apps core manage.py core/check_licence.py attachment "$DIST_DIR" [cite: 63, 114, 156, 213, 286]

log "DONE 🔒"
echo "Archive: protected.7z"
echo "Password: $PASS"