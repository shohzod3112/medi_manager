# =========================
# BUILDER STAGE
# =========================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Build uchun kerakli paketlar
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Poetry o‘rnatamiz
COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --only main --no-root

# =========================
# RUNTIME STAGE
# =========================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime uchun kerakli kutubxonalar
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    libpq5 \
    libffi8 \
    libssl3 \
    libjpeg62-turbo \
    libpng16-16 \
    libwebp7 \
    netcat-openbsd \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Builder’dan python paketlarni ko‘chiramiz
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Loyiha fayllari
COPY . .

# User
RUN useradd --create-home --shell /bin/bash app \
 && chown -R app:app /app

USER app

# Papkalar
RUN mkdir -p /app/static /app/staticfiles /app/media /app/logs /tmp /app/frontend/static /app/frontend/templates

# Frontend scriptini ishga tushirish
RUN if [ -f frontend/build_post.sh ]; then \
        chmod +x frontend/build_post.sh && ./frontend/build_post.sh; \
    fi

# Default command (web uchun)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
