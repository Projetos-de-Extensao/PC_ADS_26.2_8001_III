**Documento de Requisitos Suplementares**

**Projeto Apollo**

|  |  |
| --- | --- |
| **Projeto** | Apollo — Plataforma de Análise de Desempenho no ENEM |
| **Documento** | Documento de Requisitos Suplementares |
| **Versão** | 2.0 |
| **Data** | 08/11/2026 |
| **Status** | Em Revisão |
| **Responsável** | Equipe do Projeto Apollo |
| **Disciplina** | Projeto de Cloud |
| **Fase RUP/UP** | Elaboração |

# 1. Introdução

## 1.1. Propósito

Este documento especifica os requisitos **não funcionais** (atributos de qualidade) e as restrições do Apollo: desempenho, capacidade, confiabilidade, segurança, operação, manutenibilidade, usabilidade e custo. Os requisitos funcionais (envio de respostas, cálculo da nota TRI, análise de erros, dashboard) estão no Documento de Visão e nos casos de uso funcionais.

A versão 2.0 consolida a decisão arquitetural da AP2: a aplicação é uma API **Django + Django REST Framework** executada em contêineres Docker (`web` e `db`) em **uma instância Amazon EC2**, com banco **PostgreSQL 16** em volume Docker persistente. A arquitetura serverless/RDS descrita na versão 1.0 permanece registrada como alternativa avaliada (Seção 12).

## 1.2. Escopo

Aplica-se à plataforma Apollo completa: aplicação Django (`web`), banco PostgreSQL (`db`), infraestrutura AWS (EC2, EBS, Security Group, Elastic IP opcional) e processos de entrega (Git, Docker Compose, deploy manual/semiautomatizado).

## 1.3. Definições e Siglas

| **Sigla** | **Definição** |
| --- | --- |
| TRI | Teoria de Resposta ao Item, modelo usado para calcular a nota do ENEM |
| RNF | Requisito Não Funcional |
| RPO / RTO | Recovery Point / Recovery Time Objective |
| SG | Security Group (firewall da instância EC2) |
| EBS | Elastic Block Store (disco da EC2) |
| JSONB | Tipo JSON binário indexável do PostgreSQL |
| GIN | Índice invertido do PostgreSQL, usado sobre JSONB |
| LGPD | Lei Geral de Proteção de Dados (Lei 13.709/2018) |
| p95 | Percentil 95 do tempo de resposta |

## 1.4. Referências

* Documento de Visão — Projeto Apollo (v2.0)
* Casos de Uso Arquiteturais — Projeto Apollo (v2.0)
* Roteiro 14 — Django + PostgreSQL em Docker na EC2
* AWS Well-Architected Framework
* Documentação oficial do Django, DRF, PostgreSQL 16 e Docker Compose

# 2. Decisão Arquitetural que Condiciona os Requisitos

| **Aspecto** | **Decisão (implementada na AP2)** | **Alternativa avaliada** |
| --- | --- | --- |
| Computação | 1 EC2 executando `web` (Django + Gunicorn) via Docker Compose | Lambda + API Gateway |
| Banco | Contêiner `postgres:16` com volume nomeado `pgdata` | Amazon RDS PostgreSQL |
| Segredos | Arquivo `.env` na EC2, fora do Git (`.env.example` versionado) | AWS Secrets Manager |
| Rede | VPC padrão, Security Group com 22 (IP do grupo) e 80/8000 | VPC com sub-redes pública/privada |
| Deploy | `git pull` + `docker compose up -d --build` | CodePipeline / Blue-Green |
| Backup | `pg_dump` agendado + snapshot EBS | Backup automático do RDS |

**Justificativa:** com 4 estudantes, custo estimado de ≈ US$ 36,42/mês e foco em demonstrar o ciclo completo (código → contêiner → nuvem), uma única EC2 com Docker Compose entrega os requisitos do projeto com menor custo e menor superfície de configuração. O preço é um ponto único de falha, aceito pelo SLA de 99% (Seção 5).

# 3. Requisitos de Desempenho e Capacidade

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-PER-01 | A correção e o cálculo da nota TRI devem responder rapidamente ao aluno. | p95 do tempo entre o envio das respostas e a exibição do resultado menor que 1,5 s em teste de carga. |
| RNF-PER-02 | A plataforma deve suportar o pico de uso após um simulado. | Processar pelo menos 50 submissões por minuto com erro inferior a 1%. |
| RNF-PER-03 | O dashboard deve carregar de forma adequada. | Primeira visualização (nota TRI + gráfico) em até 3 s em condições normais. |
| RNF-PER-04 | Consultas por atributos de questão devem usar índice. | Consulta `?atributos__habilidade=H12` usa o índice GIN (verificável com `EXPLAIN`). |
| RNF-CAP-01 | A capacidade deve acompanhar o número de edições cadastradas. | Nova edição (ano) incluída por carga de dados (seed/fixture), sem alteração estrutural. |
| RNF-CAP-02 | Ingestão de respostas não deve degradar consultas do dashboard. | Pico de envios não eleva a taxa de erro das consultas acima de 1%. Em instância única, atendido por limite de *workers* Gunicorn e consultas somente leitura indexadas. |
| RNF-CAP-03 | A instância deve comportar `web` e `db` simultaneamente. | Uso de memória da EC2 abaixo de 80% sob a carga de RNF-PER-02 (medido com `docker stats`). |

# 4. Requisitos de Dados e Transações

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-DAD-01 | O envio de respostas deve ser atômico. | `POST /submissoes` grava Submissao, Respostas e Resultado dentro de `transaction.atomic()`; gabarito inválido provoca *rollback* e nenhuma linha é persistida (coberto por teste automatizado). |
| RNF-DAD-02 | Os dados devem sobreviver à reinicialização dos contêineres. | Após `docker compose down` (sem `-v`) e `up`, os registros continuam disponíveis (teste de persistência com evidência). |
| RNF-DAD-03 | O esquema deve evoluir por migrações versionadas. | Todas as alterações de tabela/índice (inclusive GIN) existem em arquivos de migração no Git. |

# 5. Requisitos de Confiabilidade e Disponibilidade

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-CON-01 | A API e o portal devem ter disponibilidade mensal de 99%. | Downtime não planejado inferior a ~7 h em 30 dias. |
| RNF-CON-02 | O endpoint de envio deve permanecer disponível durante simulados. | Sem indisponibilidade durante a janela de aplicação do simulado. |
| RNF-CON-03 | RPO dos dados transacionais menor que 24 h. | Backup diário (`pg_dump`) comprovado em exercício de restauração. |
| RNF-CON-04 | RTO de indisponibilidade catastrófica menor que 4 h. | Nova EC2 provisionada, repositório clonado, `.env` recriado e dump restaurado em até 4 h (teste simulado). |
| RNF-CON-05 | MTTR de incidentes críticos menor que 1 h. | Média inferior a 1 h nos incidentes simulados. |
| RNF-CON-06 | Contêineres devem se recuperar de falhas simples. | Política `restart: unless-stopped` nos serviços; `web` só inicia após `db` saudável (`healthcheck` com `pg_isready`). |

# 6. Requisitos de Segurança e Privacidade

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-SEG-01 | Comunicação externa protegida. | Meta: HTTPS/TLS via Nginx + certificado. Na entrega base, a API responde em HTTP; o item é registrado como evolução (Seção 12). |
| RNF-SEG-02 | Dados em repouso criptografados. | Volume EBS criptografado (AES-256, chave gerenciada pela AWS), que contém o volume `pgdata`. |
| RNF-SEG-03 | O aluno acessa apenas os próprios resultados. | Autenticação Django; consultas filtradas pelo usuário autenticado (teste automatizado). |
| RNF-SEG-04 | Menor privilégio. | Usuário do Postgres da aplicação sem privilégio de superusuário; usuário IAM de cada integrante com MFA; sem chaves de acesso fixas na instância. |
| RNF-SEG-05 | Segredos fora do código-fonte. | `.env` listado no `.gitignore`; apenas `.env.example` (valores fictícios) versionado; varredura do histórico do Git sem segredos antes da entrega. |
| RNF-SEG-06 | Tratamento de dados conforme a LGPD. | Dados de desempenho usados exclusivamente para feedback pedagógico; coleta mínima (nome/e-mail, respostas); exclusão de conta suportada. |
| RNF-SEG-07 | Superfície de rede mínima. | Security Group libera apenas 22 (IP do grupo) e 80/8000; a porta 5432 **não** é publicada no host nem aberta no SG. |
| RNF-SEG-08 | Configuração de produção segura. | `DEBUG=False` e `ALLOWED_HOSTS` restrito na EC2; `SECRET_KEY` única por ambiente. |

# 7. Requisitos de Operação e Observabilidade

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-OPS-01 | A saúde da aplicação deve ser monitorada. | Endpoint `/health/` consultado por alarme CloudWatch (métrica `StatusCheckFailed` da EC2 e verificação periódica do endpoint). |
| RNF-OPS-02 | Falhas geram alertas simples. | Notificação por e-mail (SNS) à equipe em até 15 min após a falha. |
| RNF-OPS-03 | Logs centralizados e acessíveis. | Logs de `web` e `db` consultáveis com `docker compose logs`; envio ao CloudWatch Logs como evolução. |
| RNF-OPS-04 | Backups automatizados. | `pg_dump` diário via cron, retenção mínima de 7 dias, cópia opcional no S3. |
| RNF-OPS-05 | Recuperação testada ao menos uma vez. | Restauração do dump em ambiente limpo, com evidência registrada. |

# 8. Requisitos de Manutenibilidade e Entrega

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-MAN-01 | Deploy semiautomatizado. | Nova versão publicada em até 15 min com `git pull` + `docker compose up -d --build` (script `deploy.sh`). |
| RNF-MAN-02 | Rollback possível. | Versão anterior restaurada via `git checkout <tag>` + rebuild em até 30 min. |
| RNF-MAN-03 | Mudanças rastreáveis. | Histórico Git com commits individuais de todos os integrantes. |
| RNF-MAN-04 | Solução documentada. | README (arquitetura, execução local, deploy na EC2, links, evidências) e site MkDocs publicado. |
| RNF-MAN-05 | Qualidade mínima verificável. | Mínimo de 3 testes automatizados executados por `python manage.py test`. |

# 9. Requisitos de Usabilidade

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-USA-01 | O aluno entende seu desempenho sem apoio técnico. | Dashboard mostra nota TRI, acertos/erros/brancos e habilidades a melhorar em linguagem simples. |
| RNF-USA-02 | Envio de respostas simples. | Grade de 45 questões (A–E) por área em uma tela, com validação antes do envio. |
| RNF-USA-03 | Mensagens de erro orientam a ação. | Erros de validação indicam campo e correção esperada. |

# 10. Requisitos de Custo

| **ID** | **Requisito** | **Critério de Aceitação** |
| --- | --- | --- |
| RNF-CUS-01 | Custo mensal estimado e documentado. | Estimativa feita na AWS Pricing Calculator (tabela abaixo); faturamento real conferido no console de Billing. |
| RNF-CUS-02 | Estimativa de custo registrada. | Estimativa da AWS Pricing Calculator revisada antes da entrega. |
| RNF-CUS-03 | Recursos ociosos desligados. | EC2 parada fora de períodos de teste/apresentação, quando não houver avaliação programada. |

**Estimativa de custo mensal ([AWS Pricing Calculator](https://calculator.aws/#/estimate?id=8e4fe0a08f011b6f4a2ad10ee8757d1241cf9b53); Leste dos EUA, sob demanda, Linux, 730 h) [Certain]:**

| **Recurso** | **Especificação** | **Custo (US$/mês)** |
| --- | --- | --- |
| EC2 | t3.medium (2 vCPU, 4 GiB) | ≈ 30,37 |
| EBS | gp3, 30 GB | ≈ 2,40 |
| IPv4 público | 1 endereço | ≈ 3,65 |
| **Total** |  | **≈ 36,42** |

Valores conforme a AWS Pricing Calculator, sujeitos à tabela vigente da AWS no momento da entrega.

# 11. Restrições

| **ID** | **Restrição** |
| --- | --- |
| RES-01 | Backend em Python/Django com Django REST Framework e PostgreSQL. |
| RES-02 | Execução em contêineres Docker orquestrados por Docker Compose. |
| RES-03 | Provas do ENEM de 2016 a 2025 (10 edições), 4 áreas × 45 questões em até 4 cadernos por cor (7.400 itens carregados na implantação). |
| RES-04 | Custo mensal estimado na AWS Pricing Calculator (≈ US$ 36,42). |
| RES-05 | Equipe de 4 estudantes; prazo do semestre letivo. |

# 12. Alternativas Avaliadas e Evolução

| **Item** | **Situação** | **Observação** |
| --- | --- | --- |
| Amazon RDS PostgreSQL | Alternativa avaliada | db.t3.micro ≈ US$ 15/mês; ver Modelo de Análise de Classes (RDS) e Dimensionamento de BD. |
| Lambda + API Gateway | Alternativa avaliada | Eleva complexidade de rede e custo de VPC endpoints; adiado. |
| HTTPS com Nginx e certificado | Evolução prioritária | Atende RNF-SEG-01 integralmente. |
| Multi-AZ / Auto Scaling | Evolução | Fora do escopo acadêmico e com custo adicional (ALB e 2ª EC2). |
| WAF, GuardDuty, Security Hub | Evolução | Custo adicional sem necessidade no escopo acadêmico. |

# 13. Considerações Finais

Os requisitos acima são a referência de verificação do Apollo na AP2. Cada item possui critério mensurável; as medições dependentes do ambiente implantado (RNF-PER-01/02, RNF-CAP-03, RNF-MAN-01) são registradas no README com evidências.

# 14. Aprovações

| **Função** | **Nome** | **Data** | **Assinatura** |
| --- | --- | --- | --- |
| Arquiteto de Soluções | Arthur Maurity, Bernardo Casanovas, Bernardo Miller, Lucas Jesus | 10/11/2026 | Aprovado em revisão da equipe |
| Professor Responsável | Jonh Carvalho |  |  |

# 15. Histórico de Versões

| **Versão** | **Data** | **Autor** | **Descrição das Alterações** |
| --- | --- | --- | --- |
| 1.0 | 21/09/2026 | Equipe do Projeto Apollo | Versão inicial (arquitetura serverless/RDS). |
| 2.0 | 08/11/2026 | Equipe do Projeto Apollo | Adoção de Django + PostgreSQL em Docker na EC2; novos RNF de dados e persistência; revisão de segurança, backup e custo. |
| 2.1 | 10/11/2026 | Equipe do Projeto Apollo | RES-03 alinhado à base implantada (ENEM 2016–2025, 7.400 itens). |
