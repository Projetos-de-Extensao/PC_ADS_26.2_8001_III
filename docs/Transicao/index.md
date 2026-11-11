# Transição

**Objetivo:** colocar o Apollo em produção na AWS e garantir que ele possa ser atualizado e recuperado.

## Resumo da fase

O Apollo roda numa EC2 t3.small com Docker Compose. A estratégia escolhida é **Recreate/Rolling simples**: alteração no Windows → `git push` → `./scripts/deploy.sh` na EC2 (backup `pg_dump`, `git pull`, `docker compose up -d --build`, checagem de `/health/`). O rollback volta para a *tag* anterior com o mesmo script. Blue-Green e Canary foram avaliadas e ficaram como evolução por custo.

## Documentos da fase

| **Documento** | **Conteúdo** | **Link** |
| --- | --- | --- |
| Atividades de Deploy | Estratégias avaliadas, a escolhida, diagrama de atividades, tempo, custo e plano de rollback | [ativ_deploy](ativ_deploy.md) |

## Evidências

Prints de `docker ps`, logs, acesso pelo IP público, `psql` e persistência estão no [README do repositório](https://github.com/Projetos-de-Extensao/PC_ADS_26.2_8001_III#evid%C3%AAncias-do-deploy-b8).
