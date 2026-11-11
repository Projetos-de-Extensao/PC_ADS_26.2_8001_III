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
# Cria o superusuário só se as variáveis existirem e o usuário ainda não existir (idempotente)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  if python manage.py shell --no-imports -c "import os; from django.contrib.auth import get_user_model as g; raise SystemExit(0 if g().objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists() else 1)"; then
    echo "Superusuário '$DJANGO_SUPERUSER_USERNAME' já existe; nada a criar."
  else
    python manage.py createsuperuser --noinput --email "${DJANGO_SUPERUSER_EMAIL:-admin@apollo.local}" || true
  fi
fi
exec "$@"
