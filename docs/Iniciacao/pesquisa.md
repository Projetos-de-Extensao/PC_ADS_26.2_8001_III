---
id: pesquisa
title: Pesquisa
---

# Pesquisa
### **1. Capa**

- Tema: Análise de gabarito do ENEM com estimativa de nota pela metodologia TRI em arquitetura de nuvem AWS
- Data: 2026
- Stakeholder: Equipe acadêmica da disciplina Big Data e Cloud Computing (professor orientador)

---

### **2. Pesquisa**

- **Contexto do Projeto**

<p align = "justify">
Após a divulgação do gabarito oficial pelo INEP, estudantes procuram verificar rapidamente seu desempenho no exame. Os simuladores gratuitos disponíveis calculam apenas o percentual bruto de acertos e não aplicam a Teoria de Resposta ao Item (TRI), metodologia efetivamente utilizada pelo INEP para compor a nota do ENEM. A estimativa obtida por esses simuladores pode, portanto, divergir de forma relevante da nota real do candidato.
</p>

- **Objetivo**

<p align = "justify">
Entregar uma aplicação web que estime a nota do candidato por área de conhecimento aplicando um modelo TRI, a partir do gabarito oficial e dos parâmetros de item publicados pelo INEP, e que simultaneamente sirva de demonstração prática dos serviços de nuvem estudados na disciplina.
</p>

- **Público-Alvo**

<p align = "justify">
Estudantes que realizaram o ENEM e precisam de uma estimativa mais próxima da metodologia oficial para planejar as etapas seguintes, como a inscrição no SiSu e no ProUni ou a decisão por uma nova inscrição no exame. Secundariamente, a equipe acadêmica da disciplina, que avalia a arquitetura implementada.
</p>

- **Escopo**

<p align = "justify">
Formulário web para as 45 respostas de uma área de conhecimento (LC, CH, CN ou MT), cálculo da nota estimada, exibição do resultado com acertos, erros, brancos e questões erradas, e registro das submissões. O gabarito é fixo — ENEM 2025, caderno azul —, carregado no banco por script de seed. Estão fora do escopo: seleção de ano e caderno, análise por competência e habilidade, autenticação de usuários, painel para professores e múltiplas edições do exame.
</p>

- **Análise de aplicações e mercado**

<p align = "justify">
A pesquisa registrada nos documentos de Iniciação identifica, entre as soluções gratuitas já disponíveis, a limitação comum de calcular somente o percentual bruto de acertos, sem aplicar a metodologia TRI. É nessa lacuna que o Apollo se posiciona: estimar a nota a partir do gabarito oficial e dos parâmetros de item de cada questão, e não apenas contabilizar acertos. Não foi realizada, nesta fase, comparação sistemática com produtos específicos do mercado — um levantamento comparativo formal permanece como atividade em aberto.
</p>

- **Levantamento de Legislação**

<p align = "justify">
A Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018) é a principal referência legal aplicável. O projeto adota o princípio da necessidade: o sistema coleta apenas as respostas informadas pelo candidato para a área selecionada, sem exigir qualquer dado pessoal identificável e sem autenticação de usuários. Somam-se a isso as medidas técnicas previstas nos requisitos de segurança — HTTPS obrigatório nos endpoints públicos, criptografia em repouso no Amazon RDS e no Amazon DynamoDB, credenciais mantidas exclusivamente no AWS Secrets Manager e políticas IAM de menor privilégio.
</p>

---

### **3. Referências**

> BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD).

> INEP. Gabarito oficial e microdados do ENEM 2025.

> AWS Well-Architected Framework. Amazon Web Services.

### **4. Versionamento**

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 2026 | 1.0 | Registro da pesquisa de contexto, mercado e legislação do projeto Apollo. | Equipe Apollo (`<a definir>`) |
