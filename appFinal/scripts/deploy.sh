#!/bin/sh
# Uso na EC2: ./scripts/deploy.sh [tag]   (sem tag = main atualizada)
set -e
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "ERRO: .env ausente"; exit 1; }
mkdir -p backups
echo ">> backup pré-deploy"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "backups/pre_deploy_$(date +%Y%m%d_%H%M%S).sql.gz" || echo "(sem banco ativo; seguindo)"
echo ">> atualizando código"
git fetch --tags && { [ -n "$1" ] && git checkout "$1" || git pull; }
echo ">> build e subida"
docker compose up -d --build
echo ">> verificando saúde"
for i in $(seq 1 30); do
  curl -fs http://localhost:8000/health/ >/dev/null && { echo "OK: aplicação saudável"; exit 0; }
  sleep 2
done
echo "FALHA: /health/ não respondeu. Rollback: ./scripts/deploy.sh <tag-anterior>"; exit 1
