---
id: documento_de_visao
title: Documento de Visão
---
# Documento de Visão — Projeto Apollo

| Campo | Valor |
| -- | -- |
| Projeto | Apollo — Análise de Gabarito do ENEM |
| Disciplina | Big Data e Cloud Computing (5º período) |
| Fase | Iniciação (Inception) |
| Plataforma | Amazon Web Services (AWS) |
| Stack | Python · Django REST Framework · AWS |
| Versão | 1.0 |

## Introdução

<p align = "justify">
O propósito deste documento é fornecer uma visão geral do projeto Apollo, desenvolvido na disciplina de Big Data e Cloud Computing. O Apollo é um sistema web de análise de gabarito do ENEM, hospedado na nuvem AWS, cujo objetivo acadêmico é demonstrar, em um sistema funcional, o uso integrado dos principais serviços de nuvem estudados na disciplina. São descritos neste documento o problema abordado, os usuários envolvidos, as funcionalidades previstas, a arquitetura de nuvem adotada e as restrições que delimitam o escopo da solução.
</p>

## Descrição do Problema

<p align = "justify">
Após a publicação do gabarito oficial pelo INEP, estudantes procuram verificar rapidamente seu desempenho no exame. Os simuladores gratuitos disponíveis calculam apenas o percentual bruto de acertos e não aplicam a Teoria de Resposta ao Item (TRI), metodologia efetivamente utilizada pelo INEP para compor a nota do ENEM. Como consequência, a estimativa apresentada ao candidato pode divergir de forma relevante da nota real.
</p>

### Problema

Dificuldade em obter, logo após a divulgação do gabarito, uma estimativa de nota do ENEM que considere a metodologia TRI, e não apenas a contagem bruta de acertos.

### Impactados

Estudantes que realizaram o ENEM e precisam de uma estimativa de nota mais próxima da metodologia oficial para planejar as etapas seguintes, como a inscrição no SiSu e no ProUni ou a decisão por uma nova inscrição no exame.

### Consequência

Decisões tomadas com base em estimativas incorretas: o candidato pode acreditar que atingiu a nota de corte de um curso quando, na realidade, ficou abaixo dela.

### Solução

<p align = "justify">
Uma aplicação web simples na qual o candidato seleciona a área de conhecimento, informa suas respostas e recebe imediatamente a nota estimada, a contagem de acertos, erros e questões em branco e a lista das questões erradas com o gabarito correto. A estimativa é produzida por uma engine TRI executada em ambiente serverless, a partir do gabarito oficial e dos parâmetros de item divulgados pelo INEP. A solução é implantada na AWS com arquitetura cloud-native, de modo a ser demonstrável durante as avaliações da disciplina.
</p>

## Objetivos

<p align = "justify">
O objetivo da equipe de desenvolvimento é entregar, dentro do semestre acadêmico de 20 semanas, um sistema funcional de análise de gabarito do ENEM implantado na AWS, no qual todos os serviços de nuvem exigidos pela ementa estejam efetivamente em operação e possam ser evidenciados na defesa oral: Amazon EC2, Amazon RDS, AWS Lambda, Amazon DynamoDB, Amazon S3, Amazon CloudFront, AWS Secrets Manager e AWS CodePipeline. O escopo funcional foi deliberadamente reduzido para tornar essa entrega viável no prazo disponível.
</p>

## Descrição do Usuário

<p align = "justify">
O sistema atende a três perfis de interessados, descritos a seguir.
</p>

| Perfil | Necessidade primária | Expectativa em relação à solução em nuvem |
| -- | -- | -- |
| Estudante que realizou o ENEM | Informar suas respostas e visualizar rapidamente a nota estimada e as questões que errou. | Página que carrega sem demora, formulário simples e resultado exibido em poucos segundos, sem necessidade de cadastro. |
| Equipe acadêmica (professor orientador) | Validar que os serviços AWS obrigatórios foram utilizados corretamente e que as decisões de arquitetura estão justificadas. | Todos os serviços da ementa em funcionamento e evidenciados durante a defesa oral. |
| Equipe de desenvolvimento | Implementar, implantar e apresentar uma solução funcional em 20 semanas, com os conhecimentos adquiridos na disciplina. | Infraestrutura reproduzível por código (AWS CDK), pipeline de implantação automática e código organizado para manutenção ao longo do semestre. |

<p align = "justify">
O usuário final não se autentica no sistema: a análise é anônima e o formulário coleta apenas as respostas informadas pelo candidato.
</p>

## Recursos do produto

### Formulário de respostas

<p align = "justify">
O candidato seleciona uma das quatro áreas de conhecimento — Linguagens e Códigos (LC), Ciências Humanas (CH), Ciências da Natureza (CN) ou Matemática (MT) — e preenche as 45 respostas correspondentes, podendo marcar as alternativas de A a E ou deixar a questão em branco. A interface é uma página HTML estática, sem framework de frontend.
</p>

### Sessão temporária de preenchimento

<p align = "justify">
Enquanto o candidato preenche o formulário, o rascunho das respostas é persistido como sessão temporária no Amazon DynamoDB, com TTL de 30 minutos, de modo que os registros expiram automaticamente, sem necessidade de rotina de limpeza.
</p>

### Cálculo da nota estimada (engine TRI)

<p align = "justify">
Ao receber a submissão, uma função AWS Lambda consulta no Amazon RDS o gabarito oficial e os parâmetros de item da área analisada e executa a engine TRI — módulo em Python puro, sem dependências externas de cálculo — que estima a nota a partir do padrão de respostas do candidato. Os parâmetros de item (discriminação, dificuldade e acerto casual) são obtidos dos microdados publicados pelo INEP e carregados no banco pelo script de seed.
</p>

### Exibição do resultado

<p align = "justify">
O resultado apresentado ao candidato contém a nota estimada, o total de acertos, erros e questões em branco e a lista das questões erradas com a respectiva resposta correta, em linguagem sem jargão técnico.
</p>

### Histórico de submissões

<p align = "justify">
Cada submissão é registrada no Amazon RDS. A API administrativa em Django REST Framework, hospedada em Amazon EC2, permite à equipe consultar os gabaritos cadastrados e o histórico de submissões. Essa API não é exposta ao usuário final.
</p>

### Serviços AWS de suporte

| Serviço AWS | Papel na arquitetura | Justificativa técnica |
| -- | -- | -- |
| Amazon VPC | Rede isolada dos recursos do projeto | Sub-rede pública para o Application Load Balancer que expõe a API administrativa; sub-rede privada para EC2 e RDS. Os Security Groups garantem que o RDS aceite conexões apenas da instância EC2 e da função Lambda, nunca diretamente da internet. O API Gateway é um serviço regional gerenciado, externo à VPC; a função Lambda é anexada à VPC para alcançar o RDS na sub-rede privada. |
| Amazon EC2 (Nginx + Gunicorn) | Servidor da API administrativa Django | Instância t3.micro hospedando a API em Django REST Framework, com Nginx como proxy reverso e Gunicorn como servidor de aplicação. Dimensionamento mínimo, adequado ao porte do projeto acadêmico. |
| Amazon RDS (PostgreSQL) | Banco de gabaritos, parâmetros de item e histórico | Armazena o gabarito do ENEM 2025 (4 áreas × 45 questões = 180 questões), os parâmetros de item associados e o histórico de submissões. Instância db.t3.micro com backup automático diário habilitado. |
| Amazon DynamoDB | Sessões temporárias do formulário | Armazena o rascunho das respostas durante o preenchimento, com TTL de 30 minutos. Demonstra o uso de banco NoSQL previsto na ementa, com custo praticamente nulo no volume do projeto. |
| AWS Lambda + Amazon API Gateway | Processamento das respostas (endpoint principal) | O API Gateway recebe as respostas via POST e aciona a função Lambda, que consulta o gabarito e os parâmetros no RDS, executa a engine TRI e retorna o resultado. Modelo serverless, sem custo quando não há uso. |
| Amazon S3 + Amazon CloudFront | Frontend e arquivos estáticos | O S3 hospeda a página HTML do formulário e o CloudFront a distribui com HTTPS, sem tráfego pela instância EC2. |
| AWS CodePipeline + CodeBuild + CodeDeploy | Implantação automática | O pipeline detecta o push no repositório Git, executa os testes automatizados e implanta a API Django no EC2 e a função Lambda, eliminando a implantação manual. |
| Amazon CloudWatch | Monitoramento e observabilidade básica | Centraliza os logs da Lambda e do EC2 e sustenta o alarme de taxa de erro da função Lambda. |
| AWS Secrets Manager | Credenciais do banco de dados | A senha do RDS é armazenada no serviço e recuperada em tempo de execução pela API Django e pela função Lambda, evitando credenciais no código ou no repositório Git. |

## Restrições

<p align = "justify">
A aplicação não é responsável por reproduzir a nota oficial do ENEM: o resultado apresentado é uma estimativa produzida pela engine TRI da equipe a partir do gabarito e dos parâmetros de item publicados pelo INEP. As demais restrições do projeto estão organizadas a seguir.
</p>

### Escopo

<p align = "justify">
Esta versão trabalha com um gabarito fixo — ENEM 2025, caderno azul, contemplando as provas do primeiro dia (LC e CH) e do segundo dia (CN e MT) — carregado no banco por script de seed, sem seletor de edição ou de caderno na interface. Estão fora do escopo: seleção de ano e caderno, análise por competência e habilidade, autenticação de usuários, painel para professores e múltiplas edições do exame.
</p>

### Orçamentária

<p align = "justify">
Limite de US$ 1.500/mês. O custo mensal esperado é de US$ 80 a US$ 150, considerando EC2 t3.micro, RDS db.t3.micro, Lambda e DynamoDB sob demanda, S3 e CloudFront. O AWS Budgets é configurado com alerta por e-mail em US$ 1.200 (80% do limite).
</p>

### Prazo

<p align = "justify">
Semestre acadêmico de 20 semanas, organizado em quatro blocos: semanas 1 a 6 — configuração da conta AWS, VPC, RDS e EC2; semanas 7 a 12 — Lambda, API Gateway, DynamoDB e seed do gabarito; semanas 13 a 17 — frontend, CloudFront e CodePipeline; semanas 18 a 20 — testes, ajustes e defesa oral.
</p>

### Tecnológica

<p align = "justify">
Python com Django REST Framework na API administrativa e engine TRI em Python puro executada na função Lambda. Toda a infraestrutura é definida como código com AWS CDK em Python.
</p>

### Segurança

<p align = "justify">
HTTPS obrigatório em todos os endpoints públicos (API Gateway e CloudFront), credenciais exclusivamente no AWS Secrets Manager, políticas IAM de menor privilégio por serviço e nenhuma senha versionada no repositório Git.
</p>

### Pessoal

<p align = "justify">
Equipe de quatro a cinco estudantes, com atuação dividida entre desenvolvimento backend e infraestrutura; todos os integrantes participam da implementação dos serviços AWS.
</p>

### Atributos de qualidade (SLOs)

| Atributo | Objetivo | Forma de verificação |
| -- | -- | -- |
| Disponibilidade | Sistema em funcionamento durante todas as avaliações e apresentações da disciplina; indisponibilidades fora dessas janelas são aceitáveis. | Verificação da equipe antes de cada avaliação. |
| Desempenho | Resultado da análise exibido em até 5 segundos após o envio do formulário, em condições normais de rede. | Verificação manual durante a demonstração. |
| Segurança | HTTPS em todos os endpoints públicos, credenciais apenas no Secrets Manager e coleta mínima de dados. | Inspeção da configuração e do repositório. |
| Continuidade | Backup automático diário do RDS com sete dias de retenção e infraestrutura recriável por `cdk deploy`. Perda máxima aceitável: os dados do dia. | Recriação do ambiente a partir do código versionado. |
| Custo | Faturamento mensal abaixo de US$ 1.500. | Alerta do AWS Budgets em US$ 1.200. |

## Suposições e Dependências

<p align = "justify">
Supõe-se que a conta AWS disponha de créditos acadêmicos suficientes para todo o semestre e que o gabarito oficial e os parâmetros de item do ENEM 2025 possam ser obtidos junto ao INEP e inseridos no RDS por script de seed antes das apresentações. A execução bem-sucedida desse script é pré-condição para qualquer demonstração: sem gabarito e sem parâmetros de item no banco, a função Lambda não consegue produzir o resultado. O frontend deve estar publicado no S3 antes da defesa final.
</p>

<p align = "justify">
Registra-se como dependência externa que os microdados do INEP, dos quais provêm os parâmetros de item, são publicados com defasagem em relação à aplicação da prova. Caso os parâmetros da edição de 2025 não estejam disponíveis a tempo, a equipe precisará definir com o professor orientador uma alternativa antes da fase de Construção.
</p>

## Referências Bibliográficas

> AWS Well-Architected Framework. Amazon Web Services.

> BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD).

> INEP. Gabarito oficial e microdados do ENEM 2025.

> Plano de Ensino da disciplina Big Data e Cloud Computing (5º período).

## Versionamento

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 2026 | 1.0 | Elaboração inicial — escopo reduzido para garantir a entrega no semestre. | Equipe Apollo (`<a definir>`) |
| `<a definir>` | 1.1 | Ajustes após feedback do professor orientador. | `<a definir>` |
| `<a definir>` | 2.0 | Revisão final para entrega na fase de Transição. | `<a definir>` |
