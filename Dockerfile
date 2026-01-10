# 🔹 Builder stage
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root && \
    pip uninstall -y poetry

# 🔹 Production stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libffi8 \
    libssl3 \
    libjpeg62-turbo \
    libpng16-16 \
    libwebp7 \
    curl \
    ffmpeg \
    netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY . .

# Create non-root user and set permissions
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod +x /app/entrypoint.sh

RUN mkdir -p /app/static /app/staticfiles /app/media /app/logs /app/frontend /app/frontend/templates /app/frontend/static /tmp && \
    chown -R app:app /app/static /app/staticfiles /app/media /app/logs /app/frontend /app/frontend/templates /app/frontend/static /tmp && \
    chmod -R 755 /app/static /app/staticfiles /app/media

USER app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# 🔹 Single entrypoint
# ENTRYPOINT shuningdek CMD ni ham boshqaradi
ENTRYPOINT ["/app/entrypoint.sh"]

# CMD ni docker-compose da override qilamiz:
# web: "python manage.py runserver 0.0.0.0:8000"
# worker: "celery -A core worker --loglevel=INFO"
# beat: "celery -A core beat --loglevel=INFO"
