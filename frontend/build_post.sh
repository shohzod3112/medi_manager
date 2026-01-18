#!/bin/sh
set -e

SRC="$FRONTEND_DIR/index.html"
DST="/app/frontend/templates/index.html"

mkdir -p /app/frontend/templates

if [ -f "$SRC" ]; then
    cp "$SRC" "$DST"
    echo "✔ frontend/static/index.html → frontend/templates/index.html"
else
    echo "❌ index.html topilmadi: $SRC"
fi
