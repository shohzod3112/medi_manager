# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root && \
    pip uninstall -y poetry

# Production stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only runtime dependencies (much smaller set)
RUN apt-get update && apt-get install -y \
    # Core libraries
    libpq5 \
    libffi8 \
    libssl3 \
    # Image processing (if needed)
    libjpeg62-turbo \
    libpng16-16 \
    libwebp7 \
    # Utilities
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the project
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod +x /app/entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/static /app/media /tmp && \
    chown -R app:app /app/static /app/media /tmp && \
    chmod -R 755 /app/static /app/media

USER app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]