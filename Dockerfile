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

# Runtime paketlar
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ffmpeg libpq5 libffi8 libssl3 libjpeg62-turbo libpng16-16 libwebp7 netcat-openbsd \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Builder’dan python paketlarni ko‘chiramiz
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Loyiha fayllari
COPY . .

# App user
RUN useradd --create-home --shell /bin/bash app

# Papkalarni yaratish (build vaqtida)
RUN mkdir -p /app/static /app/staticfiles /app/media \
 && chown -R app:app /app

#USER app

# Entrypoint script
# Entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Cron job faylini qo‘shish
COPY licence_cron /etc/cron.d/licence_cron
RUN chmod 644 /etc/cron.d/licence_cron && crontab /etc/cron.d/licence_cron

# Cron va gunicorn ishga tushadi
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
