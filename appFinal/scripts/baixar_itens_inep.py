"""Baixa só o ITENS_PROVA_AAAA.csv dos microdados do ENEM (INEP), sem baixar o zip inteiro.

Uso (na sua máquina, com internet):
    pip install requests remotezip
    python scripts/baixar_itens_inep.py                 # 2016..2025 -> ./dados_inep/
    python scripts/baixar_itens_inep.py 2019 2023       # anos específicos

Usa leitura parcial do zip remoto (HTTP Range). Se o servidor não aceitar, baixa o zip inteiro (centenas de MB).
Depois importe cada CSV com: python manage.py importar_inep dados_inep/ITENS_PROVA_AAAA.csv --ano AAAA
"""
import io
import os
import sys
import zipfile

import requests

URL = "https://download.inep.gov.br/microdados/microdados_enem_{ano}.zip"
SAIDA = "dados_inep"


def achar_itens(nomes):
    """Nome do CSV de itens dentro do zip (varia de pasta/caixa entre anos)."""
    cands = [n for n in nomes if "ITENS_PROVA" in n.upper() and n.lower().endswith(".csv")]
    return sorted(cands, key=len)[0] if cands else None


def extrair(zf, ano):
    nome = achar_itens(zf.namelist())
    if not nome:
        raise RuntimeError("ITENS_PROVA não encontrado no zip")
    destino = os.path.join(SAIDA, f"ITENS_PROVA_{ano}.csv")
    with zf.open(nome) as src, open(destino, "wb") as dst:
        dst.write(src.read())
    return destino


def baixar(ano):
    url = URL.format(ano=ano)
    try:
        from remotezip import RemoteZip
        with RemoteZip(url, verify=False) as zf:
            return extrair(zf, ano)
    except Exception as e:  # sem Range / sem remotezip: baixa o zip inteiro
        print(f"  (leitura parcial falhou: {e}); baixando zip completo...")
    r = requests.get(url, stream=True, timeout=120, verify=False)
    r.raise_for_status()
    buf = io.BytesIO()
    for chunk in r.iter_content(1 << 20):
        buf.write(chunk)
    with zipfile.ZipFile(buf) as zf:
        return extrair(zf, ano)


if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    os.makedirs(SAIDA, exist_ok=True)
    anos = [int(a) for a in sys.argv[1:]] or list(range(2016, 2026))
    falhas = []
    for ano in anos:
        print(f"ENEM {ano}...")
        try:
            print("  ok:", baixar(ano))
        except Exception as e:
            print("  FALHA:", e)
            falhas.append(ano)
    print("Concluído." + (f" Falharam: {falhas}" if falhas else ""))
