---
id: levantamento de requisitos
title: Levantamento de Requisitos
---
# **06 - Levantamento de Requisitos e Caso de Uso**

**Sistema:** Apollo — Análise de Gabarito do ENEM (plataforma AWS)

<p align = "justify">
Este documento consolida os stakeholders, os requisitos funcionais e os requisitos não funcionais do projeto Apollo, derivados do Documento de Visão e do Documento de Requisitos Suplementares. Os requisitos não funcionais preservam os identificadores definidos nas fontes, de modo a manter a rastreabilidade entre os artefatos.
</p>

---

## **1. Identificação dos Stakeholders**

- **Estudantes do ENEM:** usuários finais; informam suas respostas e consultam a nota estimada e as questões erradas. Não se cadastram nem se autenticam no sistema.
- **Equipe acadêmica (professor orientador):** avalia o projeto; precisa constatar que os serviços AWS exigidos pela ementa estão em operação e que as decisões de arquitetura estão justificadas.
- **Equipe de desenvolvimento:** de quatro a cinco estudantes responsáveis pelo código da API Django e da engine TRI, pela infraestrutura em AWS CDK, pelo seed do gabarito, pelo monitoramento e pela correção de defeitos antes das avaliações.
- **AWS (provedor de nuvem):** responde pela disponibilidade dos serviços gerenciados utilizados — EC2, RDS, Lambda, DynamoDB, S3, CloudFront e API Gateway — conforme os SLAs publicados pelo próprio provedor.

---

### **2. Requisitos Funcionais**

| ID   | Descrição | Prioridade |
| ---- | --------- | ---------- |
| RF01 | O sistema deve permitir que o candidato selecione a área de conhecimento a ser analisada (LC, CH, CN ou MT). | Alta |
| RF02 | O sistema deve permitir o preenchimento das 45 respostas da área selecionada, aceitando as alternativas de A a E ou a marcação em branco. | Alta |
| RF03 | O sistema deve persistir o rascunho das respostas como sessão temporária enquanto o formulário é preenchido, com expiração automática em 30 minutos. | Média |
| RF04 | O sistema deve calcular a nota estimada da área a partir do gabarito oficial e dos parâmetros de item armazenados no banco, por meio da engine TRI. | Alta |
| RF05 | O sistema deve apresentar ao candidato a nota estimada e as contagens de acertos, erros e questões em branco. | Alta |
| RF06 | O sistema deve listar as questões erradas, indicando a alternativa marcada e a resposta correta. | Alta |
| RF07 | O sistema deve registrar cada submissão no banco relacional, compondo o histórico de análises. | Média |
| RF08 | A API administrativa deve permitir à equipe consultar os gabaritos cadastrados e o histórico de submissões. | Média |
| RF09 | O sistema deve permitir a carga do gabarito e dos parâmetros de item por script de seed, sem alteração de código ou de infraestrutura. | Alta |

---

### **3. Requisitos Não Funcionais**

Os requisitos a seguir reproduzem, com os identificadores de origem, o Documento de Requisitos Suplementares. A verificação é manual, realizada durante o desenvolvimento e as apresentações; não se prevê o uso de ferramentas de teste de carga nesta fase.

#### 3.1 Desempenho e capacidade

| ID | Requisito | Critério de aceitação |
| -- | --------- | --------------------- |
| RNF-PER-01 | A análise deve ser retornada em tempo adequado ao usuário. | O resultado aparece em até 5 segundos após o envio do formulário, em condições normais de rede, verificado manualmente durante a demonstração. |
| RNF-PER-02 | O sistema deve funcionar com múltiplos acessos simultâneos durante a apresentação. | Funciona sem erros com até 10 usuários simultâneos — volume típico de uma apresentação em sala de aula. |
| RNF-PER-03 | O frontend deve carregar rapidamente. | A página HTML carrega em até 3 segundos via CloudFront em conexão padrão. |
| RNF-CAP-01 | A inclusão de novos gabaritos deve ser simples. | A estrutura do banco permite adicionar novos cadernos executando o script de seed, sem alteração de código ou de infraestrutura. |

#### 3.2 Disponibilidade e confiabilidade

| ID | Requisito | Critério de aceitação |
| -- | --------- | --------------------- |
| RNF-CON-01 | O sistema deve estar disponível durante todas as avaliações da disciplina. | API, função Lambda e frontend funcionando sem erros nas apresentações e na defesa oral; indisponibilidades fora dessas janelas são aceitáveis. |
| RNF-CON-02 | O serviço Django deve retornar automaticamente após reinicialização da instância EC2. | Serviço configurado via systemd, reiniciando sem intervenção manual após um reboot; verificado com um teste de reinicialização. |
| RNF-CON-03 | Os dados do gabarito não devem ser perdidos. | RDS com backup automático diário habilitado e retenção de sete dias; o gabarito pode ser restaurado do backup ou reinserido pelo script de seed. |
| RNF-CON-04 | O ambiente deve ser reproduzível. | O comando `cdk deploy` recria toda a infraestrutura a partir do código versionado no Git, sem intervenção manual além das credenciais AWS. |

#### 3.3 Segurança e privacidade

| ID | Requisito | Critério de aceitação |
| -- | --------- | --------------------- |
| RNF-SEG-01 | Toda comunicação externa deve usar HTTPS. | API Gateway e CloudFront servem exclusivamente HTTPS, com redirecionamento automático de HTTP, e certificado gerenciado pelo AWS Certificate Manager. |
| RNF-SEG-02 | Os dados armazenados devem ter criptografia habilitada. | RDS e DynamoDB criados com criptografia em repouso habilitada. |
| RNF-SEG-03 | Cada serviço deve operar com o menor privilégio necessário. | A IAM Role da função Lambda concede apenas leitura do segredo do banco no Secrets Manager, leitura e escrita na tabela de sessões do DynamoDB, escrita de logs no CloudWatch e as permissões de rede necessárias para execução na VPC. A IAM Role da instância EC2 concede apenas leitura do mesmo segredo e escrita de logs. Nenhuma role de serviço possui permissões administrativas. O acesso ao banco PostgreSQL é controlado por Security Group e por credencial de banco, e não por política IAM. |
| RNF-SEG-04 | As credenciais do banco não podem aparecer no código nem no repositório. | Senha do RDS armazenada no AWS Secrets Manager e carregada em tempo de execução; repositório Git verificado, sem senhas ou chaves de acesso. |
| RNF-SEG-05 | Os dados pessoais devem ser mínimos. | O sistema coleta apenas as respostas informadas pelo candidato para a área selecionada; nenhum dado pessoal identificável é exigido para o uso do sistema, em linha com o princípio da necessidade previsto na LGPD. |

#### 3.4 Operação e observabilidade

| ID | Requisito | Critério de aceitação |
| -- | --------- | --------------------- |
| RNF-OPS-01 | A equipe deve conseguir verificar se os serviços estão funcionando. | CloudWatch Logs habilitado para a função Lambda e para a instância EC2; console AWS apresentando o estado dos serviços. |
| RNF-OPS-02 | Os erros da função Lambda devem ser visíveis. | Alarme no CloudWatch para taxa de erro da Lambda acima de 20%, com notificação por SNS para o e-mail da equipe. |
| RNF-OPS-03 | Os backups devem ocorrer automaticamente. | RDS com backup automático diário e retenção de sete dias, configurado na criação do recurso via CDK. |
| RNF-OPS-04 | O processo de implantação deve estar documentado. | README com instruções de execução do CDK, do script de seed e do pipeline, permitindo que qualquer integrante replique o ambiente. |

#### 3.5 Manutenibilidade e entrega

| ID | Requisito | Critério de aceitação |
| -- | --------- | --------------------- |
| RNF-MAN-01 | A implantação deve ser automática após push no repositório. | O CodePipeline detecta o push na branch principal e executa os testes com pytest, a implantação da API Django no EC2 e a atualização da função Lambda, sem acesso manual ao servidor. |
| RNF-MAN-02 | Deve ser possível restaurar a versão anterior em caso de problema. | O CodeDeploy mantém a versão anterior disponível para rollback manual pela equipe em até 10 minutos. |
| RNF-MAN-03 | Toda a infraestrutura deve estar definida como código. | AWS CDK em Python define todos os recursos; qualquer integrante recria o ambiente com `cdk deploy`, sem uso do console AWS. |
| RNF-MAN-04 | O projeto deve ter documentação mínima para entrega. | README contendo descrição do projeto, instruções de implantação, descrição de cada serviço AWS utilizado e execução do script de seed. |

#### 3.6 Usabilidade

| ID | Requisito | Critério de aceitação |
| -- | --------- | --------------------- |
| RNF-USA-01 | O formulário deve ser utilizável sem instruções prévias. | Um usuário consegue selecionar a área, preencher as respostas e enviar sem tutorial; verificado com um colega de outro grupo durante os testes. |
| RNF-USA-02 | O resultado deve ser claro e compreensível. | A página de resultado apresenta nota estimada, acertos, erros, brancos e a lista de questões erradas com o gabarito correto, sem jargão técnico. |
| RNF-USA-03 | Os erros da API devem ser claros e não expor detalhes internos. | As respostas de erro retornam código HTTP adequado (400 ou 500) e mensagem descritiva, sem expor credenciais, stack trace ou detalhes de infraestrutura. |

#### 3.7 Custo

| ID | Requisito | Critério de aceitação |
| -- | --------- | --------------------- |
| RNF-CUS-01 | O custo mensal deve permanecer dentro do orçamento. | Faturamento abaixo de US$ 1.500/mês; custo esperado de US$ 80 a US$ 150 com EC2 t3.micro, RDS db.t3.micro e serviços sob demanda. |
| RNF-CUS-02 | O custo deve ser acompanhado. | AWS Budgets configurado com alerta em US$ 1.200 (80% do limite), enviado por e-mail à equipe. |
| RNF-CUS-03 | Os recursos devem ser dimensionados para uso acadêmico. | Instâncias mínimas (t3.micro e db.t3.micro); Lambda e DynamoDB sob demanda, sem custo quando o sistema não está em uso. |

> Disponibilidade e segurança básicas não são sacrificadas para reduzir custo: o dimensionamento mínimo já mantém o gasto bastante abaixo do orçamento aprovado.

---

### **4. Caso de Uso Principal**

#### **UC01 - Analisar Gabarito**

- **Atores:** Candidato, Sistema Apollo.
- **Pré-condição:** o gabarito e os parâmetros de item da área selecionada estão carregados no banco relacional.
- **Fluxo Principal:**
  1. O candidato acessa o formulário web.
  2. O candidato seleciona a área de conhecimento (LC, CH, CN ou MT).
  3. O candidato preenche as 45 respostas, marcando alternativas de A a E ou deixando questões em branco.
  4. O sistema registra o rascunho como sessão temporária, com expiração em 30 minutos.
  5. O candidato envia o formulário.
  6. O sistema recupera o gabarito e os parâmetros de item da área e executa a engine TRI.
  7. O sistema registra a submissão no histórico.
  8. O sistema apresenta a nota estimada, as contagens de acertos, erros e brancos e a lista das questões erradas com a resposta correta.
- **Fluxos Alternativos:**
  - **FA1:** conjunto de respostas inválido (área não informada ou quantidade de respostas diferente de 45) → o sistema retorna erro de validação com código HTTP 400 e mensagem descritiva, sem expor detalhes internos.
  - **FA2:** gabarito ou parâmetros de item ausentes para a área solicitada → o sistema não realiza a análise e retorna mensagem de indisponibilidade da análise; a equipe deve executar o script de seed.
  - **FA3:** falha na comunicação com o banco de dados → o sistema retorna erro com código HTTP 500 e mensagem genérica, e o evento é registrado no CloudWatch Logs.
- **Pós-condição:** o resultado é exibido ao candidato e a submissão fica registrada no histórico.

O diagrama de casos de uso e os demais cenários estão detalhados em [casos_de_uso.md](casos_de_uso.md). O detalhamento da interação entre os componentes deste caso de uso está em [diagrama_de_sequencia.md](diagrama_de_sequencia.md).

---

### **5. Telas Previstas**

O escopo desta versão prevê duas telas, servidas como página HTML estática pelo S3 e distribuídas via CloudFront:

- **Tela de preenchimento:** seleção da área de conhecimento e campos para as 45 respostas, com a opção de deixar questões em branco, além da ação de envio.
- **Tela de resultado:** nota estimada, contagens de acertos, erros e brancos e lista das questões erradas com a alternativa marcada e a resposta correta.

Não estão previstas telas de cadastro, autenticação ou administração: a API administrativa é consumida diretamente pela equipe, sem interface gráfica própria nesta versão.

---

### **6. Validação**

Os requisitos são considerados atendidos quando:

- todos os serviços AWS do escopo (EC2, RDS, Lambda, DynamoDB, S3, CloudFront, Secrets Manager e CodePipeline) estiverem configurados e demonstráveis;
- o formulário aceitar as respostas e a função Lambda retornar a nota estimada e a lista de questões erradas corretamente;
- o gabarito e os parâmetros de item do ENEM 2025 estiverem carregados no RDS e a correção conferir com o gabarito oficial;
- nenhuma credencial constar do repositório Git;
- o custo estimado permanecer abaixo de US$ 1.500/mês;
- o AWS CDK conseguir recriar o ambiente a partir do zero.

---

### **7. Riscos e Decisões Pendentes**

| Item | Impacto | Tratamento |
| -- | -- | -- |
| Script de seed não executar corretamente antes da apresentação | O sistema não consegue analisar as submissões, pois depende do gabarito e dos parâmetros de item no banco. | Executar o seed com pelo menos uma semana de antecedência e verificar o resultado; manter cópia do gabarito em arquivo CSV. |
| Publicação dos microdados do INEP com defasagem em relação à aplicação da prova | Sem os parâmetros de item da edição de 2025, a engine TRI não pode ser executada como especificada. | Confirmar a disponibilidade dos parâmetros antes da fase de Construção e, se necessário, definir alternativa com o professor orientador. |
| Custo do RDS mantido ligado 24 horas por dia | Instância db.t3.micro custa cerca de US$ 15 a US$ 20 por mês mesmo sem uso. | Aceitável dentro do orçamento; se necessário, desligar a instância nos períodos sem desenvolvimento e religá-la antes das apresentações. |
| Curva de aprendizado do AWS CDK | Atraso na configuração da infraestrutura. | Reservar as semanas 1 a 3 para o setup do CDK com um recurso simples (bucket S3) antes de adicionar RDS e Lambda. |
| Cold start da função Lambda | A primeira requisição após um período de inatividade pode levar de 2 a 3 segundos adicionais. | Aceitável para o contexto acadêmico; realizar um aquecimento manual com uma requisição de teste antes da apresentação. |
| Configuração incorreta do CodePipeline | A implantação automática não funciona, exigindo retorno ao processo manual. | Configurar e testar o pipeline na semana 13, mantendo a implantação manual como alternativa. |

---

### **8. Versionamento**

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 2026 | 1.0 | Consolidação dos requisitos a partir do Documento de Visão e do Documento de Requisitos Suplementares. | Equipe Apollo (`<a definir>`) |
