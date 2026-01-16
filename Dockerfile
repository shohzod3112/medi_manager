# -------------------
# 🔹 Builder stage
# -------------------
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

WORKDIR /app

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# -------------------
# 🔹 Production stage
# -------------------
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

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Make frontend build script executable if exists
RUN if [ -f /app/frontend/build_post.sh ]; then chmod +x /app/frontend/build_post.sh && /app/frontend/build_post.sh; fi

USER app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run server directly
CMD ["python3", "manage.py", "runsslserver", "--certificate", "./localhost+2.pem", "--key", "./localhost+2-key.pem", "0.0.0.0:8000"]
