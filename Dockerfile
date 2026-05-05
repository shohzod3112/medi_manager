# =========================
# BUILDER STAGE
# =========================
FROM python:3.12-slim AS builder

WORKDIR /app

# Build uchun paketlar
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev netcat-openbsd libffi-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --only main --no-root

# =========================
# RUNTIME STAGE
# =========================
FROM python:3.12-slim

WORKDIR /app

# SIZDA YO'Q BO'LGAN VA QO'SHISH KERAK BO'LGAN QISM:
# Bu yerda 'netcat-openbsd' aynan 'nc' buyrug'ini ta'minlaydi
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Builder’dan python paketlarni ko‘chiramiz (3.12 versiya ekanligiga e'tibor bering)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# LOYIHA FAYLLARI: Shifrlangan kodni /app/ papkasiga olamiz
COPY dist/ /app/

# Qolgan foydalanuvchi va sozlash ishlari
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/static /app/staticfiles /app/media /opt/media-manager/licence && \
    chown -R app:app /app /opt/media-manager/licence

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]