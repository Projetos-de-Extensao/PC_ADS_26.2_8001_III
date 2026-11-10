from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from .matriz import competencia_de
from .models import Questao, RespostaInformada, Resultado, Submissao
from .tri import estimar_nota


# Cada dia do ENEM tem um único caderno de 90 questões: as duas áreas do dia têm sempre a mesma cor.
# 2017 em diante: dia 1 = LC + CH, dia 2 = CN + MT. Em 2016 o INEP aplicou CH + CN e LC + MT (conferido nas paletas do CSV).
PARES_2016 = (("CH", "CN"), ("LC", "MT"))
PARES_PADRAO = (("LC", "CH"), ("CN", "MT"))


def area_parceira(ano, area):
    """Área que divide o caderno (mesma cor) com `area` na edição `ano`."""
    for par in (PARES_2016 if ano == 2016 else PARES_PADRAO):
        if area in par:
            return par[1] if par[0] == area else par[0]
    return None


def cor_do_dia(aluno, edicao, area):
    """(área parceira, cor da última submissão dela pelo aluno ou None)."""
    parceira = area_parceira(edicao.ano, area)
    ultima = (Submissao.objects.filter(aluno=aluno, edicao=edicao, area=parceira).order_by("-criada_em", "-pk").first()
              if parceira else None)
    return parceira, (ultima.cor if ultima else None)


@transaction.atomic
def registrar_submissao(aluno, edicao, area, respostas, lingua="", cor="AZUL"):
    """Grava Submissao + RespostaInformada(s) + Resultado de forma atômica.

    Itens anulados/abandonados pelo INEP fazem parte da prova (45 respostas), mas não entram em acertos,
    erros, nota TRI nem análise.
    Qualquer violação de regra (questão repetida/inexistente, prova incompleta)
    levanta ValidationError dentro do bloco atômico: o Django desfaz tudo (rollback).
    """
    lingua = (lingua or "EN") if area == "LC" else ""
    questoes = {q.numero: q for q in Questao.objects.filter(edicao=edicao, area=area, cor=cor, lingua__in=["", lingua])}
    if not questoes:
        raise ValidationError({"cor": f"Caderno {cor} não disponível em {edicao} / {area}."})
    parceira, cor_parceira = cor_do_dia(aluno, edicao, area)
    if cor_parceira and cor_parceira != cor:
        raise ValidationError({"cor": (
            f"Em {edicao.ano}, {area} e {parceira} são do mesmo caderno (mesmo dia de prova) e têm a mesma cor. "
            f"Você já enviou {parceira} com a cor {cor_parceira.lower()}. Se aquela cor estava errada, exclua o envio de {parceira} e reenvie.")})
    submissao = Submissao.objects.create(aluno=aluno, edicao=edicao, area=area, cor=cor, lingua=lingua)

    objetos, vistos = [], set()
    for item in respostas:
        numero = item["numero"]
        if numero in vistos:
            raise ValidationError({"respostas": f"Questão {numero} informada mais de uma vez."})
        vistos.add(numero)
        questao = questoes.get(numero)
        if questao is None:
            raise ValidationError({"respostas": f"Questão {numero} não existe em {edicao} / {area}."})
        alternativa = item.get("alternativa", "") or ""
        objetos.append(RespostaInformada(
            submissao=submissao, questao=questao, alternativa=alternativa,
            correta=bool(alternativa) and alternativa == questao.gabarito,
        ))
    RespostaInformada.objects.bulk_create(objetos)

    if not questoes or len(objetos) != len(questoes):
        raise ValidationError({"respostas": f"A prova deve ter {len(questoes)} respostas (recebidas: {len(objetos)})."})

    validas = [o for o in objetos if not o.questao.anulada]
    acertos = sum(o.correta for o in validas)
    brancos = sum(1 for o in validas if not o.alternativa)
    nota = estimar_nota((o.questao.param_a, o.questao.param_b, o.questao.param_c, o.correta) for o in validas)

    habilidades = defaultdict(lambda: {"total": 0, "erros": 0})
    competencias = defaultdict(lambda: {"total": 0, "erros": 0})
    eixos = defaultdict(lambda: {"total": 0, "erros": 0})
    for o in validas:
        hab = o.questao.atributos.get("habilidade", "N/D")
        comp = o.questao.atributos.get("competencia") or competencia_de(o.questao.area, hab)
        for grupo, chave in ((habilidades, hab), (competencias, comp)):
            grupo[chave]["total"] += 1
            grupo[chave]["erros"] += 0 if o.correta else 1
        eixo = o.questao.atributos.get("eixo")
        if eixo:
            eixos[eixo]["total"] += 1
            eixos[eixo]["erros"] += 0 if o.correta else 1
    analise = {"habilidades": dict(habilidades), "competencias": dict(competencias), "eixos": dict(eixos)}

    Resultado.objects.create(
        submissao=submissao, acertos=acertos, erros=len(validas) - acertos - brancos,
        brancos=brancos, nota_tri=Decimal(str(nota)), analise=analise,
    )
    return submissao
