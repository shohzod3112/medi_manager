# 1. Build
docker compose build

# 2. Run
docker compose up -d

# 3. Backup
mkdir -p /opt/backups
tar -czf /opt/backups/source_$(date +%F_%H-%M).tar.gz .

# 4. Delete source (compose va envdan tashqari)
find . -mindepth 1 -maxdepth 1 \
! -name docker-compose.yml \
! -name .env \
! -name licence.json \
-exec rm -rf {} +