#!/bin/bash
set -e

PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"
LICENCE_DIR="/opt/media-manager/licence"
DIST_DIR="$PROJECT_ROOT/dist"

LOG_FILE="$PROJECT_ROOT/install.log"

log(){ echo "[INSTALL] $1" | tee -a "$LOG_FILE"; }
fail(){ echo "❌ $1"; exit 1; }

log "Starting installation"

# 1. Kerakli papkalarni yaratish
mkdir -p "$LICENCE_DIR"
chmod 755 "$LICENCE_DIR"

# 2. HWID generatsiyasi
log "Generating HWID"
HWID=$(tr -d '\n' < /etc/machine-id | sha256sum | awk '{print $1}')
echo "HWID: $HWID"

echo "👉 Generate licence.json on DEV machine"
echo "👉 Copy to $LICENCE_DIR/licence.json"
read -p "Press ENTER when ready..."

# 3. Litsenziyani tekshirish
[ -f "$LICENCE_DIR/licence.json" ] || fail "licence.json missing"

log "🔍 Checking licence..."
python3 core/check_licence.py || {
  echo "❌ Licence invalid. Build to'xtatildi."
  exit 1
}

# install.sh ichidagi Poetry qismini shunday o'zgartiring:
log "Checking Poetry..."
if ! command -v poetry &> /dev/null; then
    log "Poetry topilmadi. O'rnatish boshlanmoqda..."
    # Rasmiy o'rnatish skriptini yurgizamiz
    curl -sSL https://install.python-poetry.org | python3 - || fail "Poetry o'rnatib bo'lmadi"

    # PATH (yo'l)ni yangilaymiz, shunda terminal yangi buyruqni ko'radi
    export PATH="$HOME/.local/bin:$PATH"

    # Doimiy ishlashi uchun ~/.bashrc ga ham qo'shib qo'yamiz (ixtiyoriy)
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
    log "Poetry muvaffaqiyatli o'rnatildi."
else
    log "Poetry allaqachon mavjud."
fi

# Endi shifrlashni boshlasak bo'ladi
log "Encrypting source code with PyArmor via Poetry..."
# Shifrlashdan oldin bog'liqliklarni yangilaymiz
poetry install || fail "Poetry install failed"
# ... (qolgan pyarmor gen buyruqlari)

# 4. PyArmor va Poetry tekshiruvi (Tizim darajasida)
log "Checking Poetry..."
# Agar poetry buyrug'i topilmasa, uni o'rnatish haqida xabar beradi
command -v poetry >/dev/null || fail "Poetry topilmadi. Uni o'rnating: curl -sSL https://install.python-poetry.org | python3 -"

# --- SHIFRLASH BOSQICHI ---
log "Encrypting source code with PyArmor..."
# 'dist' papkasini tozalab, yangidan shifrlaymiz
rm -rf "$DIST_DIR"

# 'gen' buyrug'i bilan butun loyihani shifrlaymiz
# PyArmor avtomatik ravishda runtime papkasini ham 'dist' ichiga yaratadi
poetry run python -m pyarmor.cli gen -O "$DIST_DIR" -r apps core attachment manage.py || fail "Encryption failed"

# Tekshiruv: Runtime papkasi yaratildimi?
if ls "$DIST_DIR"/pyarmor_runtime_* 1> /dev/null 2>&1; then
    log "PyArmor Runtime created."
else
    fail "PyArmor Runtime missing! Check your pyarmor installation."
fi
# --------------------------

# 5. Konteynerlarni ishga tushirish
log "Starting containers"
sudo docker compose -f "$COMPOSE_FILE" up -d --build

# 6. Nginx 502 xatosini bartaraf etish (Healthy holatni kutish)
log "Waiting for backend HEALTHY"
for i in {1..30}; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' media_manager_web 2>/dev/null || true)

  echo "Attempt $i - Health: $STATUS"

  if [ "$STATUS" = "healthy" ]; then
    echo "Backend is healthy!"
    log "Refreshing Nginx connections to fix 502 error..."
    sudo docker compose restart nginx
    break
  fi

  sleep 2
done

[ "$STATUS" = "healthy" ] || fail "Backend not healthy"

# 7. Manba kodini arxivlash va tozalash
log "Archiving source"
PROTECTED="$PROJECT_ROOT/protected"
ARCHIVE="$PROJECT_ROOT/protected.7z"
PASS="MediaManager@123"

mkdir -p "$PROTECTED"
cp -r apps core manage.py core/check_licence.py "$PROTECTED/"
cp -r "$LICENCE_DIR" "$PROTECTED/licence"

7z a -t7z "$ARCHIVE" "$PROTECTED/*" -p"$PASS" -mhe=on >/dev/null

log "Wiping source"
# Host serverdan ochiq kodlarni va vaqtinchalik dist papkasini o'chirish
rm -rf apps core manage.py core/check_licence.py attachment "$DIST_DIR"

log "DONE 🔒"
echo "Archive: protected.7z"
echo "Password: $PASS"