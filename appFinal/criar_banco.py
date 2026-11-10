"""Cria o banco 'apollo' no PostgreSQL local se ainda nao existir."""
import os, sys, psycopg
try:
    c = psycopg.connect(host=os.environ["POSTGRES_HOST"], port=os.environ["POSTGRES_PORT"],
                        user=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"],
                        dbname="postgres", autocommit=True, connect_timeout=5)
except Exception as e:
    print("\nNao consegui conectar no PostgreSQL (localhost:%s, usuario %s)." % (os.environ["POSTGRES_PORT"], os.environ["POSTGRES_USER"]))
    print("Confira: PostgreSQL instalado e rodando; senha correta em $env:POSTGRES_PASSWORD.")
    print("Detalhe:", str(e).strip().splitlines()[-1] if str(e).strip() else e)
    sys.exit(1)
nome = os.environ["POSTGRES_DB"]
if not c.execute("select 1 from pg_database where datname=%s", (nome,)).fetchone():
    c.execute(f'create database "{nome}"')
    print("Banco criado:", nome)
else:
    print("Banco ja existe:", nome)
