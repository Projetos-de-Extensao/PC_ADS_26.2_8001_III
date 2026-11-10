#!/bin/sh
# Backup diário (cron):  0 3 * * * /home/ubuntu/apollo/scripts/backup.sh
set -e
cd "$(dirname "$0")/.."
mkdir -p backups
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "backups/apollo_$(date +%Y%m%d).sql.gz"
find backups -name 'apollo_*.sql.gz' -mtime +7 -delete
