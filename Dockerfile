FROM python:3.9-alpine

RUN mkdir /app

# Set work directory
WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

# Install required system dependencies

RUN apk --no-cache add \
    gcc \
    musl-dev \
    linux-headers \
    python3-dev \
    libffi-dev \
    postgresql-dev \
    icu-dev \
    gettext \
    libpq-dev \
    glib-dev \
    poppler-glib \
    vips-dev \
    vips-tools \
    poppler-utils \
    ffmpeg

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the project
COPY . .

# Install netcat
RUN apk add --no-cache netcat-openbsd

# Make entrypoint.sh executable
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
# Expose the port the application runs on
EXPOSE 8000
