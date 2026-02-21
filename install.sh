#!/bin/bash

# 1. Licence tekshirish (siz allaqachon qo‘ygan)
if [ ! -f ./licence.json ]; then
    echo "Waiting for licence.json..."
    while [ ! -f ./licence.json ]; do sleep 2; done
fi
echo "Licence found, starting docker..."

# 2. Docker compose up
docker compose up -d

# Wait for web HEALTHY
until [ "$(docker inspect --format='{{.State.Status}}' media_manager_web)" == "running" ]; do
    echo "Waiting for web container to be running..."
    sleep 2
done

echo "Web container is healthy!"

# 4. Source backup
mkdir -p ./backups
tar -czf ./backups/source_backup_$(date +%F_%H-%M).tar.gz \
    apps core manage.py requirements.txt pyproject.toml
echo "Source archived!"

# 5. Source delete
rm -rf apps core manage.py requirements.txt pyproject.toml
echo "Source deleted!"

# Shu bilan skript tayyor
