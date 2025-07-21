FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libgif-dev \
    libwebp-dev \
    libtiff-dev \
    libopenjp2-7-dev \
    liblcms2-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libavutil-dev \
    libavfilter-dev \
    libavdevice-dev \
    libpostproc-dev \
    libswresample-dev \
    libx264-dev \
    libx265-dev \
    libvpx-dev \
    libmp3lame-dev \
    libopus-dev \
    libvorbis-dev \
    libtheora-dev \
    libass-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root && \
    pip uninstall -y poetry

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

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]