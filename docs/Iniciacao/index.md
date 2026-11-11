# Iniciação

**Objetivo:** definir o problema, o escopo e as restrições do Apollo e registrar a decisão arquitetural da AP2.

## Resumo da fase

O Apollo resolve a falta de uma estimativa de nota TRI do ENEM a partir das respostas do próprio aluno: as calculadoras gratuitas contam só o percentual de acertos. A plataforma recebe as 45 respostas de uma área, estima a nota com os parâmetros oficiais do INEP (ENEM 2016–2025) e aponta as habilidades com mais erros.

Na AP2 o grupo trocou o Elastic Beanstalk + SQLite da AP1 por **Django + DRF + PostgreSQL 16 em Docker Compose numa EC2**, com orçamento de US$ 100/mês (custo estimado ≈ US$ 37/mês).

## Documentos da fase

| **Documento** | **Conteúdo** | **Link** |
| --- | --- | --- |
| Documento de Visão | Problema, partes interessadas, necessidades, funcionalidades e restrições | [dv](dv.md) |
| Requisitos Suplementares | Desempenho, disponibilidade, segurança, operação, custo, SLA, riscos e a decisão EC2 + Docker + Postgres | [rs](rs.md) |

## Próxima fase

[Elaboração](../Elaboracao/index.md): arquitetura, dimensionamento e fluxos.
