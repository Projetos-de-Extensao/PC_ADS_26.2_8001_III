"""Consolida os ITENS_PROVA_AAAA.csv do INEP em data/itens_inep_2016_2025.csv (4 cores principais por área).

Uso:  python scripts/consolidar_itens_inep.py PASTA_COM_ITENS_AAAA.csv [saida.csv]

Por (ano, área) mantém os 4 cadernos regulares da 1ª aplicação: os CO_PROVA consecutivos a partir do AZUL
(AZUL, AMARELA e mais duas cores, que variam por ano: ROSA/BRANCA/CINZA/VERDE). Ficam de fora cadernos
especiais (LARANJA, ROXA, LEITOR TELA, braile) e as reaplicações. Em 2024 o AZUL regular NÃO é o de menor
CO_PROVA (ver PROVA_AZUL). Itens abandonados/anulados (IN_ITEM_ABAN=1) são mantidos e sinalizados, porque a
prova impressa tem 45 questões por área; eles não entram na pontuação. LC mantém as duas versões do idioma
(TP_LINGUA 0=inglês, 1=espanhol).

Validações (a execução falha se alguma quebrar): 45 posições por caderno; o mesmo CO_ITEM tem gabarito,
habilidade e parâmetros idênticos em todas as cores; o conjunto de itens é o mesmo nas 4 cores.
Conferência externa: gabarito oficial do AZUL bate 100% em 2020–2025 (PDF); em 2016 as notas oficiais dos
participantes reproduzem o AZUL, AMARELA, ROSA e BRANCA/CINZA.
"""
import csv
import glob
import io
import os
import re
import sys
from collections import defaultdict

# (ano, área) -> CO_PROVA do caderno AZUL regular, quando não é o menor CO_PROVA do AZUL.
PROVA_AZUL = {(2024, "CH"): 1383, (2024, "CN"): 1419, (2024, "LC"): 1395, (2024, "MT"): 1407}
CORES_REGULARES = {"AZUL", "AMARELA", "ROSA", "BRANCA", "CINZA", "VERDE"}

COLS = ["ANO", "CO_PROVA", "TX_COR", "TP_LINGUA", "CO_POSICAO", "SG_AREA", "CO_ITEM", "TX_GABARITO",
        "CO_HABILIDADE", "IN_ITEM_ABAN", "NU_PARAM_A", "NU_PARAM_B", "NU_PARAM_C"]


def ler(caminho):
    raw = open(caminho, "rb").read()
    try:
        txt = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = raw.decode("latin-1")
    return list(csv.DictReader(io.StringIO(txt), delimiter=";"))


def cadernos_regulares(ano, area, linhas):
    cor = lambda r: r["TX_COR"].strip().upper()
    azul = PROVA_AZUL.get((ano, area)) or min(int(r["CO_PROVA"]) for r in linhas if cor(r) == "AZUL")
    escolhidos = {}
    for p in range(azul, azul + 4):
        rs = [r for r in linhas if int(r["CO_PROVA"]) == p]
        cores = {cor(r) for r in rs}
        assert len(cores) == 1 and cores <= CORES_REGULARES, f"{ano} {area} CO_PROVA {p}: cores {cores}"
        assert all(r["IN_ITEM_ADAPTADO"].strip() != "1" for r in rs), f"{ano} {area} {p}: item adaptado"
        escolhidos[p] = (cores.pop(), rs)
    assert len({c for c, _ in escolhidos.values()}) == 4, f"{ano} {area}: cores repetidas"
    return escolhidos


def validar(ano, area, escolhidos):
    ref = None
    por_item, canonica = {}, {}
    for p, (cor, rs) in escolhidos.items():
        assert len({(r["CO_POSICAO"], r["TP_LINGUA"].strip()) for r in rs}) == len(rs), f"{ano} {area} {cor}: posição repetida"
        # prova do aluno = itens comuns + os do idioma (EN e ES têm a mesma quantidade)
        comuns = len({r["CO_POSICAO"] for r in rs if not r["TP_LINGUA"].strip()})
        por_lingua = {lg: len({r["CO_POSICAO"] for r in rs if r["TP_LINGUA"].strip() == lg}) for lg in ("0", "1")}
        assert por_lingua["0"] == por_lingua["1"], f"{ano} {area} {cor}: idiomas com tamanhos diferentes {por_lingua}"
        n = comuns + por_lingua["0"]
        assert n == 45, f"{ano} {area} {cor}: {n} questões (esperado 45)"
        itens = {r["CO_ITEM"] for r in rs}
        ref = ref if ref is not None else itens
        assert itens == ref, f"{ano} {area} {cor}: conjunto de itens difere do AZUL"
        for r in rs:
            ass = (r["TX_GABARITO"], r["NU_PARAM_A"], r["NU_PARAM_B"], r["NU_PARAM_C"], r["IN_ITEM_ABAN"])
            assert por_item.setdefault(r["CO_ITEM"], ass) == ass, f"{ano} {area} item {r['CO_ITEM']} difere entre cores"
            # A habilidade às vezes diverge no arquivo do INEP (erro de cadastro): vale a do caderno AZUL.
            hab = canonica.setdefault(r["CO_ITEM"], r["CO_HABILIDADE"])
            if r["CO_HABILIDADE"] != hab:
                print(f"AVISO {ano} {area} {cor} item {r['CO_ITEM']}: habilidade {r['CO_HABILIDADE']} -> {hab} (a do AZUL)")
                r["CO_HABILIDADE"] = hab


def main(pasta, saida):
    out = []
    for caminho in sorted(glob.glob(os.path.join(pasta, "ITENS_*.csv"))):
        ano = int(re.search(r"(\d{4})", os.path.basename(caminho)).group(1))
        linhas = ler(caminho)
        for area in ("LC", "CH", "CN", "MT"):
            rs = [r for r in linhas if r["SG_AREA"].strip().upper() == area]
            escolhidos = cadernos_regulares(ano, area, rs)
            validar(ano, area, escolhidos)
            for p, (cor, crs) in escolhidos.items():
                for r in crs:
                    out.append({**r, "ANO": ano, "TX_COR": cor})
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter=";", extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} linhas -> {saida}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/itens_inep_2016_2025.csv")
