# =========================
# BUILDER STAGE
# =========================
FROM python:3.11-slim AS builder

WORKDIR /app

# Build uchun paketlar
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev libffi-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --only main --no-root

# =========================
# RUNTIME STAGE
# =========================
FROM python:3.11-slim

WORKDIR /app

# ... (paketlarni o'rnatish qismi o'zgarishsiz qoladi)

# Builder’dan python paketlarni ko‘chiramiz
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# LOYIHA FAYLLARI (O'zgarish: install.sh yaratgan dist/ papkasidan olamiz)
# Bu yerda . (root) emas, shifrlangan kod nusxalanadi
COPY dist/ .

# Static va media papkalarni yaratish
RUN mkdir -p /app/static /app/staticfiles /app/media /app/core /app/apps \
 && chown -R root:root /app

# Entrypoint script (shifrlangan kod ichida bo'ladi)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]