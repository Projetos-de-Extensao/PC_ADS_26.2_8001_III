#!/bin/sh
# Gera o .env de produção com segredos aleatórios. Roda NA EC2; nada é impresso nem vai para o Git.
# Uso: ./scripts/gerar_env.sh <IP_PUBLICO_ou_dominio>
set -e
cd "$(dirname "$0")/.."
[ -n "$1" ] || { echo "Uso: $0 <IP_PUBLICO_ou_dominio>"; exit 1; }
[ ! -e .env ] || { echo "ERRO: .env já existe (não sobrescrevo). Apague-o de propósito se quiser gerar outro."; exit 1; }
gerar() { openssl rand -hex "$1"; }
umask 077
cat > .env <<EOF
POSTGRES_DB=apollo
POSTGRES_USER=apollo
POSTGRES_PASSWORD=$(gerar 24)
SECRET_KEY=$(gerar 40)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$1
CSRF_TRUSTED_ORIGINS=
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=$(gerar 12)
DJANGO_SUPERUSER_EMAIL=admin@apollo.local
EOF
chmod 600 .env
echo ".env criado (permissão 600). Para ver a senha do /admin, só você, no terminal:  grep DJANGO_SUPERUSER_PASSWORD .env"
