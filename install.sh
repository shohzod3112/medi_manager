#!/bin/bash
set -e

HWID=$(cat /etc/machine-id | sha256sum | awk '{print $1}')
echo "Server HWID: $HWID"

# Licence kutish
while [ ! -f ./licence.json ]; do
    echo "Waiting for licence.json..."
    sleep 2
done

echo "Licence found, starting docker..."
docker compose -f docker-compose.yml up -d

# Wait for web HEALTHY
until [ "$(docker inspect --format='{{.State.Health.Status}}' media-manager-web)" == "healthy" ]; do
    echo "Waiting for web container..."
    sleep 2
done

echo "Web container is healthy!"

# Source code backup
tar -czf source_backup.tar.gz backend/
rm -rf backend/*
echo "Source archived and deleted!"
