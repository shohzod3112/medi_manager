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

# Root ostida papkalarni yaratish va huquq berish
RUN mkdir -p /app/static /app/staticfiles /app/media /tmp \
 && chown -R app:app /app


USER app

# Entrypoint scriptni ishga tushirish
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
