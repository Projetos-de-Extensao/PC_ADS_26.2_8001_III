"""Importa questões reais do ENEM (INEP) a partir do CSV consolidado (scripts/consolidar_itens_inep.py).

Uso:  python manage.py importar_inep data/itens_inep_2016_2025.csv            (todos os anos do arquivo)
      python manage.py importar_inep ITENS_PROVA_2023.csv --ano 2023           (CSV do INEP sem coluna ANO)

Colunas: CO_POSICAO, SG_AREA, TX_GABARITO (obrigatórias); ANO, TX_COR, CO_PROVA, CO_ITEM, CO_HABILIDADE,
NU_PARAM_A/B/C, TP_LINGUA, IN_ITEM_ABAN, IN_ITEM_ADAPTADO (opcionais).
Cada cor (TX_COR; padrão AZUL) vira um caderno, com numeração própria 1..45 por área. Se o CSV tiver vários
CO_PROVA para a mesma cor, usa o menor (por isso o consolidador já entrega só os 4 cadernos regulares).
Itens abandonados/anulados (IN_ITEM_ABAN=1) ficam na prova, marcados `anulada`: não pontuam.
LC: itens de TP_LINGUA 0/1 viram lingua EN/ES e compartilham o número (1–5); os comuns seguem de 6 a 45.
"""
import csv
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from enem.matriz import competencia_de
from enem.models import CORES, EdicaoEnem, Questao

AREAS = ("LC", "CH", "CN", "MT")
CORES_VALIDAS = {c for c, _ in CORES}
LINGUA_DE = {"0": "EN", "1": "ES"}  # TP_LINGUA do INEP
EIXOS_CSV = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "classificacao_eixos.csv")


def carregar_eixos(caminho=EIXOS_CSV):
    """(ano, CO_ITEM) -> eixo temático. O mesmo item tem o mesmo eixo em todas as cores. Arquivo opcional."""
    if not os.path.exists(caminho):
        return {}
    with open(caminho, newline="", encoding="utf-8") as f:
        return {(int(r["ano"]), r["co_item"]): r["eixo"] for r in csv.DictReader(f, delimiter=";") if r["eixo"]}


def numero(valor, padrao=None):
    try:
        return float(str(valor).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return padrao


def abrir(caminho):
    for enc in ("utf-8-sig", "latin-1"):
        try:
            with open(caminho, newline="", encoding=enc) as f:
                f.read(200000)
            return open(caminho, newline="", encoding=enc)
        except UnicodeDecodeError:
            continue
    raise CommandError("Não foi possível ler o arquivo (encoding).")


def converter_parametros(a, b, c):
    """Os parâmetros do INEP vêm na escala da nota (média 500, desvio 100); converte para theta."""
    if b is not None and abs(b) > 20:
        b = (b - 500) / 100
        a = (a or 0.01) * 100
    return (a if a else 1.0, b if b is not None else 0.0, c if c is not None else 0.2)


class Command(BaseCommand):
    help = "Importa gabarito, habilidade, parâmetros TRI e eixo dos itens do ENEM (4 cadernos por área)."

    def add_arguments(self, parser):
        parser.add_argument("csv")
        parser.add_argument("--ano", type=int, help="Obrigatório, exceto se o CSV tiver a coluna ANO (importa todos os anos)")

    @transaction.atomic
    def handle(self, *args, **o):
        self.eixos = carregar_eixos()
        with abrir(o["csv"]) as f:
            leitor = csv.DictReader(f, delimiter=";")
            faltando = {"CO_POSICAO", "SG_AREA", "TX_GABARITO"} - set(leitor.fieldnames or [])
            if faltando:
                raise CommandError(f"Colunas ausentes: {sorted(faltando)}. Cabeçalho: {leitor.fieldnames}")
            linhas = list(leitor)
        if not linhas:
            raise CommandError("CSV sem linhas.")

        if "ANO" in linhas[0] and not o["ano"]:
            anos = sorted({int(r["ANO"]) for r in linhas})
        elif o["ano"]:
            anos = [o["ano"]]
        else:
            raise CommandError("Informe --ano (o CSV não tem a coluna ANO).")
        for ano in anos:
            sub = [r for r in linhas if "ANO" not in r or int(r["ANO"]) == ano]
            self.importar_ano(sub, ano)

    def cadernos(self, linhas, area):
        """{cor: [linhas]} da área, ignorando cores especiais e itens adaptados."""
        rs = [r for r in linhas if r["SG_AREA"].strip().upper() == area and r.get("IN_ITEM_ADAPTADO", "0").strip() != "1"]
        por_cor = {}
        for r in rs:
            cor = (r.get("TX_COR") or "AZUL").strip().upper()
            if cor not in CORES_VALIDAS:
                continue
            por_cor.setdefault(cor, []).append(r)
        for cor, crs in por_cor.items():
            if "CO_PROVA" in crs[0]:
                prova = min(int(numero(r["CO_PROVA"])) for r in crs)
                por_cor[cor] = [r for r in crs if int(numero(r["CO_PROVA"])) == prova]
        return por_cor

    def importar_ano(self, linhas, ano):
        edicao, _ = EdicaoEnem.objects.get_or_create(ano=ano)
        total = 0
        for area in AREAS:
            cadernos = self.cadernos(linhas, area)
            if not cadernos:
                self.stdout.write(self.style.WARNING(f"{ano} {area}: nenhum item."))
                continue
            for cor, itens in sorted(cadernos.items()):
                total += self.importar_caderno(edicao, ano, area, cor, itens)
            self.stdout.write(f"{ano} {area}: {len(cadernos)} caderno(s) — " + ", ".join(sorted(cadernos)))
        self.stdout.write(self.style.SUCCESS(f"ENEM {ano}: {total} itens importados."))

    def importar_caderno(self, edicao, ano, area, cor, itens):
        for r in itens:
            r["_pos"] = int(numero(r["CO_POSICAO"]))
            r["_lingua"] = LINGUA_DE.get((r.get("TP_LINGUA") or "").strip(), "") if area == "LC" else ""
        # Numeração: itens específicos de idioma ocupam 1..k (por idioma); os comuns vêm depois, iguais para todos.
        especificos = [r for r in itens if r["_lingua"]]
        k = max([sum(1 for r in especificos if r["_lingua"] == lg) for lg in LINGUA_DE.values()] or [0])
        rank = {pos: n for n, pos in enumerate(sorted({r["_pos"] for r in itens if not r["_lingua"]}), start=k + 1)}
        for lg in LINGUA_DE.values():
            for n, pos in enumerate(sorted(r["_pos"] for r in especificos if r["_lingua"] == lg), start=1):
                rank[(lg, pos)] = n
        mantidas = set()
        for r in itens:
            pos, lingua = r["_pos"], r["_lingua"]
            n = rank[(lingua, pos)] if lingua else rank[pos]
            a, b, c = converter_parametros(numero(r.get("NU_PARAM_A")), numero(r.get("NU_PARAM_B")), numero(r.get("NU_PARAM_C")))
            hab = (r.get("CO_HABILIDADE") or "").strip()
            hab_txt = f"H{int(numero(hab))}" if hab else "N/D"
            eixo = self.eixos.get((ano, (r.get("CO_ITEM") or "").strip()))
            mantidas.add((n, lingua))
            existente = Questao.objects.filter(edicao=edicao, area=area, cor=cor, numero=n, lingua=lingua).first()
            if existente is not None and existente.respostas.exists() and existente.atributos.get("posicao") != pos:
                raise CommandError(
                    f"{ano} {area} {cor} Q{n}: já existem submissões nesta questão com outra numeração. "
                    "Recrie o banco (dados de teste) antes de reimportar.")
            Questao.objects.update_or_create(
                edicao=edicao, area=area, cor=cor, numero=n, lingua=lingua,
                defaults=dict(
                    gabarito=r["TX_GABARITO"].strip().upper()[:1],
                    anulada=r.get("IN_ITEM_ABAN", "0").strip() == "1",
                    atributos={"habilidade": hab_txt, "competencia": competencia_de(area, hab_txt),
                               "posicao": pos, "fonte": "INEP", **({"eixo": eixo} if eixo else {})},
                    param_a=round(a, 4), param_b=round(b, 4), param_c=round(c, 4),
                ),
            )
        # remove sobras (ex.: sintéticas ou de importação antiga) que não tenham respostas
        sobras = [q for q in Questao.objects.filter(edicao=edicao, area=area, cor=cor) if (q.numero, q.lingua) not in mantidas]
        presas = 0
        for q in sobras:
            if q.respostas.exists():
                presas += 1
            else:
                q.delete()
        if presas:
            self.stdout.write(self.style.WARNING(f"{ano} {area} {cor}: {presas} questão(ões) antigas mantidas por terem respostas."))
        return len(itens)
