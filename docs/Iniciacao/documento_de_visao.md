**Documento de Visão (v1.0)**

*Projeto Apollo — Análise de Gabarito do ENEM*

Projeto de Cloud – Fase de Inception

| **Campo** | **Valor** |
| --- | --- |
| Disciplina | Big Data e Cloud Computing (5º Período) |
| Plataforma | Amazon Web Services (AWS) |
| Stack | Python · Django REST Framework · AWS |
| Data | 2026 |

# 1. Introdução

Este documento descreve as necessidades de negócio, restrições e requisitos da plataforma Apollo, guiando o planejamento da solução na nuvem AWS dentro do prazo acadêmico disponível.

## 1.1. Propósito

Definir o escopo e a arquitetura da plataforma Apollo na AWS: um sistema funcional de análise de gabarito do ENEM que demonstra, na prática, o uso dos principais serviços de nuvem estudados na disciplina.

## 1.2. Escopo

O escopo é intencionalmente reduzido para garantir entrega dentro do semestre acadêmico de 20 semanas:

* 1. Formulário web simples: o candidato seleciona a área (LC, CH, CN ou MT) e preenche as 45 respostas da prova.
* 2. Cálculo e exibição do resultado: nota TRI estimada, total de acertos, erros e questões em branco, e lista das questões erradas com o gabarito correto.
* 3. Gabarito fixo: ENEM 2025. Um único conjunto de dados carregado no banco — sem seletor de edição ou caderno na interface.
* 4. Interface HTML simples: página estática servida via S3 + CloudFront, sem framework de frontend.
* 5. Todos os serviços AWS obrigatórios da ementa em funcionamento: EC2, RDS, Lambda, DynamoDB, S3, CloudFront, Secrets Manager e CodePipeline.

Fora do escopo desta versão: seletor de ano e caderno, análise por competência e habilidade, autenticação de usuários, dashboard de professores e múltiplas edições do ENEM.

## 1.3. Definições, Acrônimos e Abreviações

| **Termo** | **Definição** |
| --- | --- |
| ENEM | Exame Nacional do Ensino Médio — principal processo seletivo para o ensino superior brasileiro |
| TRI | Teoria de Resposta ao Item — metodologia do INEP para calcular a nota do ENEM |
| Caderno Azul | Versão da prova utilizada como gabarito de referência nesta versão do projeto (ENEM 2025) |
| Gabarito | Sequência oficial de respostas corretas por área para um caderno de prova |
| API | Application Programming Interface |
| VPC | Virtual Private Cloud — rede virtual isolada na AWS |
| RDS | Relational Database Service — banco de dados relacional gerenciado pela AWS |
| IaC | Infrastructure as Code — infraestrutura definida como código via AWS CDK |
| LGPD | Lei Geral de Proteção de Dados (Lei nº 13.709/2018) |

## 1.4. Referências

* AWS Well-Architected Framework.
* Lei Geral de Proteção de Dados (LGPD — Lei nº 13.709/2018).
* Plano de Ensino da Disciplina: Big Data e Cloud Computing (5º Período).
* INEP — Gabarito Oficial ENEM 2023.

# 2. Posicionamento

## 2.1. Oportunidade de Negócio

Após a publicação do gabarito pelo INEP, estudantes buscam verificar seu desempenho rapidamente. Os simuladores gratuitos existentes calculam apenas o percentual de acertos sem aplicar a metodologia TRI real. O Apollo entrega uma análise mais precisa — nota TRI estimada com base no gabarito oficial — usando uma arquitetura cloud-native na AWS que separa os fluxos de ingestão e gestão.

## 2.2. Descrição do Problema

|  |  |
| --- | --- |
| **O problema de...** | Simuladores de ENEM que calculam apenas o percentual bruto de acertos, sem aplicar a metodologia TRI do INEP, entregando ao candidato uma estimativa de nota diferente da real. |
| **Afeta...** | Estudantes que realizaram o ENEM e querem uma estimativa de nota mais próxima da metodologia oficial para planejar as próximas etapas (sisu, prouni, reinscrição). |
| **Cujo impacto é...** | Decisões baseadas em estimativas incorretas de nota — o candidato pode acreditar que atingiu a nota de corte de um curso quando na realidade ficou abaixo. |
| **Uma solução bem-sucedida incluiria...** | Uma aplicação web simples onde o candidato digita as respostas, a nota TRI é calculada com o gabarito oficial do INEP e o resultado é exibido imediatamente — hospedada na AWS com arquitetura cloud-native demonstrável em sala de aula. |

## 2.3. Posicionamento do Produto

Para estudantes que realizaram o ENEM 2023, o Apollo é um sistema web de análise de gabarito que estima a nota TRI com base no gabarito oficial do INEP. Diferente de calculadoras simples de percentual, aplica o modelo matemático TRI. Desenvolvido como projeto acadêmico da disciplina de Cloud Computing, demonstra na prática o uso integrado de EC2, RDS, Lambda, DynamoDB, S3, CloudFront, Secrets Manager e CodePipeline.

# 3. Descrição dos Stakeholders e Usuários

| **Stakeholder (Perfil)** | **Necessidade Primária** | **Expectativa na Nuvem (AWS)** |
| --- | --- | --- |
| Estudantes do ENEM 2023 | Digitar as respostas e ver rapidamente a nota TRI estimada e quais questões erraram. | Página que carrega sem demora, formulário simples e resultado exibido em poucos segundos, sem necessidade de cadastro. |
| Equipe Acadêmica (professor) | Validar que os serviços AWS obrigatórios foram utilizados corretamente e que a arquitetura é justificada. | Todos os serviços da ementa em funcionamento e evidenciados durante a defesa oral: EC2, RDS, Lambda, DynamoDB, S3, CloudFront, Secrets Manager e CodePipeline. |
| Equipe de Desenvolvimento (grupo) | Implementar, deployar e apresentar uma solução funcional dentro de 20 semanas com os conhecimentos adquiridos na disciplina. | Infraestrutura reproduzível via CDK, pipeline de deploy automático e código organizado para fácil manutenção durante o semestre. |

# 4. Visão Geral do Produto/Solução

## 4.1. Perspectiva do Produto

O Apollo é uma aplicação web hospedada na AWS com dois fluxos independentes. O frontend HTML estático (S3 + CloudFront) coleta as 45 respostas do candidato e envia para o endpoint serverless. A função Lambda recebe as respostas, busca o gabarito do ENEM 2025 no RDS, executa o cálculo TRI em Python puro e retorna o resultado. A API Django no EC2 gerencia os dados administrativos — gabaritos no banco e histórico de submissões. O DynamoDB armazena sessões temporárias durante o preenchimento do formulário.

## 4.2. Funcionalidades Principais

* Formulário de respostas: o candidato escolhe a área (LC, CH, CN ou MT) e preenche as 45 respostas (A a E ou em branco).
* Cálculo TRI: a Lambda executa a engine Python com o gabarito oficial do ENEM 2025 e retorna a nota estimada.
* Exibição do resultado: nota TRI estimada, contagem de acertos, erros e brancos, e lista das questões erradas com a resposta correta.
* Histórico simples: submissões salvas no RDS para consulta administrativa via API Django.

## 4.3. Suposições e Dependências

Suposições: o gabarito oficial do ENEM 2025 está disponível no site do INEP e será inserido no RDS via script de seed antes das apresentações; a conta AWS tem créditos acadêmicos suficientes para o semestre.

Dependências: o script de seed deve ser executado com sucesso antes de qualquer demonstração — sem gabarito no RDS a Lambda retorna erro. O frontend deve estar no S3 antes da defesa final.

# 5. Recursos do Produto (Arquitetura AWS)

| **Serviço AWS** | **Papel na Arquitetura** | **Justificativa Técnica (Por que usar?)** |
| --- | --- | --- |
| Amazon VPC | Rede isolada para os recursos do projeto | Sub-rede pública para o ALB e API Gateway; sub-rede privada para EC2 e RDS. Security Groups garantem que o RDS só aceita conexões do EC2 e da Lambda, nunca diretamente da internet. |
| Amazon EC2 + Nginx/Gunicorn | Servidor da API Django | Instância t3.micro para hospedar a API administrativa em Django REST Framework. Nginx como proxy reverso. Dimensionamento mínimo adequado ao projeto acadêmico. |
| Amazon RDS PostgreSQL | Banco de dados dos gabaritos e histórico | Armazena o gabarito do ENEM 2025 (4 áreas × 45 questões = 180 registros do ENEM 2025) e o histórico de submissões. Instância db.t3.micro com backup automático diário habilitado. |
| Amazon DynamoDB | Sessões temporárias do formulário | Armazena o rascunho das respostas enquanto o candidato preenche o formulário, com TTL de 30 minutos — expiram automaticamente. Demonstra o uso de banco NoSQL conforme ementa, com custo praticamente zero. |
| AWS Lambda + API Gateway | Processamento das respostas (endpoint principal) | API Gateway recebe as 45 respostas via POST. A Lambda busca o gabarito no RDS, calcula a nota TRI em Python puro e retorna o resultado. Serverless: custo zero quando não há uso. |
| Amazon S3 + CloudFront | Frontend e arquivos estáticos | S3 hospeda a página HTML do formulário. CloudFront entrega o conteúdo com HTTPS sem passar pelo EC2. Simples, barato e suficiente para o projeto. |
| AWS CodePipeline + CodeBuild | Deploy automático | Pipeline que detecta push no repositório Git, executa os testes e faz deploy da API Django no EC2 e da função Lambda automaticamente — sem deploy manual. |
| Amazon CloudWatch | Monitoramento básico | Logs da Lambda e do EC2. Um alarme simples para erros da Lambda. Suficiente para acompanhar o funcionamento durante o desenvolvimento e as apresentações. |
| AWS Secrets Manager | Credenciais do banco | Senha do RDS armazenada e injetada em tempo de execução. Nenhuma credencial no código ou no repositório Git. |

# 6. Restrições do Projeto

### Orçamentária

Máximo de US$ 1.500/mês. Custo real esperado: US$ 80–150/mês com t3.micro (EC2), db.t3.micro (RDS), Lambda e DynamoDB on-demand, S3 e CloudFront. Ampla margem para os testes e apresentações do semestre.

### Prazo

20 semanas. Semanas 1–6: setup AWS, VPC, RDS, EC2 básico. Semanas 7–12: Lambda, API Gateway, DynamoDB, seed do gabarito. Semanas 13–17: frontend, CloudFront, CodePipeline. Semanas 18–20: testes, ajustes e defesa oral.

### Tecnológica

Python com Django REST Framework. Engine TRI em Python puro dentro da Lambda. Infraestrutura como código via AWS CDK em Python. Gabarito fixo (ENEM 2025) — sem funcionalidade de múltiplos cadernos nesta versão.

### Segurança

HTTPS em todos os endpoints públicos (API Gateway e CloudFront). Credenciais do banco no Secrets Manager. IAM com permissões mínimas por serviço. Nenhuma senha no repositório Git.

### Pessoal

Quatro a cinco estudantes com papéis de desenvolvimento backend e infraestrutura. Todos aprendem e contribuem com os serviços AWS.

# 7. Atributos de Qualidade (SLAs e SLOs)

### Disponibilidade

O sistema deve estar funcionando durante todas as avaliações e apresentações da disciplina. Manutenções e indisponibilidades fora das janelas de avaliação são aceitáveis.

### Performance

O resultado da análise deve aparecer em até 5 segundos após o envio do formulário em condições normais de rede. Verificação manual durante a demonstração é o critério de aceitação.

### Segurança

HTTPS obrigatório. Credenciais exclusivamente no Secrets Manager. Sem dados pessoais além do mínimo necessário para o funcionamento do sistema.

### Continuidade

Backup automático diário habilitado no RDS (retenção de 7 dias). Infraestrutura reproduzível via CDK — qualquer membro da equipe pode recriar o ambiente. Perda máxima aceitável: dados do dia (projeto acadêmico).

### Custo

Faturamento mensal abaixo de US$ 1.500. AWS Budgets com alerta em 80% do limite (US$ 1.200) enviado por e-mail para a equipe.

# 8. Aprovação e Histórico de Versões

| **Versão** | **Data** | **Descrição da Alteração** | **Autor(es)** |
| --- | --- | --- | --- |
| 1.0 | 2026 | Elaboração inicial — escopo reduzido para garantia de entrega no semestre. | Equipe Apollo |
| 1.1 | — | Ajustes após feedback do professor orientador. | — |
| 2.0 | — | Revisão final para entrega na fase de Transição. | — |
