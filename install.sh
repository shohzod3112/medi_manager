#!/bin/bash
set -e

# ... (avvalgi o'zgaruvchilar)

log "Step 1: Pulling latest code"
git pull origin main

log "Step 2: Encrypting with PyArmor"
# PyArmor butun loyihani shifrlaydi va dist/ papkasiga joylaydi
pip install pyarmor
pyarmor gen -O dist -r apps core manage.py

log "Step 3: Docker Build (using encrypted code)"
sudo docker compose up -d --build

log "Step 4: Wiping source and dist"
# Host serverda ochiq kod qolmasligi uchun
rm -rf apps core manage.py dist
# check_licence.py ham o'chiriladi, chunki u shifrlangan holda image ichida

log "DONE 🔒 Loyiha shifrlangan va himoyalangan."