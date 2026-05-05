#!/bin/bash
set -e

# 1. Avval funksiyalarni ta'riflang
log(){ echo "[INSTALL] $1" | tee -a "$LOG_FILE"; }
fail(){ echo "❌ $1"; exit 1; }

# 2. Keyin o'zgaruvchilarni belgilang [cite: 53]
PROJECT_ROOT="$(pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
LICENCE_DIR="/opt/media-manager/licence"
LOG_FILE="$PROJECT_ROOT/install.log"
DIST_DIR="$PROJECT_ROOT/dist"

log "Starting installation"

# ... (HWID generatsiyasi va litsenziya tekshiruvi) [cite: 57, 58]

# 3. PyArmor bilan shifrlash (Agar hali qo'shmagan bo'lsangiz) [cite: 164, 180]
log "Encrypting code with PyArmor..."
pyarmor gen -O "$DIST_DIR" -r apps core manage.py

# 4. Konteynerlarni yuritish [cite: 59, 167]
sudo docker compose -f "$COMPOSE_FILE" up -d --build

# 5. Nginx 502 xatosini oldini olish uchun sog'lomlikni tekshirish [cite: 60, 321]
log "Waiting for backend HEALTHY"
for i in {1..30}; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' media_manager_web 2>/dev/null || true)
  if [ "$STATUS" = "healthy" ]; then
    log "Backend is healthy! Refreshing Nginx..."
    sudo docker compose restart nginx # Nginx-ni qayta ishga tushirish [cite: 322, 323]
    break
  fi
  sleep 2
done

# 6. Ochiq kodlarni o'chirish [cite: 63, 114, 182]
log "Wiping source code"
rm -rf apps core manage.py "$DIST_DIR"
log "DONE 🔒"