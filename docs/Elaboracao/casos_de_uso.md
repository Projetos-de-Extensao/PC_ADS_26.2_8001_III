**Casos de Uso Arquiteturais**

**Projeto Apollo**

|  |  |
| --- | --- |
| **Projeto** | Apollo — Plataforma de Análise de Desempenho no ENEM |
| **Documento** | Modelo de Casos de Uso Arquiteturais |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Em Desenvolvimento |
| **Responsável** | Equipe do Projeto Apollo |
| **Disciplina** | Projeto de Cloud |

# 1. Introdução

## 1.1. Propósito

Este documento descreve os Casos de Uso Arquiteturais para a infraestrutura em nuvem AWS da plataforma Apollo. Os casos de uso arquiteturais focam em requisitos de infraestrutura, segurança, operações e governança, diferentemente dos casos de uso funcionais que descrevem a interação do aluno com o sistema (envio de respostas, visualização do dashboard e das sugestões de estudo).

## 1.2. Escopo

Os casos de uso arquiteturais abrangem a configuração, operação e manutenção da infraestrutura AWS do Apollo, incluindo:

* Rede (VPC, sub-redes, rotas)
* Segurança (Security Groups, IAM)
* Conectividade entre camadas (EC2, RDS, API Gateway, Lambda)
* Integração com serviços gerenciados (DynamoDB, S3, Secrets Manager)
* Automação e deploy (CI/CD)

O escopo aqui é deliberadamente mais enxuto que uma arquitetura de produção corporativa: o Apollo é um projeto acadêmico com equipe de quatro pessoas e orçamento de até US$ 100/mês, priorizando o AWS Free Tier. Por isso, não há redundância Multi-AZ obrigatória nem Auto Scaling Group como pré-requisito — esses itens aparecem como evolução possível, não como requisito de entrega.

## 1.3. Referências

* Documento de Visão — Projeto Apollo (v1.0)
* Documento de Requisitos Suplementares — Projeto Apollo (v1.0)
* AWS Well-Architected Framework
* Amazon VPC Documentation

# 2. Visão Geral dos Casos de Uso

## 2.1. Atores

| **Ator** | **Descrição** | **Responsabilidades** |
| --- | --- | --- |
| Administrador de Infraestrutura | Estudante do grupo responsável por configurar e gerenciar a infraestrutura AWS. | Criar VPC, sub-redes, security groups, banco de dados. |
| Desenvolvedor Backend | Estudante responsável pela API Django e pelo motor de correção/TRI. | Implementar endpoints, integrar com RDS e DynamoDB, publicar releases. |
| Sistema AWS | Serviços gerenciados da AWS (RDS, DynamoDB, S3, Lambda, API Gateway). | Prover serviços, endpoints, logs. |
| Professor/Avaliador | Responsável por validar a arquitetura entregue ao final da disciplina. | Revisar aderência aos requisitos e à documentação. |

## 2.2. Diagrama de Casos de Uso

(Inserir aqui o diagrama de casos de uso arquiteturais do Apollo — atores e UC-ARQ-001 a UC-ARQ-006 conforme especificação da Seção 3.)

# 3. Especificação dos Casos de Uso

**UC-ARQ-001: Configurar VPC e Rede do Apollo**

|  |  |
| --- | --- |
| **Identificador** | UC-ARQ-001 |
| **Nome** | Configurar VPC e Rede do Apollo |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Aprovado |
| **Ator Principal** | Administrador de Infraestrutura |
| **Ator Secundário** | Sistema AWS |
| **Pré-condição** | 1. Conta AWS ativa (Free Tier). 2. Permissões IAM para criar VPC, sub-redes, Internet Gateway e Route Tables. |
| **Pós-condição** | 1. VPC criada com CIDR 10.0.0.0/16. 2. 2 sub-redes criadas (1 pública, 1 privada) em uma única AZ. 3. Internet Gateway anexado. 4. Route Tables configuradas. |

**Fluxo Principal**

**1.** Administrador acessa o Console AWS.

**2.** Navega até o serviço VPC.

**3.** Cria VPC com CIDR 10.0.0.0/16 e habilita DNS hostnames.

**4.** Cria 1 sub-rede pública com CIDR 10.0.1.0/24 (hospeda a EC2 da API Django).

**5.** Cria 1 sub-rede privada com CIDR 10.0.2.0/24 (hospeda o RDS).

**6.** Cria e anexa Internet Gateway à VPC.

**7.** Configura Route Table pública: 10.0.0.0/16 → local, 0.0.0.0/0 → IGW.

**8.** Configura Route Table privada: 10.0.0.0/16 → local (sem rota direta à Internet).

**9.** Associa cada sub-rede à sua Route Table.

**10.** Valida conectividade: EC2 pública acessa a Internet; RDS privado só é alcançado pela EC2.

**Fluxos Alternativos**

| **Alt.** | **Descrição** |
| --- | --- |
| Alt 1 | CIDR da VPC conflita com outra VPC existente na conta (erro de criação). |
| Alt 2 | Permissões IAM insuficientes (erro de autorização). |

**Requisitos Não-Funcionais**

| **Requisito** | **Métrica** |
| --- | --- |
| Desempenho | VPC criada e configurada em menos de 15 minutos. |
| Disponibilidade | Uma única AZ é suficiente para o escopo acadêmico; Multi-AZ fica registrado como evolução futura. |
| Segurança | Sub-rede privada do RDS sem rota direta para a Internet. |
| Custo | Sem NAT Gateway (custo evitado); RDS acessa a Internet apenas indiretamente via EC2, quando necessário. |

**Riscos**

| **Risco** | **Mitigação** |
| --- | --- |
| Endereçamento conflitante | Planejar CIDR único por ambiente (dev/teste). |
| Ausência de NAT limitar atualizações do RDS | Usar Security Group + bastion via EC2 pública quando necessário, sem custo adicional de NAT Gateway. |

**UC-ARQ-002: Configurar Segurança de Rede do Apollo**

|  |  |
| --- | --- |
| **Identificador** | UC-ARQ-002 |
| **Nome** | Configurar Segurança de Rede do Apollo |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Aprovado |
| **Ator Principal** | Administrador de Infraestrutura |
| **Ator Secundário** | Sistema AWS |
| **Pré-condição** | 1. VPC e sub-redes criadas (UC-ARQ-001). 2. IAM configurado. |
| **Pós-condição** | 1. Security Groups configurados para cada camada. 2. IAM roles definidas para EC2 e Lambda. |

**Fluxo Principal**

**1.** Administrador acessa o Console AWS.

**2.** Navega até Security Groups.

**3.** Cria SG-EC2-API com regras de entrada: portas 80/443 (0.0.0.0/0) para o portal e a API Django.

**4.** Cria SG-RDS com regra de entrada: porta 5432, origem restrita ao SG-EC2-API.

**5.** Cria SG-Lambda com regras de saída liberadas para DynamoDB e S3.

**6.** Define IAM roles específicas para a EC2 (acesso a Secrets Manager) e para a Lambda (acesso a DynamoDB e RDS).

**Fluxos Alternativos**

| **Alt.** | **Descrição** |
| --- | --- |
| Alt 1 | Porta do banco (5432) exposta acidentalmente à Internet → revisão imediata das regras. |
| Alt 2 | IAM role com permissões excessivas → aplicar princípio de menor privilégio. |

**Requisitos Não-Funcionais**

| **Requisito** | **Métrica** |
| --- | --- |
| Segurança | Princípio de menor privilégio implementado em todas as roles. |
| Segurança | Comunicação criptografada em trânsito (HTTPS/TLS). |
| Compliance | Conformidade com a LGPD no tratamento de dados de desempenho do aluno. |

**Riscos**

| **Risco** | **Mitigação** |
| --- | --- |
| Security Groups permissivos | Revisão manual das regras antes de cada apresentação/entrega. |
| Acesso não autorizado ao banco | Restringir origem do SG-RDS apenas ao SG-EC2-API. |

**UC-ARQ-003: Configurar Acesso a Serviços Gerenciados (DynamoDB, S3, Secrets Manager)**

|  |  |
| --- | --- |
| **Identificador** | UC-ARQ-003 |
| **Nome** | Configurar Acesso a Serviços Gerenciados (DynamoDB, S3, Secrets Manager) |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Aprovado |
| **Ator Principal** | Administrador de Infraestrutura |
| **Ator Secundário** | Sistema AWS (DynamoDB, S3, Secrets Manager) |
| **Pré-condição** | 1. VPC e sub-redes criadas (UC-ARQ-001). 2. IAM configurado. |
| **Pós-condição** | 1. Lambda e EC2 com acesso configurado a DynamoDB, S3 e Secrets Manager. 2. Políticas de acesso restritivas aplicadas. |

**Fluxo Principal**

**1.** Administrador acessa o Console AWS.

**2.** Cria a tabela DynamoDB usada para cache de resultados de análise/sessão do aluno.

**3.** Cria o bucket S3 para hospedar os arquivos estáticos do frontend.

**4.** Configura o Secrets Manager com as credenciais do RDS.

**5.** Concede à role da EC2 e da Lambda permissão de leitura/escrita apenas nos recursos necessários (tabela e bucket específicos).

**6.** Valida o acesso: API Django lê/grava no DynamoDB e no RDS; Lambda processa submissões e grava resultado.

**Fluxos Alternativos**

| **Alt.** | **Descrição** |
| --- | --- |
| Alt 1 | Permissão configurada de forma ampla demais (acesso a todos os buckets/tabelas) → revisar e restringir à tabela/bucket específico. |

**Requisitos Não-Funcionais**

| **Requisito** | **Métrica** |
| --- | --- |
| Segurança | Acesso restrito a recursos nomeados (não wildcard). |
| Custo | Uso do Free Tier do DynamoDB e do S3 sempre que possível. |
| Desempenho | Leitura de resultados recentes via DynamoDB reduz carga sobre o RDS. |

**Riscos**

| **Risco** | **Mitigação** |
| --- | --- |
| Custo acima do Free Tier em picos de uso | Monitorar consumo via AWS Budgets (ver Documento de Requisitos Suplementares, RNF-CUS-02). |

**UC-ARQ-004: Configurar Conectividade entre Camadas (API, Banco e Ingestão)**

|  |  |
| --- | --- |
| **Identificador** | UC-ARQ-004 |
| **Nome** | Configurar Conectividade entre Camadas (API, Banco e Ingestão) |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Aprovado |
| **Ator Principal** | Administrador de Infraestrutura |
| **Ator Secundário** | Desenvolvedor Backend |
| **Pré-condição** | 1. VPC e sub-redes criadas (UC-ARQ-001). 2. Security Groups configurados (UC-ARQ-002). 3. Acesso a serviços gerenciados configurado (UC-ARQ-003). |
| **Pós-condição** | 1. EC2 rodando a API Django (Gunicorn + Nginx) acessível via HTTPS. 2. RDS acessível apenas pela EC2. 3. API Gateway + Lambda processando o envio de respostas do aluno. |

**Fluxo Principal**

**1.** Administrador acessa o Console AWS.

**2.** Sobe a instância EC2 na sub-rede pública com Nginx + Gunicorn servindo a API Django.

**3.** Configura o RDS PostgreSQL na sub-rede privada, com o Security Group SG-RDS.

**4.** Configura o API Gateway com um endpoint HTTP para recebimento das respostas do aluno.

**5.** Configura a função Lambda que valida o payload, chama o motor de correção/TRI e grava o resultado no RDS e no DynamoDB.

**6.** Testa o fluxo completo: aluno envia respostas → API Gateway → Lambda → RDS/DynamoDB → dashboard consulta resultado via API Django.

**Fluxos Alternativos**

| **Alt.** | **Descrição** |
| --- | --- |
| Alt 1 | EC2 não alcança o RDS (erro de Security Group) → revisar regras do SG-RDS. |
| Alt 2 | Lambda não consegue gravar no DynamoDB (erro de IAM) → revisar a role da função. |

**Requisitos Não-Funcionais**

| **Requisito** | **Métrica** |
| --- | --- |
| Disponibilidade | 99% de disponibilidade mensal (ver RNF-CON-01 do Documento de Requisitos Suplementares). |
| Desempenho | p95 do processamento da submissão menor que 1,5 s (ver RNF-PER-01). |
| Segurança | Comunicação entre camadas restrita à rede da VPC. |

**Riscos**

| **Risco** | **Mitigação** |
| --- | --- |
| EC2 como ponto único de falha | Aceitável no escopo acadêmico; documentar Auto Scaling/Multi-AZ como evolução futura. |
| Payload malformado na ingestão | Validação de schema na Lambda antes de gravar no banco. |

**UC-ARQ-005: Configurar Monitoramento Básico**

|  |  |
| --- | --- |
| **Identificador** | UC-ARQ-005 |
| **Nome** | Configurar Monitoramento Básico |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Aprovado |
| **Ator Principal** | Administrador de Infraestrutura |
| **Ator Secundário** | Desenvolvedor Backend |
| **Pré-condição** | 1. Recursos de rede e aplicação configurados (UC-ARQ-001 a UC-ARQ-004). |
| **Pós-condição** | 1. Dashboard CloudWatch básico configurado. 2. Alarme de erro/indisponibilidade configurado. 3. Logs centralizados no CloudWatch Logs. |

**Fluxo Principal**

**1.** Administrador acessa o Console AWS.

**2.** Navega até o CloudWatch.

**3.** Cria um dashboard simples com métricas de CPU da EC2, erros da API e latência do endpoint de análise.

**4.** Configura um alarme de erro/indisponibilidade que envia notificação por e-mail à equipe.

**5.** Habilita o CloudWatch Logs para a EC2 e para a função Lambda.

**Requisitos Não-Funcionais**

| **Requisito** | **Métrica** |
| --- | --- |
| Observabilidade | Logs cobrindo 100% das requisições da API e execuções da Lambda. |
| Resposta a incidentes | Alerta recebido pela equipe em até 15 minutos após a falha (ver RNF-OPS-02). |

**UC-ARQ-006: Configurar Pipeline de Deploy (CI/CD)**

|  |  |
| --- | --- |
| **Identificador** | UC-ARQ-006 |
| **Nome** | Configurar Pipeline de Deploy (CI/CD) |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Aprovado |
| **Ator Principal** | Desenvolvedor Backend |
| **Ator Secundário** | Sistema AWS (ou GitHub Actions) |
| **Pré-condição** | 1. Código da API Django em repositório Git. 2. EC2 e RDS configurados. |
| **Pós-condição** | 1. Pipeline de deploy funcionando (manual ou semi-automatizado). 2. Deploy de uma nova versão em até 15 minutos. 3. Rollback manual possível em até 30 minutos. |

**Fluxo Principal**

**1.** Desenvolvedor configura um pipeline simples (GitHub Actions ou AWS CodePipeline/CodeBuild) disparado por push na branch principal.

**2.** O pipeline executa os testes automatizados do motor de correção/TRI.

**3.** Em caso de sucesso, o pipeline publica a nova versão da API na instância EC2 (via script de deploy ou CodeDeploy).

**4.** Em caso de falha nos testes, o pipeline interrompe o deploy e notifica a equipe.

**5.** A equipe documenta o passo a passo de rollback manual (restaurar a versão anterior do código) para uso em caso de problema em produção.

**Fluxos Alternativos**

| **Alt.** | **Descrição** |
| --- | --- |
| Alt 1 | Testes falham no pipeline → deploy é bloqueado automaticamente. |
| Alt 2 | Deploy falha na EC2 → equipe executa rollback manual documentado. |

**Requisitos Não-Funcionais**

| **Requisito** | **Métrica** |
| --- | --- |
| Desempenho | Deploy completo em até 15 minutos (ver RNF-MAN-01). |
| Confiabilidade | Rollback manual documentado e executável em até 30 minutos (ver RNF-MAN-02). |

**Riscos**

| **Risco** | **Mitigação** |
| --- | --- |
| Deploy manual sujeito a erro humano | Documentar passo a passo em runbook e, se possível, automatizar via script único. |

# 4. Matriz de Rastreamento

| **Caso de Uso** | **Requisitos Suplementares** | **Documento de Visão** | **Serviços AWS** |
| --- | --- | --- | --- |
| UC-ARQ-001 | Disponibilidade, Custo (RNF-CON, RNF-CUS) | Arquitetura da solução | VPC, Sub-redes, Internet Gateway, Route Tables |
| UC-ARQ-002 | Segurança (LGPD) (RNF-SEG) | Segurança e Privacidade | Security Groups, IAM |
| UC-ARQ-003 | Segurança, Custo (RNF-SEG, RNF-CUS) | Arquitetura da solução | DynamoDB, S3, Secrets Manager |
| UC-ARQ-004 | Desempenho, Disponibilidade (RNF-PER, RNF-CON) | API + Ingestão de respostas | EC2, RDS, API Gateway, Lambda |
| UC-ARQ-005 | Operação e Observabilidade (RNF-OPS) | Monitoramento | CloudWatch, Logs, Alarms |
| UC-ARQ-006 | Manutenibilidade (Deploy/Rollback) (RNF-MAN) | Automação de entrega | CI/CD (GitHub Actions ou CodePipeline) |

# 5. Aprovações

| **Função** | **Nome** | **Data** | **Assinatura** |
| --- | --- | --- | --- |
| Arquiteto de Soluções |  |  |  |
| Professor Responsável |  |  |  |
| Coordenador do Curso |  |  |  |

# 6. Histórico de Versões

| **Versão** | **Data** | **Autor** | **Descrição das Alterações** |
| --- | --- | --- | --- |
| 1.0 | 21/09/2026 | Equipe do Projeto Apollo | Criação do documento de Casos de Uso Arquiteturais, adaptado ao escopo acadêmico reduzido do Apollo. |
