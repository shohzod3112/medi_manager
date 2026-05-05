#!/bin/bash
set -e

# 1. Funksiyalarni ta'riflash [cite: 53, 54, 335]
log(){ echo "[INSTALL] $1" | tee -a "$LOG_FILE"; }
fail(){ echo "❌ $1"; exit 1; }

# 2. O'zgaruvchilar [cite: 53]
PROJECT_ROOT="$(pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
LICENCE_DIR="/opt/media-manager/licence"
LOG_FILE="$PROJECT_ROOT/install.log"
DIST_DIR="$PROJECT_ROOT/dist"

log "Starting installation"

# 3. HWID generatsiyasi va dastlabki tekshiruvlar [cite: 57, 58]
mkdir -p "$LICENCE_DIR"
HWID=$(tr -d '\n' < /etc/machine-id | sha256sum | awk '{print $1}')
log "HWID: $HWID"

[ -f "$LICENCE_DIR/licence.json" ] || fail "licence.json missing in $LICENCE_DIR"

# 4. PyArmor o'rnatish va shifrlash [cite: 342, 356, 357]
log "Checking PyArmor..."
python3 -m pip install --upgrade pyarmor || fail "Pip not found. Run: sudo apt install python3-pip"

log "Encrypting code with PyArmor..."
# Modul sifatida chaqirish PATH muammosini hal qiladi [cite: 342, 344]
python3 -m pyarmor.cli gen -O "$DIST_DIR" -r apps core manage.py || fail "Encryption failed"

# 5. Konteynerlarni yuritish [cite: 59, 165]
log "Starting Docker build with encrypted code..."
sudo docker compose -f "$COMPOSE_FILE" up -d --build

# 6. Nginx 502 xatosini oldini olish uchun kutish [cite: 60, 321]
log "Waiting for backend HEALTHY..."
for i in {1..30}; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' media_manager_web 2>/dev/null || true)
  if [ "$STATUS" = "healthy" ]; then
    log "Backend is healthy!"
    # Nginx-ni yangi IP manzillarni olishi uchun restart qilamiz [cite: 322, 323]
    sudo docker compose restart nginx
    break
  fi
  sleep 2
done

[ "$STATUS" = "healthy" ] || fail "Backend not healthy"

# 7. Ochiq kodlarni tozalash [cite: 63, 114, 182]
log "Wiping source code from host..."
rm -rf apps core manage.py "$DIST_DIR"

log "DONE 🔒 Loyiha shifrlangan va muvaffaqiyatli o'rnatildi."