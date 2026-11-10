"""Eixos e temas do ENEM, derivados dos "Objetos de conhecimento associados às Matrizes de Referência" (edital).

eixo = agrupamento do edital (ex.: Física, Conhecimentos geométricos); tema = tópico dentro do eixo.
Lista fechada: a classificação de cada questão (data/classificacao_questoes.csv) só pode usar estes códigos.
"""

# área -> eixo -> [(código do tema, descrição)]
EIXOS = {
    "MT": {
        "Conhecimentos numéricos": [
            ("operacoes_numeros", "Operações com números naturais, inteiros, racionais e reais"),
            ("divisibilidade_fatoracao", "Divisibilidade e fatoração"),
            ("razao_proporcao", "Razões e proporções"),
            ("porcentagem_juros", "Porcentagem e juros"),
            ("grandezas_dependencia", "Relações de dependência entre grandezas"),
            ("sequencias_progressoes", "Sequências e progressões"),
            ("contagem", "Princípios de contagem"),
        ],
        "Conhecimentos geométricos": [
            ("figuras_planas_espaciais", "Características e propriedades de figuras planas e espaciais"),
            ("unidades_escalas", "Unidades de medida e escalas"),
            ("comprimento_area_volume", "Comprimentos, áreas e volumes"),
            ("angulos_retas_simetria", "Ângulos, posições de retas e simetria"),
            ("congruencia_semelhanca", "Congruência e semelhança de triângulos; Teorema de Tales"),
            ("trigonometria_triangulo", "Relações métricas e trigonometria no triângulo"),
            ("circunferencia_circulo", "Circunferência e círculo"),
        ],
        "Conhecimentos de estatística e probabilidade": [
            ("dados_graficos_tabelas", "Representação e análise de dados (gráficos e tabelas)"),
            ("medidas_centrais_dispersao", "Média, moda, mediana, desvio e variância"),
            ("probabilidade", "Noções de probabilidade"),
        ],
        "Conhecimentos algébricos": [
            ("funcoes", "Gráficos e funções (afim, quadrática, polinomial, exponencial, logarítmica)"),
            ("equacoes_sistemas", "Equações, inequações e sistemas"),
            ("trigonometria_funcoes", "Círculo trigonométrico e funções trigonométricas"),
            ("geometria_analitica", "Plano cartesiano, retas e circunferências"),
        ],
    },
    "CN": {
        "Física": [
            ("fis_medidas_vetores", "Conhecimentos básicos: grandezas, SI, notação científica e vetores"),
            ("fis_movimento_leis", "Movimento, equilíbrio e leis físicas (cinemática, Newton, quantidade de movimento)"),
            ("fis_hidrostatica", "Hidrostática"),
            ("fis_energia_trabalho", "Energia, trabalho e potência"),
            ("fis_gravitacao", "Gravitação e funcionamento do Universo"),
            ("fis_eletromagnetismo", "Fenômenos elétricos e magnéticos"),
            ("fis_ondas_optica", "Oscilações, ondas, óptica e radiação"),
            ("fis_termologia", "Calor e fenômenos térmicos"),
        ],
        "Química": [
            ("qui_reacoes_estequiometria", "Transformações e reações químicas, balanceamento e estequiometria"),
            ("qui_gases", "Sistemas gasosos"),
            ("qui_atomistica_periodica", "Modelos atômicos, estrutura atômica e Tabela Periódica"),
            ("qui_materiais_misturas", "Materiais, propriedades e misturas"),
            ("qui_ligacoes_substancias", "Substâncias químicas e ligações"),
            ("qui_solucoes", "Água e soluções (solubilidade, concentração, propriedades coligativas)"),
            ("qui_acidos_bases", "Ácidos, bases, sais e óxidos"),
            ("qui_termoquimica", "Transformações químicas e energia (termoquímica)"),
            ("qui_eletroquimica", "Transformações químicas e energia elétrica (pilhas, eletrólise)"),
            ("qui_nuclear", "Transformações nucleares e radioatividade"),
            ("qui_cinetica_equilibrio", "Velocidade das reações e equilíbrio químico"),
            ("qui_organica", "Compostos de carbono e química orgânica"),
            ("qui_macromoleculas", "Macromoléculas naturais e sintéticas"),
            ("qui_sociedade_ambiente", "Química, tecnologia, sociedade e meio ambiente"),
        ],
        "Biologia": [
            ("bio_celulas_moleculas", "Moléculas, células e tecidos; metabolismo"),
            ("bio_biotecnologia", "Biotecnologia e sustentabilidade"),
            ("bio_genetica", "Hereditariedade e genética"),
            ("bio_evolucao", "Evolução e origem da vida"),
            ("bio_diversidade", "Identidade e diversidade dos seres vivos"),
            ("bio_fisiologia_humana", "Embriologia, anatomia e fisiologia humana"),
            ("bio_ecologia", "Ecologia e ciências ambientais"),
            ("bio_problemas_ambientais", "Problemas ambientais e conservação da biodiversidade"),
            ("bio_saude", "Saúde, doenças e qualidade de vida"),
        ],
    },
    "CH": {
        "História": [
            ("his_cultura_identidades", "Cultura material e imaterial, identidades e diversidade cultural"),
            ("his_america_escravidao", "Conquista da América, escravidão e resistência indígena e africana"),
            ("his_antiguidade_moderna", "Cidadania na Antiguidade, Estado moderno e revoluções europeias"),
            ("his_brasil_imperio", "Independências americanas e Brasil Imperial"),
            ("his_brasil_republica", "Brasil República, ditaduras e direitos nas constituições"),
            ("his_seculo_xx", "Revoluções, totalitarismos, guerras mundiais e Guerra Fria"),
            ("his_trabalho_producao", "Formas de produção e trabalho (Revolução Industrial, fordismo, economia agroexportadora)"),
            ("his_movimentos_culturais", "Movimentos culturais no Ocidente"),
        ],
        "Geografia": [
            ("geo_territorio_brasil", "Formação territorial, regiões brasileiras e migrações"),
            ("geo_urbanizacao", "Vida urbana, redes de cidades e espaço urbano-industrial"),
            ("geo_agrario", "Espaço agrário, agronegócio e relação campo-cidade"),
            ("geo_globalizacao", "Globalização, tecnologias de telecomunicação e geopolítica"),
            ("geo_cartografia", "Representação espacial e cartografia"),
            ("geo_natureza_relevo_clima", "Estrutura da Terra, solo, relevo, clima e vegetação"),
            ("geo_recursos_naturais", "Recursos minerais, energéticos e hídricos"),
            ("geo_ambiente_sustentabilidade", "Questões ambientais, políticas ambientais e sustentabilidade"),
        ],
        "Filosofia": [
            ("fil_politica_democracia", "Filosofia política: democracia, liberalismo e seus críticos"),
            ("fil_outros", "Outros temas de Filosofia (ética, conhecimento, estética, antropologia filosófica)"),
        ],
        "Sociologia": [
            ("soc_organizacao_movimentos", "Organização social, movimentos sociais e ação do Estado"),
            ("soc_direitos_cidadania", "Direitos, cidadania e políticas afirmativas"),
            ("soc_outros", "Outros temas de Sociologia (cultura, trabalho, desigualdade, indivíduo e sociedade)"),
        ],
    },
    "LC": {
        "Língua estrangeira": [
            ("le_lingua_estrangeira", "Língua estrangeira moderna (inglês ou espanhol)"),
        ],
        "Língua portuguesa e texto": [
            ("lp_generos_texto", "Estudo do texto e gêneros textuais"),
            ("lp_organizacao_argumentacao", "Organização, progressão, coesão e argumentação"),
            ("lp_norma_variacao", "Norma culta e variação linguística"),
            ("lp_recursos_linguisticos", "Recursos linguísticos, registro e contexto"),
        ],
        "Literatura": [
            ("lit_movimentos_contexto", "Texto literário, movimentos e contexto social"),
            ("lit_generos_recursos", "Gêneros literários e recursos expressivos"),
            ("lit_relacoes_artes", "Relações entre literatura e outras artes"),
        ],
        "Artes": [
            ("art_visuais", "Artes visuais"),
            ("art_cenicas_musica", "Teatro, dança e música"),
            ("art_cultura_identidade", "Arte, cultura, diversidade e identidade"),
        ],
        "Práticas corporais": [
            ("cor_saude_exercicio", "Corpo, exercício físico e saúde"),
            ("cor_esporte_jogos_lazer", "Esporte, jogos, lutas, dança e lazer"),
        ],
        "Tecnologias da informação e comunicação": [
            ("tic_generos_digitais", "Gêneros digitais e função social das tecnologias"),
        ],
    },
}

# Código "outro" aceito em qualquer área quando o item não se enquadra (ex.: depende de figura não extraída).
OUTRO = "outro"


def mapa_tema_eixo(area):
    return {cod: eixo for eixo, temas in EIXOS[area].items() for cod, _ in temas}


def eixo_de(area, tema):
    return mapa_tema_eixo(area).get(tema, "Outro")


def eixos_publico():
    return {a: [{"eixo": e, "temas": [{"tema": c, "descricao": d} for c, d in ts]} for e, ts in eixos.items()]
            for a, eixos in EIXOS.items()}
