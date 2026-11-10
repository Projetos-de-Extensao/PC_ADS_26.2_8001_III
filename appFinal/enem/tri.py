"""Estimativa de nota TRI, seguindo o método descrito pelo INEP (documento "Procedimentos de Análise", Enem).

- Modelo logístico de 3 parâmetros (Birnbaum): P(θ) = c + (1 - c) / (1 + exp(-D·a·(θ - b))), com D = 1.
- Proficiência por EAP (Expected a Posteriori) com priori normal N(0,1), integrada numericamente
  (o INEP usa 40 pontos de quadratura; aqui, grade de 81 pontos em θ de -4 a 4).
- Escala (500,100): nota = 500 + 100·θ.

Os parâmetros a, b, c vêm dos microdados (escala θ). Validado contra as notas oficiais de participantes de 2016:
erro absoluto médio ≈ 8 (CN), 10 (CH) e 22 (MT) pontos. Não reproduz o cálculo oficial exato (o INEP usa o
conjunto completo de itens e regras de coerência não publicadas): é uma estimativa.
"""
import math

ESCALA_MEDIA = 500.0
ESCALA_DESVIO = 100.0
D = 1.0
_GRADE = [i / 10 for i in range(-40, 41)]
_PESOS_PRIORI = [math.exp(-0.5 * t * t) for t in _GRADE]


def prob_acerto(theta, a, b, c):
    return c + (1 - c) / (1 + math.exp(-D * a * (theta - b)))


def estimar_nota(itens):
    """itens: iterável de (a, b, c, acertou). Retorna a nota estimada (float), por EAP."""
    itens = list(itens)
    if not itens:
        return ESCALA_MEDIA
    logs = []
    for theta in _GRADE:
        ll = 0.0
        for a, b, c, acertou in itens:
            p = min(max(prob_acerto(theta, a, b, c), 1e-12), 1 - 1e-12)
            ll += math.log(p) if acertou else math.log(1 - p)
        logs.append(ll)
    m = max(logs)
    pesos = [w * math.exp(ll - m) for w, ll in zip(_PESOS_PRIORI, logs)]
    theta_eap = sum(w * t for w, t in zip(pesos, _GRADE)) / sum(pesos)
    return round(ESCALA_MEDIA + ESCALA_DESVIO * theta_eap, 1)
