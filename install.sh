#!/bin/bash
set -e

# 1. Funksiyalarni ta'riflash
log(){ echo "[INSTALL] $1" | tee -a "$LOG_FILE"; }
fail(){ echo "❌ $1"; exit 1; }

# 2. O'zgaruvchilarni belgilash
PROJECT_ROOT="$(pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
LICENCE_DIR="/opt/media-manager/licence"
LOG_FILE="$PROJECT_ROOT/install.log"
DIST_DIR="$PROJECT_ROOT/dist"

log "Starting installation (Poetry + PyArmor mode)"

# 3. HWID generatsiyasi
mkdir -p "$LICENCE_DIR"
HWID=$(tr -d '\n' < /etc/machine-id | sha256sum | awk '{print $1}')
log "HWID: $HWID"

# Litsenziya fayli borligini tekshirish
[ -f "$LICENCE_DIR/licence.json" ] || fail "licence.json missing in $LICENCE_DIR"

# 4. PyArmor-ni Poetry orqali o'rnatish va shifrlash
log "Checking PyArmor via Poetry..."
# PyArmor-ni dev-group ga qo'shish (agar yo'q bo'lsa)
poetry add --group dev pyarmor || fail "Poetry failed to add PyArmor"

log "Encrypting source code with PyArmor..."
# Virtual muhit ichida shifrlashni amalga oshirish
poetry run pyarmor gen -O "$DIST_DIR" -r apps core manage.py || fail "Encryption failed"

# 5. Docker Build jarayonini boshlash
log "Starting Docker build (using encrypted code from $DIST_DIR)..."
# Dockerfile'da 'COPY dist/ .' qatori bo'lishi shart
sudo docker compose -f "$COMPOSE_FILE" up -d --build

# 6. Backend sog'lomligini va Nginx holatini tekshirish
log "Waiting for backend to become HEALTHY..."
for i in {1..30}; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' media_manager_web 2>/dev/null || true)
  if [ "$STATUS" = "healthy" ]; then
    log "Backend is healthy! Restarting Nginx to fix 502 Bad Gateway..."
    sudo docker compose restart nginx [cite: 323, 372]
    break
  fi
  sleep 2
done

[ "$STATUS" = "healthy" ] || fail "Backend not healthy after 60 seconds"

# 7. Xavfsizlik: Ochiq kodlarni va vaqtinchalik 'dist' papkasini o'chirish
log "Wiping open source code and temporary files from host..."
# Faqat shifrlangan kod Docker Image ichida qoladi
rm -rf apps core manage.py "$DIST_DIR" [cite: 182, 359, 372]

log "DONE 🔒 Loyiha shifrlangan va muvaffaqiyatli o'rnatildi."