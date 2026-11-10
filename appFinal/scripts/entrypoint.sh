#!/bin/sh
set -e
python manage.py migrate --noinput
# Dados reais do INEP (2016-2025) se o arquivo existir; senão, seed sintético
if [ -f data/itens_inep_2016_2025.csv ]; then
  python manage.py importar_inep data/itens_inep_2016_2025.csv
else
  python manage.py seed_enem
fi
python manage.py collectstatic --noinput -v0
# Cria o superusuário só se as variáveis existirem (idempotente)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput --email "${DJANGO_SUPERUSER_EMAIL:-admin@apollo.local}" || true
fi
exec "$@"
