# Construção

**Objetivo:** implementar a API definida na Elaboração e empacotá-la em contêineres.

## Resumo da fase

A aplicação (`appFinal/`) é uma API Django + DRF com PostgreSQL 16 multimodelo:

* **Relacional:** `EdicaoEnem`, `Questao`, `Aluno`, `Submissao`, `RespostaInformada` (tabela associativa N—N entre `Submissao` e `Questao`) e `Resultado`.
* **Documento:** `Questao.atributos` em JSONB com índice GIN, filtrável por `?atributos__habilidade=H12`; `Resultado.analise` em JSONB.
* **Transação:** o envio da prova grava `Submissao`, 45 respostas e `Resultado` em `transaction.atomic()`, com rollback em prova inválida.
* **Empacotamento:** `Dockerfile` (Python 3.12 + Gunicorn) e `docker-compose.yml` com `web` e `db`, volume `pgdata` e `healthcheck`.
* **Qualidade:** testes automatizados (`python manage.py test`) e importação automática das 7.400 questões do INEP ao subir.

## Artefatos

| **Artefato** | **Link** |
| --- | --- |
| Documentação da aplicação | [Aplicação (appFinal)](aplicacao.md) |
| Código-fonte | [`appFinal/` no GitHub](https://github.com/Projetos-de-Extensao/PC_ADS_26.2_8001_III/tree/main/appFinal) |

## Próxima fase

[Transição](../Transicao/index.md): estratégia de deploy, rollback e custo.
