"""Matriz de Referência do ENEM (INEP): competência de área de cada habilidade (H1–H30).

Fonte: Matriz de Referência do ENEM (competências de área e faixas de habilidades).
Camada 1 do "eixo temático": determinística a partir da habilidade que o INEP já informa por item.
"""

# área -> [(número da competência, título curto, primeira habilidade, última habilidade)]
COMPETENCIAS = {
    "LC": [
        (1, "Tecnologias da comunicação e da informação", 1, 4),
        (2, "Língua estrangeira moderna", 5, 8),
        (3, "Linguagem corporal", 9, 11),
        (4, "Arte como saber cultural e estético", 12, 14),
        (5, "Recursos expressivos e contextos dos textos", 15, 17),
        (6, "Sistemas simbólicos das linguagens", 18, 20),
        (7, "Confronto de opiniões entre linguagens", 21, 24),
        (8, "Língua portuguesa", 25, 27),
        (9, "Natureza e impacto das tecnologias da informação", 28, 30),
    ],
    "MT": [
        (1, "Números e seus significados", 1, 5),
        (2, "Geometria", 6, 9),
        (3, "Grandezas e medidas", 10, 14),
        (4, "Variação de grandezas", 15, 18),
        (5, "Álgebra e modelagem de problemas", 19, 23),
        (6, "Gráficos e tabelas", 24, 26),
        (7, "Estatística e probabilidade", 27, 30),
    ],
    "CN": [
        (1, "Ciência e tecnologia como construção humana", 1, 4),
        (2, "Tecnologias em diferentes contextos", 5, 7),
        (3, "Ambiente, produção e intervenções", 8, 12),
        (4, "Organismos, ambiente e saúde", 13, 16),
        (5, "Métodos e procedimentos científicos", 17, 19),
        (6, "Física", 20, 23),
        (7, "Química", 24, 27),
        (8, "Biologia", 28, 30),
    ],
    "CH": [
        (1, "Identidades e elementos culturais", 1, 5),
        (2, "Espaço geográfico e relações de poder", 6, 10),
        (3, "Instituições sociais, políticas e econômicas", 11, 15),
        (4, "Transformações técnicas e tecnológicas", 16, 20),
        (5, "Cidadania e democracia", 21, 25),
        (6, "Sociedade e natureza", 26, 30),
    ],
}


def competencia_de(area, habilidade):
    """'MT','H12' -> 'C3'. Retorna 'N/D' se a habilidade for desconhecida."""
    try:
        n = int(str(habilidade).lstrip("Hh"))
    except (TypeError, ValueError):
        return "N/D"
    for num, _titulo, ini, fim in COMPETENCIAS.get(area, []):
        if ini <= n <= fim:
            return f"C{num}"
    return "N/D"


def titulo_competencia(area, competencia):
    for num, titulo, _i, _f in COMPETENCIAS.get(area, []):
        if f"C{num}" == competencia:
            return titulo
    return competencia


def matriz_publica():
    return {a: [{"competencia": f"C{n}", "titulo": t, "habilidades": [f"H{i}" for i in range(ini, fim + 1)]}
                for n, t, ini, fim in comps] for a, comps in COMPETENCIAS.items()}
