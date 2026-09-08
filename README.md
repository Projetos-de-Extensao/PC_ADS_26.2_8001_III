# Projeto Apollo — Análise de Gabarito do ENEM

**Código da Disciplina**: IBM8936<br>
**Disciplina**: Big Data e Cloud Computing (5º período)<br>

## Sobre

O Apollo é um sistema web de análise de gabarito do ENEM implantado na nuvem AWS. O candidato seleciona uma área de conhecimento (LC, CH, CN ou MT), preenche as 45 respostas da prova e recebe a nota estimada, as contagens de acertos, erros e questões em branco e a lista das questões erradas com o gabarito correto. A estimativa é produzida por uma engine TRI em Python puro, executada em AWS Lambda a partir do gabarito oficial e dos parâmetros de item publicados pelo INEP — e não corresponde à nota oficial do exame.

O projeto é acadêmico e tem como objetivo demonstrar, em um sistema funcional, o uso integrado dos serviços de nuvem estudados na disciplina. Esta versão trabalha com um gabarito fixo (ENEM 2025, caderno azul), carregado no banco por script de seed.

A documentação completa do projeto está em [docs/](docs/), com destaque para o [Documento de Visão](docs/Iniciacao/documento_de_visao.md) e o [Levantamento de Requisitos](docs/Elaboracao/levreq.md).

### Arquitetura

| Serviço AWS | Papel |
| -- | -- |
| Amazon VPC | Rede isolada: sub-rede pública para o load balancer da API administrativa; sub-rede privada para EC2 e RDS |
| Amazon EC2 (Nginx + Gunicorn) | API administrativa em Django REST Framework |
| Amazon RDS (PostgreSQL) | Gabarito, parâmetros de item e histórico de submissões |
| Amazon DynamoDB | Sessões temporárias do formulário, com TTL de 30 minutos |
| AWS Lambda + Amazon API Gateway | Endpoint de análise e execução da engine TRI |
| Amazon S3 + Amazon CloudFront | Frontend HTML estático distribuído com HTTPS |
| AWS CodePipeline + CodeBuild + CodeDeploy | Testes e implantação automática a partir do repositório |
| Amazon CloudWatch | Logs e alarme de taxa de erro da função Lambda |
| AWS Secrets Manager | Credencial do banco de dados |

## Instalação

**Linguagens**: Python, Django (Django REST Framework)<br>
**Infraestrutura como código**: AWS CDK em Python<br>
**Tecnologias**: AWS, GitHub, Visual Studio Code<br>

Pré-requisitos para executar o projeto:

- conta AWS com credenciais configuradas localmente;
- Python e AWS CDK instalados;
- gabarito oficial e parâmetros de item do ENEM 2025 disponíveis para a carga inicial.

Etapas de implantação:

1. provisionar a infraestrutura com `cdk deploy`;
2. executar o script de seed, que carrega o gabarito e os parâmetros de item no Amazon RDS — sem essa etapa a análise não pode ser realizada;
3. publicar o frontend no bucket S3;
4. verificar a implantação automática pelo AWS CodePipeline a partir de um push na branch principal.
