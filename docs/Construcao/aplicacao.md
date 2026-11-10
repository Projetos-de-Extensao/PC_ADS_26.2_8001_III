# Aplicação (appFinal)

Aplicação web do Projeto Apollo: o aluno envia as respostas de uma prova do ENEM (2016–2025), recebe a **correção**, a **nota TRI estimada** e um diagnóstico dos erros por eixo temático, competência e habilidade, para estudar de forma focada.

[:material-download: Baixar o código (appFinal.zip)](../assets/appFinal.zip){ .md-button .md-button--primary }

O mesmo código está na pasta `appFinal/` deste repositório.

## Stack

| Camada | Tecnologia |
|---|---|
| API | Django 5.2+ + Django REST Framework, autenticação por sessão |
| Banco | PostgreSQL 16 (atributos das questões em JSONB, com índice GIN) |
| Servidor | Gunicorn, arquivos estáticos pelo WhiteNoise |
| Empacotamento | Docker + Docker Compose (banco sem porta publicada; só a API na 8000) |

## Funcionalidades

- Cadastro e login do aluno.
- Envio das 45 respostas de uma área (LC, CH, CN ou MT), com escolha do caderno (cor) e do idioma em Linguagens.
- Correção contra o gabarito oficial do INEP e nota TRI estimada pelo método do INEP.
- Análise de erros por eixo temático, competência e habilidade.
- Dashboard com resumo de provas por edição, gráfico de acertos, erros e brancos, desempenho por área e ranking do que mais errou.
- Exclusão de um envio, usada para corrigir uma cor de caderno informada errado.
- **Regra de cor por dia:** cada dia do ENEM aplica um único caderno de 90 questões, então LC e CH (dia 1) e CN e MT (dia 2) têm sempre a mesma cor (em 2016: CH com CN e LC com MT). A API recusa a cor divergente, a tela de envio trava a cor e o dashboard sinaliza edições inconsistentes.

## Como executar

```bash
cd appFinal
./scripts/gerar_env.sh <IP_ou_localhost>   # gera o .env com SECRET_KEY e senhas aleatórias (não versionado)
docker compose up -d --build
curl http://localhost:8000/health/
```

Páginas: `/` (início), `/login/`, `/home/`, `/enviar/` e `/dashboard/`; administração em `/admin/`.

## Testes e robustez

- 69 testes automatizados (`python manage.py test`), incluindo CRUD, regra de cor por dia, exclusão e regressões de entradas hostis.
- Teste de caos (entradas gigantes, Unicode, XSS, SQL injection, JSON aninhado, tipos trocados e 1.000 requisições em 5 segundos): nenhuma resposta 500 e nenhum vazamento de stack trace em modo de produção; o banco não recebe dados parciais, porque cada envio é gravado em uma única transação.

## Segurança

- Segredos apenas no arquivo `.env`, listado no `.gitignore` e no `.dockerignore`; o repositório traz só o modelo `.env.example`.
- Com `DEBUG=False` a aplicação recusa subir sem `SECRET_KEY`.
- O banco não é exposto: o Compose não publica a porta 5432.
- Senhas guardadas com hash do Django; o texto dos usuários é sempre escapado na interface.
