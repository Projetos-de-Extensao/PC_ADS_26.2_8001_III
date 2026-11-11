# Elaboração

**Objetivo:** refinar os requisitos, resolver os riscos críticos e definir a arquitetura base do Apollo.

## Resumo da fase

Na Elaboração, a equipe definiu e documentou a arquitetura **Django + PostgreSQL em Docker Compose, executada em uma instância EC2**, com banco em volume persistente, segurança de rede mínima (somente 22, 80 e 8000), segredos fora do Git e deploy por `git pull` + `docker compose up -d --build`. A arquitetura serverless/RDS foi avaliada e mantida como evolução.

**Produto principal:** arquitetura validada e dimensionada, com rastreabilidade entre requisitos, casos de uso, pacotes de segurança e fluxos de interação.

## Documentos da fase

| **Documento** | **Conteúdo** | **Link** |
| --- | --- | --- |
| Requisitos Suplementares | RNF com critérios mensuráveis, decisão arquitetural, custo e restrições | [rs](../Iniciacao/rs.md) |
| Casos de Uso Arquiteturais | 7 casos de uso (EC2, rede, banco, aplicação, monitoramento, deploy, backup) com diagramas | [cua](cua.md) |
| Modelo de Análise — Segurança | 6 pacotes de segurança, matrizes e trade-offs | [maps](maps.md) |
| Dimensionamento de Computação | Instância EC2, *workers*, memória e custo | [dim_comp](dim_comp.md) |
| Dimensionamento de Banco de Dados | Docker × RDS, modelo de dados, backup, RPO/RTO | [dimrbd](dimrbd.md) |
| Diagramas de Sequência e Comunicação | 6 fluxos arquiteturais com matriz de rastreamento | [seq_com](seq_com.md) |

## Documentos relacionados

* Iniciação: [Documento de Visão](../Iniciacao/dv.md)
* Transição: [Atividades de Deploy](../Transicao/ativ_deploy.md)

## Decisões principais

| **Decisão** | **Escolha** | **Documento** |
| --- | --- | --- |
| Hospedagem do banco | PostgreSQL 16 em contêiner com volume `pgdata` | dimrbd |
| Computação | 1 EC2 t3.small, 3 *workers* Gunicorn | dim_comp |
| Segredos | `.env` fora do Git + `.env.example` | maps |
| Deploy | Recreate/Rolling simples, rollback por *tag* | ativ_deploy |
| Custo estimado | ≈ US$ 21,23/mês (AWS Pricing Calculator) | rs |
