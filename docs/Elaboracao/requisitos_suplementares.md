**Documento de Requisitos Suplementares (v1.0)**

**Projeto Apollo**

Projeto: Cloud Computing — Fase de Inception

Data: 21/09/2026

Status: Versão inicial para validação arquitetural

# 1. Propósito e escopo

Este documento define os requisitos não-funcionais, os objetivos de nível de serviço (SLOs), o acordo de nível de serviço (SLA) e as condições operacionais da plataforma Apollo — sistema de análise de gabaritos do ENEM que calcula a nota estimada na Teoria de Resposta ao Item (TRI) e identifica pontos fortes e fracos do estudante por habilidade da Matriz de Referência do INEP.

O escopo deste documento inclui:

* portal web e API transacional em Python com Django REST Framework;
* motor de correção e cálculo de nota TRI (biblioteca própria, com fallback de calibração piecewise quando parâmetros IRT não estão disponíveis);
* ingestão do envio de respostas do aluno via API Gateway e AWS Lambda;
* persistência transacional (gabaritos, matriz de competências/habilidades, resultados de análise) em Amazon RDS PostgreSQL;
* persistência de dados de sessão e cache de resultados recentes em Amazon DynamoDB;
* arquivos estáticos do frontend e ativos de apoio em Amazon S3 e Amazon CloudFront;
* rede, segurança, observabilidade, backup e pipeline de CI/CD na AWS.

Não fazem parte deste documento a implementação completa do código da aplicação, o desenho detalhado da VPC, a parametrização IRT (a/b/c) de todas as questões do banco (dados não públicos do INEP) e a classificação manual de habilidades pendente em algumas edições do banco de questões.

# 2. Contexto e restrições

| **Item** | **Premissa ou restrição** |
| --- | --- |
| Escala inicial | Uso acadêmico/piloto — dezenas a centenas de alunos simultâneos (turma/escola), não milhões de usuários |
| Cobertura de conteúdo | Provas do ENEM de 2019 a 2025 (7 edições), 4 áreas (LC, CH, CN, MT), 45 questões por área |
| Frequência de uso | Envios pontuais por aluno (uma submissão por simulado/prova realizada), não telemetria contínua |
| Pico de uso esperado | Após aplicação de um simulado, dezenas de submissões concorrentes em uma janela curta (ex.: 1 hora) |
| Stack obrigatória | Python, Django REST Framework e serviços gerenciados AWS |
| Equipe | Quatro estudantes, entre desenvolvimento e DevOps |
| Orçamento | Máximo de US$ 100 por mês (ambiente acadêmico, camada gratuita da AWS sempre que possível) |
| Prazo | Semestre letivo — entrega ao final do período da disciplina |
| Regulamentação | Lei Geral de Proteção de Dados (LGPD) — dados de desempenho escolar tratados como dado pessoal do aluno |
| Crescimento esperado | Não aplicável no horizonte do projeto acadêmico; arquitetura documentada de forma a permitir evolução futura |

# 3. Definições e indicadores

**SLA:** compromisso formal de nível de serviço assumido com os usuários (alunos e professores).

**SLO:** objetivo mensurável que orienta o serviço.

**SLI:** indicador observado para verificar um SLO.

**TRI:** Teoria de Resposta ao Item — modelo estatístico usado pelo INEP para estimar a proficiência do aluno a partir do padrão de acertos e erros.

**Habilidade/Competência:** unidades da Matriz de Referência do INEP que classificam cada questão por área de conhecimento.

**p95:** valor abaixo do qual estão 95% das medições.

**RPO:** máximo de dados que podem ser perdidos após uma falha.

**RTO:** tempo máximo para restaurar o serviço.

**MTTR:** tempo médio para reparar ou restaurar o serviço.

# 4. Requisitos de desempenho e capacidade

| **ID** | **Requisito** | **Critério de aceitação** |
| --- | --- | --- |
| RNF-PER-01 | A correção e o cálculo da nota TRI devem responder rapidamente ao aluno. | p95 do tempo entre o envio das respostas e a exibição do resultado menor que 1,5 s em teste de carga. |
| RNF-PER-02 | A plataforma deve suportar o pico de uso após aplicação de um simulado. | Processar pelo menos 50 submissões por minuto sem erro superior a 1%. |
| RNF-PER-03 | O dashboard de desempenho deve carregar de forma adequada para o aluno. | Primeira visualização do dashboard (nota TRI + gráfico) disponível em até 3 segundos em condições normais. |
| RNF-CAP-01 | A capacidade deve acompanhar o crescimento do número de edições do ENEM cadastradas. | Adicionar uma nova edição (ano) ao banco de questões sem alteração estrutural da solução. |
| RNF-CAP-02 | A ingestão de respostas deve ser isolada da API administrativa/dashboard. | Pico de envios de respostas não pode elevar a taxa de erro das consultas de dashboard acima de 1%. |

Medição: CloudWatch, métricas do API Gateway e testes de carga simples (ex.: locust ou k6) simulando o envio simultâneo de submissões. As medições devem registrar percentis, taxa de erro, throughput e cenário utilizado.

# 5. Requisitos de disponibilidade e confiabilidade

| **ID** | **Requisito** | **Critério de aceitação** |
| --- | --- | --- |
| RNF-CON-01 | A API e o portal web devem ter disponibilidade mensal de 99%. | Downtime não planejado inferior a aproximadamente 7 horas em uma janela de 30 dias. |
| RNF-CON-02 | O endpoint de envio de respostas deve permanecer disponível durante o uso normal da turma. | Downtime não planejado inferior a 99% no período de aplicação de simulados. |
| RNF-CON-03 | O RPO dos dados transacionais (respostas e resultados) deve ser menor que 24 horas. | Backup diário do RDS comprova perda máxima de 24 horas em exercício de recuperação. |
| RNF-CON-04 | O RTO de uma indisponibilidade catastrófica deve ser menor que 4 horas. | Ambiente restaurado e validado em até 4 horas durante teste de recuperação simulado. |
| RNF-CON-05 | O MTTR de incidentes críticos deve ser menor que 1 hora. | Registro de incidentes simulados durante o projeto mostra média inferior a 1 hora após identificação do problema. |

Diretriz: utilizar recursos gerenciados simples e de baixo custo — RDS com backup automático diário, DynamoDB com backup sob demanda, e infraestrutura documentada em scripts para permitir recriação manual do ambiente quando necessário.

# 6. Requisitos de segurança e privacidade

| **ID** | **Requisito** | **Critério de aceitação** |
| --- | --- | --- |
| RNF-SEG-01 | Toda comunicação externa deve ser protegida. | API e portal aceitam somente HTTPS/TLS. |
| RNF-SEG-02 | Dados em repouso devem ser criptografados. | RDS, DynamoDB e S3 utilizam criptografia gerenciada por AWS KMS (opção padrão do serviço). |
| RNF-SEG-03 | O acesso de aluno aos próprios resultados deve ser autenticado. | Aluno só visualiza resultados de submissões associadas à sua própria conta. |
| RNF-SEG-04 | O princípio do menor privilégio deve ser aplicado às credenciais da aplicação. | Cada componente (API, função Lambda) utiliza uma IAM role específica, sem credenciais compartilhadas. |
| RNF-SEG-05 | Segredos não podem ser armazenados no código-fonte. | Credenciais de banco de dados ficam no AWS Secrets Manager e não aparecem no repositório Git. |
| RNF-SEG-06 | O tratamento de dados deve observar a LGPD. | Dados de desempenho do aluno (respostas, notas, habilidades com dificuldade) são tratados com finalidade definida (feedback pedagógico) e não compartilhados com terceiros. |

# 7. Requisitos de operação e observabilidade

| **ID** | **Requisito** | **Critério de aceitação** |
| --- | --- | --- |
| RNF-OPS-01 | A saúde da aplicação deve ser monitorada. | Dashboard CloudWatch básico exibe disponibilidade, latência e erros da API. |
| RNF-OPS-02 | Falhas devem gerar alertas simples para a equipe. | Alarme de erro ou indisponibilidade envia notificação (e-mail) à equipe do projeto. |
| RNF-OPS-03 | Logs da aplicação devem ser centralizados. | Requisições da API e erros são registrados no CloudWatch Logs com timestamp e identificador de submissão. |
| RNF-OPS-04 | Backups devem ser automatizados. | RDS possui backup diário automático com retenção mínima de 7 dias. |
| RNF-OPS-05 | A recuperação deve ser testada ao menos uma vez. | Procedimento de restore é documentado e executado uma vez durante o projeto, com evidência registrada. |

# 8. Requisitos de manutenibilidade e entrega

| **ID** | **Requisito** | **Critério de aceitação** |
| --- | --- | --- |
| RNF-MAN-01 | O deploy deve ser, no mínimo, semi-automatizado. | Pipeline (CodePipeline/CodeBuild ou script equivalente) publica uma nova versão em até 15 minutos. |
| RNF-MAN-02 | O rollback deve ser possível. | Uma versão estável anterior pode ser restaurada manualmente em até 30 minutos. |
| RNF-MAN-03 | Mudanças devem ser rastreáveis. | Histórico de commits no Git registra autor, data e descrição de cada alteração relevante. |
| RNF-MAN-04 | A solução deve ser documentada para entrega acadêmica. | Documento de Visão, este Documento de Requisitos Suplementares e um README de instalação/execução acompanham a entrega final. |

# 9. Requisitos de usabilidade

| **ID** | **Requisito** | **Critério de aceitação** |
| --- | --- | --- |
| RNF-USA-01 | O aluno deve compreender seu desempenho sem apoio técnico. | Dashboard apresenta nota TRI, acertos/erros/brancos e habilidades a melhorar em linguagem simples, sem jargão técnico. |
| RNF-USA-02 | O envio de respostas deve ser simples. | Aluno preenche uma grade de 45 questões (A–E) em uma única tela, com validação de campos antes do envio. |
| RNF-USA-03 | Mensagens de erro devem orientar a ação do usuário. | Erros de validação (ex.: questão sem resposta em campo obrigatório) indicam claramente o campo e a correção esperada. |

# 10. Requisitos de custo

| **ID** | **Requisito** | **Critério de aceitação** |
| --- | --- | --- |
| RNF-CUS-01 | O custo mensal total deve respeitar o orçamento do projeto acadêmico. | Faturamento mensal permanece abaixo de US$ 100, priorizando o AWS Free Tier. |
| RNF-CUS-02 | O custo deve ser acompanhado durante o desenvolvimento. | AWS Budgets configurado com alerta em 80% e 100% do orçamento mensal definido. |
| RNF-CUS-03 | Recursos não utilizados devem ser desligados fora dos períodos de teste/apresentação. | Instâncias EC2/RDS são interrompidas quando não há atividade planejada, reduzindo custo ocioso. |

# 11. SLA e responsabilidades

O SLA definido para fins do projeto acadêmico estabelece 99% de disponibilidade mensal para a API e o portal web, medido por verificações periódicas simples (ex.: health check HTTPS). Manutenções programadas e comunicadas com antecedência à turma não entram no cálculo.

| **Responsável** | **Obrigações principais** |
| --- | --- |
| AWS | Disponibilidade dos serviços gerenciados contratados (EC2, RDS, DynamoDB, S3, CloudFront, Lambda, API Gateway), conforme os SLAs próprios de cada serviço. |
| Equipe do Projeto Apollo | Código da aplicação, configuração, IAM, dados, monitoramento básico, backups, testes e resposta a incidentes durante o período do projeto. |
| Professor/Avaliador | Validar a aderência da entrega aos requisitos definidos neste documento e no Documento de Visão. |

# 12. Dependências, riscos e decisões pendentes

| **Item** | **Impacto** | **Tratamento** |
| --- | --- | --- |
| Parâmetros IRT (a, b, c) não são públicos para todas as questões | Nota TRI usa calibração piecewise como aproximação, não o modelo IRT completo | Manter fallback documentado e aplicar IRT completo apenas às questões já parametrizadas |
| Classificação de habilidade pendente em algumas edições (2020–2022, 2024–2025) | Dashboard de pontos fortes/fracos fica limitado nessas edições | Priorizar classificação manual das edições mais usadas (ex.: 2025) até a entrega final |
| Custo real de serviços gerenciados no Free Tier | Pode exceder o orçamento de US$ 100/mês se o uso ultrapassar os limites gratuitos | Validar no AWS Pricing Calculator e monitorar via AWS Budgets desde o início |
| Dados pessoais de desempenho escolar | Risco de exposição indevida do histórico de respostas do aluno | Restringir acesso a resultados por conta do aluno e documentar finalidade de uso |
| Divisão de responsabilidades entre backend local e deploy AWS | Parte do time constrói a aplicação localmente antes da migração para nuvem | Definir contrato de API estável entre motor de análise, backend Django e infraestrutura AWS antes da migração |

# 13. Critérios de aprovação

O documento será considerado aprovado quando:

* todos os requisitos não-funcionais críticos tiverem métrica e critério de aceitação definidos;
* a arquitetura proposta (Django + API Gateway/Lambda + RDS + DynamoDB + S3/CloudFront) demonstrar atendimento aos requisitos de desempenho e disponibilidade estabelecidos;
* o custo estimado estiver dentro do orçamento de US$ 100/mês ou possuir justificativa formal registrada;
* o tratamento de dados pessoais dos alunos for revisado à luz da LGPD;
* os testes de carga básicos, backup e restore estiverem planejados e, quando possível, executados ao menos uma vez.

# 14. Histórico de versões

| **Versão** | **Data** | **Descrição** | **Autor** |
| --- | --- | --- | --- |
| 1.0 | 21/09/2026 | Criação do Documento de Requisitos Suplementares para o Projeto Apollo, com escopo reduzido e adequado a entrega acadêmica. | Equipe do Projeto Apollo |
