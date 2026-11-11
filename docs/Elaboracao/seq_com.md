**Diagramas de Sequência e de Comunicação**

**Projeto Apollo**

|  |  |
| --- | --- |
| **Projeto** | Apollo — Plataforma de Análise de Desempenho no ENEM |
| **Documento** | Diagramas de Sequência e de Comunicação |
| **Versão** | 1.0 |
| **Data** | 08/11/2026 |
| **Status** | Em Revisão |
| **Responsável** | Equipe do Projeto Apollo |
| **Disciplina** | Projeto de Cloud |
| **Fase RUP/UP** | Elaboração |

# 1. Introdução

## 1.1. Propósito

Detalhar, por meio de diagramas de sequência e de comunicação, as interações entre os componentes do Apollo nos seis fluxos arquiteturalmente relevantes: autenticação, envio de respostas, dashboard, consulta por atributo JSONB, deploy e persistência/recuperação.

## 1.2. Escopo

Componentes: Aluno, Administrador, Desenvolvedor, `web` (Django + DRF + Gunicorn), `db` (PostgreSQL 16), volume `pgdata`, Docker Compose, GitHub, CloudWatch/SNS.

## 1.3. Siglas

| **Sigla** | **Definição** |
| --- | --- |
| API | Interface de programação |
| JSONB | JSON binário do PostgreSQL |
| GIN | Índice invertido |
| TRI | Teoria de Resposta ao Item |

## 1.4. Referências

* Casos de Uso Arquiteturais v2.0; Requisitos Suplementares v2.0
* Dimensionamento de Computação e de Banco de Dados v1.0

# 2. Visão Geral dos Fluxos

| **Fluxo** | **Descrição** | **Casos de Uso** | **RNF** |
| --- | --- | --- | --- |
| F1 | Cadastro e login do aluno | UC-ARQ-004 | RNF-SEG-03 |
| F2 | Envio de respostas com transação atômica | UC-ARQ-004 | RNF-DAD-01, RNF-PER-01 |
| F3 | Consulta do dashboard (nota TRI e habilidades) | UC-ARQ-004 | RNF-PER-03, RNF-SEG-03 |
| F4 | Consulta de questões por atributo JSONB | UC-ARQ-003/004 | RNF-PER-04 |
| F5 | Deploy e rollback | UC-ARQ-006 | RNF-MAN-01/02 |
| F6 | Persistência após reinício e restauração de backup | UC-ARQ-003/007 | RNF-DAD-02, RNF-CON-03/04 |

# 3. Especificação dos Fluxos

## 3.1. F1 — Cadastro e Login

### Diagrama de Sequência

```plantuml
@startuml
hide footbox
actor Aluno
participant "web (Django)" as W
database "db" as D
Aluno -> W : POST /api/cadastro (nome, e-mail, senha)
W -> W : valida dados e aplica hash na senha
W -> D : INSERT Aluno/usuário
D --> W : id
W --> Aluno : 201 Created
Aluno -> W : POST /api/login (e-mail, senha)
W -> D : SELECT usuário
D --> W : registro
W -> W : confere hash
W -> D : INSERT sessão
W --> Aluno : 200 OK + cookie de sessão
@enduml
```

### Diagrama de Comunicação

```plantuml
@startuml
left to right direction
skinparam shadowing false
actor Aluno
component "web (Django)" as W
database "db" as D
Aluno --> W : 1: POST cadastro / 4: POST login
W --> D : 2: INSERT usuário / 5: SELECT usuário / 6: INSERT sessão
W --> Aluno : 3: 201 Created / 7: 200 + cookie
@enduml
```

| **#** | **Mensagem** | **De → Para** | **Dados** |
| --- | --- | --- | --- |
| 1 | POST cadastro | Aluno → web | nome, e-mail, senha |
| 2 | INSERT usuário | web → db | senha em hash |
| 3 | 201 Created | web → Aluno | id |
| 4 | POST login | Aluno → web | e-mail, senha |
| 5–6 | SELECT usuário / INSERT sessão | web → db | credenciais, sessão |
| 7 | 200 OK + cookie | web → Aluno | cookie de sessão |

## 3.2. F2 — Envio de Respostas (Transação Atômica)

### Diagrama de Sequência

```plantuml
@startuml
hide footbox
actor Aluno
participant "web (DRF)" as W
database "db" as D
Aluno -> W : POST /api/submissoes (edição, área, 45 respostas)
W -> W : autentica sessão e valida o payload
W -> D : SELECT questões da edição/área (gabarito, atributos)
D --> W : 45 questões
W -> W : corrige e calcula nota TRI (estimada)
W -> D : BEGIN (transaction.atomic)
W -> D : INSERT Submissao
W -> D : INSERT RespostaInformada ×45
W -> D : INSERT Resultado
alt regras válidas
  W -> D : COMMIT
  W --> Aluno : 201 Created (acertos, nota TRI)
else gabarito inconsistente / regra violada
  W -> D : ROLLBACK
  W --> Aluno : 400 Bad Request (nenhuma linha gravada)
end
@enduml
```

### Diagrama de Comunicação

```plantuml
@startuml
left to right direction
skinparam shadowing false
actor Aluno
component "web (DRF)" as W
database "db" as D
Aluno --> W : 1: POST /submissoes
W --> W : 2: valida e autentica
W --> D : 3: SELECT questões
D --> W : 4: gabarito e atributos
W --> W : 5: corrige e calcula TRI
W --> D : 6: BEGIN + INSERTs
W --> D : 7: COMMIT ou ROLLBACK
W --> Aluno : 8: 201 ou 400
@enduml
```

| **#** | **Mensagem** | **De → Para** | **Dados** |
| --- | --- | --- | --- |
| 1 | POST /submissoes | Aluno → web | edição, área, respostas |
| 2 | validar / autenticar | web | sessão, esquema |
| 3–4 | SELECT questões | web ↔ db | gabarito, atributos |
| 5 | corrigir e calcular TRI | web | acertos, nota |
| 6 | BEGIN + INSERTs | web → db | Submissao, Respostas, Resultado |
| 7 | COMMIT / ROLLBACK | web → db | decisão da transação |
| 8 | 201 / 400 | web → Aluno | resultado ou erro |

## 3.3. F3 — Consulta do Dashboard

### Diagrama de Sequência

```plantuml
@startuml
hide footbox
actor Aluno
participant "web (DRF)" as W
database "db" as D
Aluno -> W : GET /api/dashboard
W -> W : identifica o aluno pela sessão
W -> D : SELECT Resultados do aluno (histórico)
D --> W : resultados
W -> D : SELECT erros por habilidade/assunto (JOIN Resposta × Questão)
D --> W : agregação por habilidade
W -> W : ordena áreas prioritárias
W --> Aluno : 200 OK (nota TRI, acertos/erros, habilidades a melhorar)
@enduml
```

### Diagrama de Comunicação

```plantuml
@startuml
left to right direction
skinparam shadowing false
actor Aluno
component "web (DRF)" as W
database "db" as D
Aluno --> W : 1: GET /dashboard
W --> D : 2: SELECT resultados do aluno
W --> D : 3: SELECT erros por habilidade
D --> W : 4: dados agregados
W --> Aluno : 5: 200 + dashboard
@enduml
```

| **#** | **Mensagem** | **De → Para** | **Dados** |
| --- | --- | --- | --- |
| 1 | GET /dashboard | Aluno → web | cookie de sessão |
| 2 | SELECT resultados | web → db | filtro pelo aluno autenticado |
| 3–4 | SELECT erros por habilidade | web ↔ db | agregação |
| 5 | 200 OK | web → Aluno | nota TRI, habilidades |

## 3.4. F4 — Consulta por Atributo JSONB

### Diagrama de Sequência

```plantuml
@startuml
hide footbox
actor Aluno
participant "web (DRF)" as W
database "db" as D
Aluno -> W : GET /api/questoes/?atributos__habilidade=H12
W -> W : monta filtro (django-filter)
W -> D : SELECT ... WHERE atributos @> '{"habilidade":"H12"}'
note right of D : usa índice GIN\nsobre atributos (JSONB)
D --> W : questões filtradas
W --> Aluno : 200 OK (lista paginada)
@enduml
```

### Diagrama de Comunicação

```plantuml
@startuml
left to right direction
skinparam shadowing false
actor Aluno
component "web (DRF)" as W
database "db (índice GIN)" as D
Aluno --> W : 1: GET /questoes/?atributos__habilidade=H12
W --> D : 2: SELECT ... atributos @> {...}
D --> W : 3: questões
W --> Aluno : 4: 200 OK
@enduml
```

| **#** | **Mensagem** | **De → Para** | **Dados** |
| --- | --- | --- | --- |
| 1 | GET com filtro | Aluno → web | `atributos__habilidade=H12` |
| 2 | SELECT com `@>` | web → db | consulta JSONB indexada |
| 3 | resultado | db → web | linhas |
| 4 | 200 OK | web → Aluno | JSON paginado |

## 3.5. F5 — Deploy e Rollback

### Diagrama de Sequência

```plantuml
@startuml
hide footbox
actor Desenvolvedor as DEV
participant GitHub as GH
participant "EC2 (shell)" as EC2
participant "Docker Compose" as C
database "db" as D
participant "web" as W
DEV -> GH : git push + tag vX.Y
DEV -> EC2 : ssh
EC2 -> D : pg_dump pré-deploy
EC2 -> GH : git pull
EC2 -> C : docker compose up -d --build
C -> W : recria contêiner web
EC2 -> W : manage.py migrate
EC2 -> W : GET /health/
alt saudável
  W --> EC2 : 200 OK
else falha
  EC2 -> GH : git checkout tag anterior
  EC2 -> C : docker compose up -d --build
end
@enduml
```

### Diagrama de Comunicação

```plantuml
@startuml
left to right direction
skinparam shadowing false
actor Desenvolvedor as DEV
component GitHub as GH
component "EC2 (shell)" as EC2
component "Docker Compose" as C
component web as W
database db as D
DEV --> GH : 1: push + tag
DEV --> EC2 : 2: ssh
EC2 --> D : 3: pg_dump
EC2 --> GH : 4: git pull
EC2 --> C : 5: up -d --build
C --> W : 6: recria web
EC2 --> W : 7: migrate e /health/
@enduml
```

| **#** | **Mensagem** | **De → Para** | **Dados** |
| --- | --- | --- | --- |
| 1 | push + tag | Dev → GitHub | commits, versão |
| 2 | ssh | Dev → EC2 | chave `.pem` |
| 3 | `pg_dump` | EC2 → db | backup pré-deploy |
| 4 | `git pull` | EC2 → GitHub | código |
| 5–6 | `up -d --build` | EC2 → Compose → web | nova imagem |
| 7 | migrate e `/health/` | EC2 → web | verificação |

## 3.6. F6 — Persistência e Restauração

### Diagrama de Sequência

```plantuml
@startuml
hide footbox
actor Administrador as ADM
participant "Docker Compose" as C
database "db" as D
participant "Volume pgdata" as V
ADM -> D : cria registro de teste
ADM -> C : docker compose down (sem -v)
C -> D : encerra contêiner
D -> V : dados permanecem no volume
ADM -> C : docker compose up -d
C -> D : novo contêiner monta pgdata
ADM -> D : SELECT registro de teste
D --> ADM : registro presente
== Perda do volume ==
ADM -> D : gunzip -c dump.sql.gz | psql
D --> ADM : dados restaurados (RPO ≤ 24 h)
@enduml
```

### Diagrama de Comunicação

```plantuml
@startuml
left to right direction
skinparam shadowing false
actor Administrador as ADM
component "Docker Compose" as C
database db as D
storage "Volume pgdata" as V
ADM --> D : 1: grava registro de teste
ADM --> C : 2: down (sem -v)
D --> V : 3: dados permanecem
ADM --> C : 4: up -d
C --> D : 5: remonta pgdata
ADM --> D : 6: consulta e confirma
ADM --> D : 7: restaura dump (se o volume foi perdido)
@enduml
```

| **#** | **Mensagem** | **De → Para** | **Dados** |
| --- | --- | --- | --- |
| 1 | gravar registro de teste | Admin → db | linha de teste |
| 2–3 | `down` sem `-v` | Admin → Compose → db | volume preservado |
| 4–5 | `up -d` | Admin → Compose → db | montagem de `pgdata` |
| 6 | consultar | Admin → db | confirma persistência |
| 7 | restaurar dump | Admin → db | `.sql.gz` diário |

# 4. Diagrama de Classes de Análise

```plantuml
@startuml
skinparam shadowing false
skinparam classAttributeIconSize 0
class SubmissaoView <<boundary>> {
  +post()
  +get()
}
class SubmissaoService <<control>> {
  +corrigir(respostas)
  +calcularTri(acertos)
  +registrar()
}
class QuestaoRepository <<entity access>> {
  +porEdicaoArea()
  +porAtributo()
}
class Aluno <<entity>>
class Submissao <<entity>>
class RespostaInformada <<entity>>
class Resultado <<entity>>
class Questao <<entity>> {
  +atributos : JSONB
}
SubmissaoView --> SubmissaoService
SubmissaoService --> QuestaoRepository
SubmissaoService --> Submissao
Submissao "1" o-- "45" RespostaInformada
Submissao "1" -- "1" Resultado
RespostaInformada "*" --> "1" Questao
Aluno "1" --> "*" Submissao
@enduml
```

# 5. Matriz de Rastreamento

| **Fluxo** | **Requisitos** | **Caso de Uso** | **Componentes** | **Evidência prevista (README)** |
| --- | --- | --- | --- | --- |
| F1 | RNF-SEG-03 | UC-ARQ-004 | web, db | Teste de login |
| F2 | RNF-DAD-01, RNF-PER-01/02 | UC-ARQ-004 | web, db | Teste de *rollback*; medição de p95 |
| F3 | RNF-PER-03, RNF-SEG-03 | UC-ARQ-004 | web, db | Captura do dashboard |
| F4 | RNF-PER-04 | UC-ARQ-003/004 | web, db (GIN) | `EXPLAIN` mostrando índice |
| F5 | RNF-MAN-01/02 | UC-ARQ-006 | GitHub, EC2, Compose | Log do deploy e do rollback |
| F6 | RNF-DAD-02, RNF-CON-03/04 | UC-ARQ-003/007 | db, pgdata | Print antes/depois do `down`/`up`; restauração |

# 6. Considerações Finais

Os seis fluxos cobrem os requisitos centrais da AP2: transação atômica, índice JSONB, persistência em volume e deploy reprodutível. Cada fluxo possui uma evidência a ser anexada ao README.

# 7. Aprovações

| **Função** | **Nome** | **Data** | **Assinatura** |
| --- | --- | --- | --- |
| Arquiteto de Soluções |  |  |  |
| Professor Responsável |  |  |  |

# 8. Histórico de Versões

| **Versão** | **Data** | **Autor** | **Descrição das Alterações** |
| --- | --- | --- | --- |
| 1.0 | 08/11/2026 | Equipe do Projeto Apollo | Criação: seis fluxos com sequência e comunicação, classes de análise e matriz. |
