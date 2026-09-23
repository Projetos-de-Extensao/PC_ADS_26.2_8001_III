**Modelo de Análise (Pacotes/Subsistemas)**

**APOLLO — ARQUITETURA DE SEGURANÇA EM NUVEM AWS**

|  |  |
| --- | --- |
| **Projeto** | Apollo — Plataforma de Análise de Desempenho no ENEM |
| **Documento** | Modelo de Análise (Pacotes/Subsistemas) — Segurança |
| **Versão** | 1.0 |
| **Data** | 21/09/2026 |
| **Status** | Em Desenvolvimento |
| **Responsável** | Equipe do Projeto Apollo |
| **Disciplina** | Projeto de Cloud |
| **Fase RUP/UP** | Elaboration |

# 1. Introdução

## 1.1. Propósito

Este documento apresenta o Modelo de Análise (Pacotes/Subsistemas) para a arquitetura de segurança da plataforma Apollo na AWS. O modelo organiza os componentes de segurança em pacotes coesos, facilitando a compreensão, manutenção e evolução da arquitetura, além de permitir a rastreabilidade entre requisitos de segurança e elementos técnicos.

O modelo é derivado diretamente dos seguintes artefatos:

* Documento de Visão — seção "Segurança e Privacidade";
* Documento de Requisitos Suplementares — seção "Requisitos de Segurança e Privacidade" (RNF-SEG);
* Casos de Uso Arquiteturais — UC-ARQ-002 (Segurança de Rede) e UC-ARQ-003 (Acesso a Serviços Gerenciados).

## 1.2. Escopo

O modelo abrange os subsistemas de segurança necessários para proteger:

* Dados de desempenho e respostas do aluno (LGPD);
* Credenciais de banco de dados;
* Resultados de análise e cache de sessão no DynamoDB;
* Arquivos estáticos do frontend no S3;
* Logs de acesso e auditoria básica.

Assim como nos documentos anteriores, o escopo de segurança do Apollo é deliberadamente mais enxuto que o de uma arquitetura corporativa de produção: a equipe é de quatro estudantes, o orçamento é de até US$ 100/mês, e o objetivo é demonstrar boas práticas de segurança em nuvem sem depender de serviços premium de detecção avançada (GuardDuty, Security Hub, WAF gerenciado), que ficam registrados como evolução futura na Seção 6.

## 1.3. Definições e Siglas

| **Sigla** | **Definição** |
| --- | --- |
| IAM | Identity and Access Management |
| KMS | Key Management Service |
| SG | Security Group |
| RBAC | Role-Based Access Control |
| MFA | Multi-Factor Authentication |
| LGPD | Lei Geral de Proteção de Dados |
| TLS | Transport Layer Security |
| SSE | Server-Side Encryption |

## 1.4. Referências

* Documento de Visão — Projeto Apollo (v1.0)
* Documento de Requisitos Suplementares — Projeto Apollo (v1.0)
* Casos de Uso Arquiteturais — Projeto Apollo (v1.0)
* AWS Well-Architected Framework — Security Pillar
* AWS IAM Best Practices
* Lei Geral de Proteção de Dados (LGPD)

# 2. Visão Geral dos Pacotes de Segurança

## 2.1. Diagrama de Pacotes

(Inserir aqui o diagrama de pacotes — quatro pacotes principais: Identity & Access, Network Security, Data Protection e Secrets & Audit — com as dependências descritas na Seção 4.)

## 2.2. Descrição dos Pacotes

| **Pacote** | **Responsabilidade** | **Serviços AWS** | **Requisitos Atendidos** |
| --- | --- | --- | --- |
| Identity & Access | Gerenciar identidades, autenticação e autorização. | IAM, MFA, Grupos IAM | Segurança (LGPD) |
| Network Security | Controlar tráfego de rede entre camadas. | Security Groups | Segurança, Disponibilidade |
| Data Protection | Criptografar dados em repouso e em trânsito. | KMS (padrão AWS), RDS/S3/DynamoDB Encryption, ACM | Segurança, Compliance |
| Secrets & Audit | Proteger credenciais e registrar acessos administrativos. | Secrets Manager, CloudTrail, CloudWatch Logs | Segurança, Manutenibilidade |

## 2.3. Matriz de Rastreamento

| **Requisito (Doc. Suplementar)** | **Pacote Responsável** | **Serviço AWS** | **Controle** |
| --- | --- | --- | --- |
| Criptografia em repouso (RNF-SEG-02) | Data Protection | KMS, RDS, S3, DynamoDB | Criptografia gerenciada padrão AWS |
| Criptografia em trânsito (RNF-SEG-01) | Data Protection | ACM | HTTPS/TLS |
| Menor privilégio (RNF-SEG-04) | Identity & Access | IAM Roles | Roles específicas por serviço |
| Isolamento de credenciais (RNF-SEG-05) | Secrets & Audit | Secrets Manager | Credenciais fora do código |
| Auditoria de acessos (RNF-SEG-06) | Secrets & Audit | CloudTrail | Log de eventos administrativos |
| Conformidade LGPD (RNF-SEG-07) | Data Protection / Secrets & Audit | KMS + CloudTrail | Minimização e rastreabilidade de dados pessoais |

# 3. Especificação dos Pacotes

**3.1. Pacote: Identity & Access**

**3.1.1. Responsabilidade**

Gerenciar identidades (estudantes do grupo e serviços), autenticação e permissões de acesso aos recursos AWS do Apollo.

**3.1.2. Elementos do Pacote**

| **Elemento** | **Descrição** | **Serviço AWS** |
| --- | --- | --- |
| IAM Users | Usuários humanos (membros do grupo com acesso ao console). | IAM |
| IAM Groups | Agrupamento de usuários por função (Dev, Infra). | IAM Groups |
| IAM Roles | Identidades para serviços (EC2, Lambda). | IAM Roles |
| MFA | Autenticação multifator para os usuários humanos. | IAM MFA |

**3.1.3. Roles e Permissões (Apollo)**

| **Role** | **Tipo** | **Serviços Acessados** | **Permissões** | **Justificativa** |
| --- | --- | --- | --- | --- |
| Admin-Role | Humano (grupo) | Todos os recursos do projeto | Administração geral, com MFA | Gestão do ambiente durante o projeto. |
| EC2-API-Role | Serviço | S3, Secrets Manager, DynamoDB, RDS | Leitura/escrita restrita a recursos nomeados | A API Django acessa apenas o necessário. |
| Lambda-Role | Serviço | DynamoDB, RDS, CloudWatch Logs | Escrita de resultado de análise | Processa o envio de respostas do aluno. |

**3.1.4. Política IAM (Exemplo — EC2-API-Role)**

{
 "Version": "2012-10-17",
 "Statement": [
 {
 "Sid": "S3Access",
 "Effect": "Allow",
 "Action": ["s3:GetObject", "s3:PutObject"],
 "Resource": "arn:aws:s3:::apollo-static/\*"
 },
 {
 "Sid": "SecretsAccess",
 "Effect": "Allow",
 "Action": ["secretsmanager:GetSecretValue"],
 "Resource": "arn:aws:secretsmanager:us-east-1:\*:secret:apollo-rds-credentials-\*"
 },
 {
 "Sid": "DynamoDBAccess",
 "Effect": "Allow",
 "Action": ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query"],
 "Resource": "arn:aws:dynamodb:us-east-1:\*:table/apollo-resultados"
 }
 ]
}

**3.1.5. Riscos e Mitigações**

| **Risco** | **Mitigação** |
| --- | --- |
| Credenciais hardcoded no código | Usar IAM Roles para serviços, nunca chaves fixas. |
| Permissões excessivas | Aplicar princípio de menor privilégio nas policies. |
| Acesso não autorizado ao console | MFA obrigatório para todos os membros do grupo. |

**3.2. Pacote: Network Security**

**3.2.1. Responsabilidade**

Controlar e filtrar o tráfego de rede entre as camadas da aplicação (EC2, RDS, Lambda), garantindo que o banco de dados não fique exposto diretamente à Internet.

**3.2.2. Elementos do Pacote**

| **Elemento** | **Descrição** | **Serviço AWS** |
| --- | --- | --- |
| Security Groups | Firewall de instâncias (stateful). | VPC |
| Sub-rede privada | Sub-rede sem rota direta à Internet, usada pelo RDS. | VPC |

**3.2.3. Matriz de Security Groups (Apollo)**

| **Security Group** | **Regra de Entrada** | **Origem** | **Justificativa** |
| --- | --- | --- | --- |
| SG-EC2-API | 80, 443 | 0.0.0.0/0 | Portal e API expostos via HTTPS. |
| SG-RDS | 5432 | SG-EC2-API | Banco acessível apenas pela API. |
| SG-Lambda | (sem entrada) | — | Lambda apenas realiza chamadas de saída para RDS/DynamoDB. |

**3.2.4. Riscos e Mitigações**

| **Risco** | **Mitigação** |
| --- | --- |
| Security Group permissivo demais | Revisão manual das regras antes de cada apresentação/entrega. |
| Porta do banco exposta acidentalmente | Restringir SG-RDS exclusivamente ao SG-EC2-API. |

**3.3. Pacote: Data Protection**

**3.3.1. Responsabilidade**

Garantir a criptografia de dados em repouso e em trânsito, assegurando conformidade com a LGPD no tratamento de dados de desempenho do aluno.

**3.3.2. Elementos do Pacote**

| **Elemento** | **Descrição** | **Serviço AWS** |
| --- | --- | --- |
| Criptografia gerenciada | Criptografia padrão (AES-256) habilitada nos serviços de armazenamento. | KMS (chave gerenciada pela AWS) |
| TLS/ACM | Certificado SSL/TLS para tráfego HTTPS. | ACM |
| Backup automático | Backup diário do banco relacional. | RDS Automated Backups |

**3.3.3. Matriz de Criptografia (Apollo)**

| **Serviço** | **Criptografia em Repouso** | **Criptografia em Trânsito** | **Justificativa** |
| --- | --- | --- | --- |
| RDS | AES-256 (KMS gerenciada pela AWS) | TLS | Dados de respostas e resultados dos alunos (LGPD). |
| S3 | SSE-S3/SSE-KMS | TLS | Arquivos estáticos do frontend. |
| DynamoDB | AES-256 (padrão) | TLS | Cache de resultado de análise/sessão. |
| Secrets Manager | AES-256 (padrão) | TLS | Credenciais do banco de dados. |

**3.3.4. Política de Backup (Apollo)**

| **Serviço** | **Frequência** | **Retenção** | **RPO** | **RTO** |
| --- | --- | --- | --- | --- |
| RDS | Diário (snapshot automático) | 7 dias | 24 horas | 4 horas |
| DynamoDB | Backup sob demanda | Conforme necessidade do projeto | 24 horas | 4 horas |

**3.3.5. Riscos e Mitigações**

| **Risco** | **Mitigação** |
| --- | --- |
| Dados não criptografados por configuração padrão incorreta | Verificar, na criação de cada recurso, que a criptografia está habilitada. |
| Backup não testado | Executar ao menos um teste de restore documentado durante o projeto. |

**3.4. Pacote: Secrets & Audit**

**3.4.1. Responsabilidade**

Proteger credenciais para que não sejam expostas em código, e manter um registro básico de acessos administrativos para fins de auditoria.

**3.4.2. Elementos do Pacote**

| **Elemento** | **Descrição** | **Serviço AWS** |
| --- | --- | --- |
| Secrets Manager | Armazenamento das credenciais do RDS. | Secrets Manager |
| CloudTrail | Registro de ações administrativas na conta AWS. | CloudTrail |
| CloudWatch Logs | Logs de aplicação (API e Lambda). | CloudWatch Logs |

**3.4.3. Segredos Gerenciados (Apollo)**

| **Segredo** | **Serviço** | **Acesso** | **Justificativa** |
| --- | --- | --- | --- |
| rds-credentials | RDS PostgreSQL | EC2-API-Role | Evitar credenciais hardcoded no código Django. |
| django-secret-key | Django | EC2-API-Role | Chave de assinatura de sessão/token. |

**3.4.4. Riscos e Mitigações**

| **Risco** | **Mitigação** |
| --- | --- |
| Segredos commitados no repositório Git | Uso obrigatório do Secrets Manager + .gitignore para arquivos de configuração local. |
| Ausência de rastro de quem alterou o quê na infraestrutura | Habilitar CloudTrail básico na conta desde o início do projeto. |

# 4. Diagrama de Dependências entre Pacotes

| **De** | **Para** | **Motivo** |
| --- | --- | --- |
| Identity & Access | Data Protection | IAM define quais roles podem acessar dados criptografados. |
| Network Security | Identity & Access | Security Groups liberam tráfego apenas para roles/serviços autorizados. |
| Data Protection | Secrets & Audit | Credenciais de acesso ao banco criptografado ficam no Secrets Manager. |
| Secrets & Audit | Identity & Access | CloudTrail registra as ações realizadas pelos usuários e roles IAM. |

# 5. Matriz de Rastreamento Completa

| **Requisito (Doc. Suplementar)** | **Caso de Uso** | **Pacote** | **Serviço AWS** |
| --- | --- | --- | --- |
| Criptografia em repouso (RNF-SEG-02) | UC-ARQ-003 | Data Protection | KMS, RDS, S3, DynamoDB |
| Criptografia em trânsito (RNF-SEG-01) | UC-ARQ-004 | Data Protection | ACM |
| Menor privilégio (RNF-SEG-04) | UC-ARQ-002 | Identity & Access | IAM Roles |
| Isolamento de credenciais (RNF-SEG-05) | UC-ARQ-003 | Secrets & Audit | Secrets Manager |
| Auditoria de acessos (RNF-SEG-06) | UC-ARQ-002 | Secrets & Audit | CloudTrail |
| Conformidade LGPD (RNF-SEG-07) | UC-ARQ-002, UC-ARQ-003 | Data Protection, Secrets & Audit | KMS, CloudTrail |

# 6. Evolução Futura (Fora do Escopo Acadêmico)

Os itens abaixo representam boas práticas de segurança adicionais, comuns em arquiteturas de produção corporativa, mas que ficam fora do escopo desta entrega acadêmica por implicarem custo e complexidade de configuração incompatíveis com o orçamento e o prazo do projeto:

* AWS WAF (Web Application Firewall) para proteção contra SQL Injection, XSS e rate limiting na API.
* Amazon GuardDuty e AWS Security Hub para detecção de ameaças com machine learning.
* AWS Config com Config Rules automatizadas para verificação contínua de conformidade.
* Rotação automática de segredos via Lambda (rotação neste projeto é manual, quando necessária).
* Multi-AZ e Point-in-Time Recovery completo para o RDS.

Esses itens podem ser incorporados em uma evolução futura do Apollo, caso o projeto avance além do escopo acadêmico.

# 7. Histórico de Versões

| **Versão** | **Data** | **Autor** | **Descrição das Alterações** |
| --- | --- | --- | --- |
| 1.0 | 21/09/2026 | Equipe do Projeto Apollo | Criação do Modelo de Análise de Segurança, adaptado ao escopo acadêmico reduzido do Apollo (4 pacotes em vez de 6, sem serviços premium de detecção). |
