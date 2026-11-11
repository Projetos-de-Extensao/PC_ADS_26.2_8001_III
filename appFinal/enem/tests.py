import os

from django.core.management import call_command
from django.db import connection
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from .models import Aluno, EdicaoEnem, Questao, RespostaInformada, Resultado, Submissao
from .tri import estimar_nota


def criar_aluno(email="a@x.com"):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username=email, email=email, password="senha-forte-123")
    return Aluno.objects.create(user=user, nome=email.split("@")[0], email=email)


def prova_completa(area="MT", ano=2023, erradas=(), lingua="EN"):
    """Respostas corretas para as 45 questões, exceto as listadas em `erradas`."""
    out = []
    for q in Questao.objects.filter(edicao__ano=ano, area=area, lingua__in=["", lingua]):
        alt = q.gabarito if q.numero not in erradas else ("A" if q.gabarito != "A" else "B")
        out.append({"numero": q.numero, "alternativa": alt})
    return out


class BaseApollo(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_enem", verbosity=0)
        cls.aluno = criar_aluno("aluno1@x.com")
        cls.outro = criar_aluno("aluno2@x.com")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.aluno.user)


class TriTests(TestCase):
    def test_mais_acertos_gera_nota_maior(self):
        itens = [(1.2, b / 10, 0.2) for b in range(-10, 20)]
        baixa = estimar_nota([(a, b, c, i < 10) for i, (a, b, c) in enumerate(itens)])
        alta = estimar_nota([(a, b, c, i < 25) for i, (a, b, c) in enumerate(itens)])
        self.assertGreater(alta, baixa)


class SubmissaoTests(BaseApollo):
    def test_envio_valido_grava_tres_tabelas(self):
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": prova_completa(erradas={1, 2, 3})}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["resultado"]["acertos"], 42)
        self.assertEqual(Submissao.objects.count(), 1)
        self.assertEqual(RespostaInformada.objects.count(), 45)
        self.assertEqual(Resultado.objects.count(), 1)

    def test_prova_incompleta_faz_rollback_total(self):
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": prova_completa()[:30]}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual((Submissao.objects.count(), RespostaInformada.objects.count(), Resultado.objects.count()), (0, 0, 0))

    def test_questao_inexistente_faz_rollback(self):
        respostas = prova_completa()
        respostas[0]["numero"] = 77
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": respostas}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Submissao.objects.count(), 0)

    def test_aluno_nao_ve_submissao_de_outro(self):
        self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": prova_completa()}, format="json")
        outro = APIClient()
        outro.force_authenticate(self.outro.user)
        self.assertEqual(outro.get("/api/submissoes/").data["count"], 0)

    def test_dashboard_lista_habilidades_com_erro(self):
        self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": prova_completa(erradas={1, 2, 3, 4, 5})}, format="json")
        d = self.client.get("/api/dashboard/").data
        self.assertEqual(d["por_area"][0]["area"], "MT")
        self.assertGreaterEqual(len(d["habilidades_prioritarias"]), 1)


class QuestaoTests(BaseApollo):
    def test_filtro_por_atributo_jsonb(self):
        q = Questao.objects.filter(edicao__ano=2023, area="MT").first()
        hab = q.atributos["habilidade"]
        r = self.client.get(f"/api/questoes/?atributos__habilidade={hab}")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data["count"], 1)
        self.assertTrue(all(i["atributos"]["habilidade"] == hab for i in r.data["results"]))

    def test_gabarito_nao_vaza_para_aluno(self):
        r = self.client.get("/api/questoes/?ano=2023&area=MT")
        self.assertNotIn("gabarito", r.data["results"][0])

    def test_indice_gin_existe_no_banco(self):
        with connection.cursor() as cur:
            cur.execute("SELECT indexdef FROM pg_indexes WHERE indexname = 'questao_atributos_gin'")
            self.assertIn("gin", cur.fetchone()[0].lower())


class CadastroEHealthTests(TestCase):
    def test_cadastro_login_e_health(self):
        c = APIClient()
        r = c.post("/api/cadastro/", {"nome": "Ana", "email": "ana@x.com", "senha": "senha-forte-123"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(c.post("/api/login/", {"email": "ana@x.com", "senha": "senha-forte-123"}, format="json").status_code, 200)
        self.assertEqual(c.get("/health/").status_code, 200)

    def test_endpoints_exigem_login(self):
        self.assertEqual(APIClient().get("/api/submissoes/").status_code, 403)


class ImportarInepTests(TestCase):
    def test_importa_csv_no_formato_do_inep(self):
        import tempfile, os
        linhas = ["CO_POSICAO;SG_AREA;CO_ITEM;TX_GABARITO;CO_HABILIDADE;IN_ITEM_ADAPTADO;NU_PARAM_A;NU_PARAM_B;NU_PARAM_C;TX_COR;TP_LINGUA;IN_ITEM_ABAN"]
        for i in range(1, 4):
            linhas.append(f"{i};MT;{100+i};B;{i+4};0;0,05;{650+i*10},5;0,18;AZUL;;0")
        linhas.append("4;MT;200;C;9;0;0,05;700,0;0,18;AMARELA;;0")   # outra cor: caderno próprio
        linhas.append("5;MT;201;D;9;0;0,05;700,0;0,18;AZUL;;1")      # abandonado: fica na prova, marcado
        linhas.append("6;MT;202;D;9;0;0,05;700,0;0,18;LARANJA;;0")   # caderno especial: ignorado
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="latin-1") as f:
            f.write("\n".join(linhas)); caminho = f.name
        call_command("importar_inep", caminho, "--ano", "2016", verbosity=0)
        os.unlink(caminho)
        qs = Questao.objects.filter(edicao__ano=2016, area="MT", cor="AZUL").order_by("numero")
        self.assertEqual(qs.count(), 4)
        self.assertEqual([q.anulada for q in qs], [False, False, False, True])
        self.assertEqual(Questao.objects.filter(edicao__ano=2016, area="MT", cor="AMARELA").count(), 1)
        self.assertFalse(Questao.objects.filter(edicao__ano=2016, area="MT", cor="LARANJA").exists())
        q = qs.first()
        self.assertEqual((q.gabarito, q.atributos["habilidade"]), ("B", "H5"))
        self.assertAlmostEqual(q.param_b, 1.605, places=2)   # (660,5-500)/100
        self.assertAlmostEqual(q.param_a, 5.0, places=2)     # 0,05 * 100

    def test_csv_consolidado_com_coluna_ano(self):
        import tempfile, os
        linhas = ["ANO;CO_POSICAO;SG_AREA;TX_GABARITO;CO_HABILIDADE;NU_PARAM_A;NU_PARAM_B;NU_PARAM_C"]
        for ano in (2016, 2017):
            for i in range(1, 4):
                linhas.append(f"{ano};{i};CN;{'ABC'[i-1]};{i};1.5;0.5;0.2")
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("\n".join(linhas)); caminho = f.name
        call_command("importar_inep", caminho, verbosity=0)
        os.unlink(caminho)
        for ano in (2016, 2017):
            self.assertEqual(Questao.objects.filter(edicao__ano=ano, area="CN").count(), 3)
        self.assertEqual(Questao.objects.get(edicao__ano=2017, area="CN", numero=2).gabarito, "B")
        self.assertEqual(Questao.objects.get(edicao__ano=2017, area="CN", numero=2).param_b, 0.5)


class MatrizTests(BaseApollo):
    def test_matriz_cobre_h1_a_h30_sem_lacuna_nem_sobreposicao(self):
        from .matriz import COMPETENCIAS, competencia_de
        for area, comps in COMPETENCIAS.items():
            cobertas = [h for _n, _t, ini, fim in comps for h in range(ini, fim + 1)]
            self.assertEqual(sorted(cobertas), list(range(1, 31)), area)
            self.assertTrue(all(competencia_de(area, f"H{h}") != "N/D" for h in range(1, 31)))

    def test_fronteiras_conhecidas(self):
        from .matriz import competencia_de
        self.assertEqual(competencia_de("CN", "H12"), "C3")   # C3 = H8–H12
        self.assertEqual(competencia_de("CN", "H13"), "C4")
        self.assertEqual(competencia_de("MT", "H30"), "C7")
        self.assertEqual(competencia_de("LC", "H25"), "C8")
        self.assertEqual(competencia_de("CH", "H1"), "C1")
        self.assertEqual(competencia_de("MT", "N/D"), "N/D")
        self.assertEqual(competencia_de("XX", "H1"), "N/D")

    def test_questoes_tem_competencia_coerente_com_habilidade(self):
        from .matriz import competencia_de
        for q in Questao.objects.filter(edicao__ano=2023)[:200]:
            self.assertEqual(q.atributos["competencia"], competencia_de(q.area, q.atributos["habilidade"]))

    def test_analise_e_dashboard_por_competencia(self):
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT",
                             "respostas": prova_completa(erradas={1, 2, 3, 4, 5})}, format="json")
        self.assertEqual(r.status_code, 201)
        an = r.data["resultado"]["analise"]
        self.assertEqual(set(an), {"habilidades", "competencias", "eixos"})
        self.assertEqual(sum(v["total"] for v in an["competencias"].values()), len(prova_completa()))
        self.assertEqual(sum(v["erros"] for v in an["competencias"].values()), 5)
        d = self.client.get("/api/dashboard/").data
        self.assertGreaterEqual(len(d["competencias_prioritarias"]), 1)
        self.assertEqual(sum(c["erros"] for c in d["competencias_prioritarias"]), 5)
        self.assertTrue(all(c["titulo"] and c["area"] == "MT" for c in d["competencias_prioritarias"]))

    def test_endpoint_matriz(self):
        d = self.client.get("/api/matriz/").data
        self.assertEqual(set(d), {"LC", "CH", "CN", "MT"})
        self.assertEqual(len(d["CN"]), 8)
        self.assertEqual(APIClient().get("/api/matriz/").status_code in (401, 403), True)

    def test_importador_grava_competencia(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("ANO;CO_POSICAO;SG_AREA;TX_GABARITO;CO_HABILIDADE;NU_PARAM_A;NU_PARAM_B;NU_PARAM_C\n2016;1;MT;A;12;1.5;0.5;0.2\n"); caminho = f.name
        call_command("importar_inep", caminho, verbosity=0); os.unlink(caminho)
        self.assertEqual(Questao.objects.get(edicao__ano=2016, area="MT", numero=1).atributos["competencia"], "C3")


class LinguaTests(BaseApollo):
    """Linguagens: questões 1–5 em inglês e espanhol; o aluno escolhe um idioma."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        e = EdicaoEnem.objects.get(ano=2023)
        Questao.objects.filter(edicao=e, area="LC", numero__lte=5).delete()
        for n in range(1, 6):
            for lg, gab in (("EN", "A"), ("ES", "B")):
                Questao.objects.create(edicao=e, area="LC", numero=n, lingua=lg, gabarito=gab)

    def _prova(self, lingua, erradas=()):
        return prova_completa("LC", 2023, erradas=erradas, lingua=lingua)

    def test_cada_idioma_tem_45_questoes_e_gabarito_proprio(self):
        for lg, gab in (("EN", "A"), ("ES", "B")):
            p = self._prova(lg)
            self.assertEqual(len(p), 45)
            r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "LC", "lingua": lg, "respostas": p}, format="json")
            self.assertEqual(r.status_code, 201, r.data)
            self.assertEqual(r.data["lingua"], lg)
            self.assertEqual(r.data["resultado"]["acertos"], 45)
            self.assertEqual([x["alternativa"] for x in r.data["respostas"] if x["numero"] == 1], [gab])

    def test_gabarito_do_outro_idioma_conta_como_erro(self):
        p = self._prova("EN")                      # gabarito inglês nas questões 1–5 (A)
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "LC", "lingua": "ES", "respostas": p}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["resultado"]["erros"], 5)   # 1–5: A ≠ B

    def test_idioma_padrao_e_ingles_e_invalido_da_400(self):
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "LC", "respostas": self._prova("EN")}, format="json")
        self.assertEqual(r.data["lingua"], "EN")
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "LC", "lingua": "FR", "respostas": self._prova("EN")}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_lingua_ignorada_fora_de_linguagens(self):
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "lingua": "ES", "respostas": prova_completa()}, format="json")
        self.assertEqual((r.status_code, r.data["lingua"]), (201, ""))

    def test_api_questoes_filtra_idioma(self):
        r = self.client.get("/api/questoes/?ano=2023&area=LC&lingua=ES&page_size=100")
        self.assertEqual(r.data["count"], 45)
        self.assertEqual(self.client.get("/api/questoes/?lingua=XX").status_code, 400)
        self.assertEqual(self.client.get("/api/edicoes/").data["results"][-1]["total_questoes"], 45 * 4)

    def test_importador_cria_en_e_es_com_mesmo_numero(self):
        import tempfile, os
        linhas = ["ANO;TX_COR;CO_PROVA;TP_LINGUA;CO_POSICAO;SG_AREA;TX_GABARITO;CO_HABILIDADE;NU_PARAM_A;NU_PARAM_B;NU_PARAM_C"]
        linhas += [f"2016;AZUL;1;0;{i};LC;A;5;1.5;0.5;0.2" for i in (1, 2)]
        linhas += [f"2016;AZUL;1;1;{i};LC;B;5;1.5;0.5;0.2" for i in (1, 2)]
        linhas += ["2016;AZUL;1;;3;LC;C;7;1.5;0.5;0.2"]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("\n".join(linhas)); caminho = f.name
        call_command("importar_inep", caminho, verbosity=0); os.unlink(caminho)
        qs = Questao.objects.filter(edicao__ano=2016, area="LC")
        self.assertEqual(sorted((q.numero, q.lingua, q.gabarito) for q in qs),
                         [(1, "EN", "A"), (1, "ES", "B"), (2, "EN", "A"), (2, "ES", "B"), (3, "", "C")])
        self.assertEqual(qs.get(numero=3).atributos["posicao"], 3)


class EixoTests(BaseApollo):
    def test_analise_e_dashboard_por_eixo(self):
        for q in Questao.objects.filter(edicao__ano=2023, area="MT"):
            q.atributos = {**q.atributos, "eixo": "Conhecimentos geométricos" if q.numero <= 20 else "Conhecimentos algébricos"}
            q.save()
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": prova_completa(erradas=(1, 2, 30))}, format="json")
        eixos = r.data["resultado"]["analise"]["eixos"]
        self.assertEqual(eixos["Conhecimentos geométricos"], {"total": 20, "erros": 2})
        self.assertEqual(eixos["Conhecimentos algébricos"], {"total": 25, "erros": 1})
        d = self.client.get("/api/dashboard/").data["eixos_prioritarios"]
        self.assertEqual((d[0]["eixo"], d[0]["erros"], d[0]["total"]), ("Conhecimentos geométricos", 2, 20))

    def test_sem_eixo_nao_quebra(self):
        r = self.client.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": prova_completa(erradas=(1,))}, format="json")
        self.assertEqual(r.data["resultado"]["analise"]["eixos"], {})
        self.assertEqual(self.client.get("/api/dashboard/").data["eixos_prioritarios"], [])

    def test_arquivo_de_classificacao_cobre_todos_os_itens_do_inep(self):
        import csv
        from enem.eixos import EIXOS
        from enem.management.commands.importar_inep import EIXOS_CSV, carregar_eixos
        eixos = carregar_eixos(EIXOS_CSV)
        validos = {e for area in EIXOS.values() for e in area}
        base = os.path.join(os.path.dirname(EIXOS_CSV), "itens_inep_2016_2025.csv")
        with open(base, newline="", encoding="utf-8") as f:
            chaves = {(int(r["ANO"]), r["CO_ITEM"]) for r in csv.DictReader(f, delimiter=";") if r["IN_ITEM_ABAN"] != "1"}
        self.assertEqual(chaves - set(eixos), set())  # todo item que pontua tem eixo (as 4 cores compartilham o item)
        self.assertTrue(set(eixos.values()) <= validos | {"Língua estrangeira"})

    def test_importador_grava_eixo_no_atributo(self):
        self.assertFalse(Questao.objects.filter(edicao__ano=2023, area="CN").exclude(atributos__eixo__isnull=True).exists())
        call_command("importar_inep", os.path.join(os.path.dirname(__import__("enem.management.commands.importar_inep", fromlist=["x"]).EIXOS_CSV), "itens_inep_2016_2025.csv"), "--ano", "2023", verbosity=0)
        q = Questao.objects.filter(edicao__ano=2023, area="CN", cor="AZUL")
        self.assertEqual(q.count(), 45)
        self.assertEqual(q.filter(atributos__eixo__in=["Física", "Química", "Biologia"]).count(), 45 - q.filter(anulada=True).count())


class TriMetodoTests(SimpleTestCase):
    def test_eap_monotono_e_estavel_nos_extremos(self):
        itens = [(2.0, (i - 22) / 10, 0.2) for i in range(45)]
        notas = [estimar_nota((a, b, c, i < k) for i, (a, b, c) in enumerate(itens)) for k in (0, 10, 22, 35, 45)]
        self.assertEqual(notas, sorted(notas))
        self.assertGreater(notas[0], 0)
        self.assertLess(notas[-1], 1000)

    def test_prior_puxa_para_500_sem_itens(self):
        self.assertEqual(estimar_nota([]), 500.0)


ARQUIVO_ITENS = os.path.join(os.path.dirname(__file__), "..", "data", "itens_inep_2016_2025.csv")


class CadernosTests(TestCase):
    """4 cadernos (cores) por área, 45 questões cada; itens anulados ficam na prova mas não pontuam."""

    @classmethod
    def setUpTestData(cls):
        call_command("importar_inep", ARQUIVO_ITENS, "--ano", "2016", verbosity=0)
        cls.aluno = criar_aluno("cores@x.com")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.aluno.user)

    def _prova(self, area, cor, lingua="EN", acertar=True, ano=2016):
        out = []
        for q in Questao.objects.filter(edicao__ano=ano, area=area, cor=cor, lingua__in=["", lingua]):
            alt = q.gabarito if acertar else ("A" if q.gabarito != "A" else "B")
            out.append({"numero": q.numero, "alternativa": alt})
        return out

    def test_base_tem_4_cadernos_de_45_questoes_por_area(self):
        for area in ("LC", "CH", "CN", "MT"):
            cores = set(Questao.objects.filter(edicao__ano=2016, area=area).values_list("cor", flat=True))
            self.assertEqual(len(cores), 4, area)
            for cor in cores:
                qs = Questao.objects.filter(edicao__ano=2016, area=area, cor=cor)
                self.assertEqual(sorted(qs.filter(lingua__in=["", "EN"]).values_list("numero", flat=True)), list(range(1, 46)), (area, cor))
                if area == "LC":
                    self.assertEqual(qs.filter(lingua="ES").count(), 5)

    def test_arquivo_consolidado_tem_4_cores_e_45_questoes_em_todos_os_anos(self):
        import csv
        from collections import defaultdict
        por = defaultdict(set)
        with open(ARQUIVO_ITENS, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter=";"):
                if r["TP_LINGUA"] != "1":   # conta a prova em inglês (as 5 de espanhol ocupam as mesmas posições lógicas)
                    por[(r["ANO"], r["SG_AREA"], r["TX_COR"])].add(r["CO_POSICAO"])
        areas = {(a, ar) for a, ar, _ in por}
        self.assertEqual(len(areas), 40)
        for (ano, area) in areas:
            self.assertEqual(len([k for k in por if k[:2] == (ano, area)]), 4, (ano, area))
        self.assertTrue(all(len(v) == 45 for v in por.values()))

    def test_cada_cor_usa_o_gabarito_do_proprio_caderno(self):
        amar = self.client.post("/api/submissoes/", {"ano": 2016, "area": "MT", "cor": "AMARELA", "respostas": self._prova("MT", "AMARELA")}, format="json")
        self.assertEqual(amar.status_code, 201, amar.data)
        self.assertEqual((amar.data["cor"], amar.data["resultado"]["acertos"]), ("AMARELA", 45 - Questao.objects.filter(edicao__ano=2016, area="MT", cor="AMARELA", anulada=True).count()))
        # o gabarito da amarela aplicado ao caderno azul erra muita coisa (ordem diferente)
        cruzada = self.client.post("/api/submissoes/", {"ano": 2016, "area": "MT", "cor": "AZUL", "respostas": self._prova("MT", "AMARELA")}, format="json")
        self.assertLess(cruzada.data["resultado"]["acertos"], 25)

    def test_cor_indisponivel_ou_invalida_da_400_e_nao_grava(self):
        r = self.client.post("/api/submissoes/", {"ano": 2016, "area": "MT", "cor": "VERDE", "respostas": self._prova("MT", "AZUL")}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/submissoes/", {"ano": 2016, "area": "MT", "cor": "LARANJA", "respostas": self._prova("MT", "AZUL")}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Submissao.objects.count(), 0)

    def test_cor_padrao_e_azul(self):
        r = self.client.post("/api/submissoes/", {"ano": 2016, "area": "CH", "respostas": self._prova("CH", "AZUL")}, format="json")
        self.assertEqual((r.status_code, r.data["cor"]), (201, "AZUL"))

    def test_item_anulado_exige_resposta_mas_nao_pontua(self):
        q = Questao.objects.get(edicao__ano=2016, area="CH", cor="AZUL", numero=7)
        q.anulada = True; q.save()
        completa = self._prova("CH", "AZUL")
        faltando = [x for x in completa if x["numero"] != 7]
        self.assertEqual(self.client.post("/api/submissoes/", {"ano": 2016, "area": "CH", "respostas": faltando}, format="json").status_code, 400)
        errada = [dict(x, alternativa=("A" if q.gabarito != "A" else "B")) if x["numero"] == 7 else x for x in completa]
        r = self.client.post("/api/submissoes/", {"ano": 2016, "area": "CH", "respostas": errada}, format="json")
        res = r.data["resultado"]
        anul = Questao.objects.filter(edicao__ano=2016, area="CH", cor="AZUL", anulada=True).count()
        self.assertEqual((res["acertos"], res["erros"], res["brancos"]), (45 - anul, 0, 0))
        self.assertEqual(sum(v["total"] for v in res["analise"]["habilidades"].values()), 45 - anul)
        self.assertEqual(self.client.get("/api/dashboard/").data["habilidades_prioritarias"], [])  # nenhum erro conta

    def test_api_lista_cores_por_area_e_filtra_por_cor(self):
        ed = [e for e in self.client.get("/api/edicoes/").data["results"] if e["ano"] == 2016][0]
        self.assertEqual(ed["cores"]["MT"][0], "AZUL")
        self.assertEqual(len(ed["cores"]["LC"]), 4)
        r = self.client.get("/api/questoes/?ano=2016&area=MT&cor=AMARELA&page_size=100")
        self.assertEqual(r.data["count"], 45)
        self.assertTrue(all(i["cor"] == "AMARELA" for i in r.data["results"]))
        self.assertEqual(self.client.get("/api/questoes/?cor=ROXA").status_code, 400)

    def test_reimportar_nao_muda_questoes_com_submissao_de_outra_numeracao(self):
        r = self.client.post("/api/submissoes/", {"ano": 2016, "area": "MT", "respostas": self._prova("MT", "AZUL")}, format="json")
        self.assertEqual(r.status_code, 201)
        q = Questao.objects.get(edicao__ano=2016, area="MT", cor="AZUL", numero=3)
        q.atributos = {**q.atributos, "posicao": 999}; q.save()   # simula numeração antiga
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("importar_inep", ARQUIVO_ITENS, "--ano", "2016", verbosity=0)


class DashboardFiltroTests(TestCase):
    _prova = CadernosTests._prova

    @classmethod
    def setUpTestData(cls):
        call_command("importar_inep", ARQUIVO_ITENS, "--ano", "2016", verbosity=0)
        cls.aluno = criar_aluno("dash@x.com")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.aluno.user)

    def test_filtro_por_area_e_historico_detalhado(self):
        self.client.post("/api/submissoes/", {"ano": 2016, "area": "MT", "cor": "ROSA", "respostas": self._prova("MT", "ROSA", acertar=False)}, format="json")
        self.client.post("/api/submissoes/", {"ano": 2016, "area": "CH", "respostas": self._prova("CH", "AZUL", acertar=False)}, format="json")
        tudo = self.client.get("/api/dashboard/").data
        so_mt = self.client.get("/api/dashboard/?area=MT").data
        self.assertEqual({h["area"] for h in tudo["historico"]}, {"MT", "CH"})
        self.assertEqual({h["area"] for h in so_mt["historico"]}, {"MT"})
        self.assertEqual({e["area"] for e in so_mt["eixos_prioritarios"]}, {"MT"})
        self.assertEqual([a["area"] for a in so_mt["por_area"]], ["MT"])
        h = so_mt["historico"][0]
        self.assertEqual((h["cor"], h["lingua"], h["acertos"] + h["erros"] + h["brancos"]), ("ROSA", "", 45 - Questao.objects.filter(edicao__ano=2016, area="MT", cor="ROSA", anulada=True).count()))
        self.assertIn("criada_em", h)
        self.assertEqual(self.client.get("/api/dashboard/?area=XX").status_code, 400)

    def test_detalhe_da_submissao_traz_mapa_da_prova(self):
        r = self.client.post("/api/submissoes/", {"ano": 2016, "area": "CH", "respostas": self._prova("CH", "AZUL")}, format="json")
        d = self.client.get(f"/api/submissoes/{r.data['id']}/").data
        self.assertEqual(len(d["respostas"]), 45)
        self.assertEqual(set(d["respostas"][0]), {"numero", "alternativa", "correta", "anulada", "habilidade"})
        self.assertEqual(set(d["resultado"]["analise"]), {"habilidades", "competencias", "eixos"})


class PaginasTests(TestCase):
    """As 3 páginas HTML (landing, enviar, dashboard) são servidas e ligam o cookie CSRF."""

    def test_paginas_respondem(self):
        for url, marca in [("/", 'data-page="inicio"'), ("/enviar/", 'data-page="enviar"'),
                           ("/dashboard/", 'data-page="dashboard"'),
                           ("/login/", 'data-page="login"'), ("/home/", 'data-page="home"')]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertIn(marca, r.content.decode())
            self.assertIn("csrftoken", r.cookies, url)

    def test_paginas_usam_rotas_reais(self):
        corpo = self.client.get("/enviar/").content.decode()
        for rota in ('href="/dashboard/"', 'href="/enviar/"'):
            self.assertIn(rota, corpo)

    def test_dashboard_tem_novas_secoes_e_sem_pareto(self):
        corpo = self.client.get("/dashboard/").content.decode()
        for marca in ("Resumo de provas", "Suas provas por edição", "Acertos e erros da prova inteira", "Erros por eixo temático", "Falta área"):
            self.assertIn(marca, corpo)
        for fora in ("Pareto", "pareto", "medias-nacionais", "média nacional"):
            self.assertNotIn(fora, corpo)

    def test_home_tem_resumo_de_provas(self):
        self.assertIn("Resumo de provas", self.client.get("/home/").content.decode())

    def test_logo_estatica_existe(self):
        from django.contrib.staticfiles import finders
        self.assertTrue(finders.find("enem/logo-claro.png"))
        self.assertTrue(finders.find("enem/logo-escuro.png"))
        self.assertTrue(finders.find("enem/favicon.png"))

    def test_logo_servida_pelo_servidor(self):
        r = self.client.get("/static/enem/logo-escuro.png")
        self.assertEqual(r.status_code, 200)


class CrudResultadoTests(BaseApollo):
    def _enviar(self, cliente):
        r = cliente.post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": prova_completa(erradas={1})}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.data["id"]

    def test_aluno_le_so_os_seus_resultados(self):
        self._enviar(self.client)
        outro = APIClient(); outro.force_authenticate(self.outro.user)
        dados = self.client.get("/api/resultados/").data
        self.assertEqual(len(dados["results"] if "results" in dados else dados), 1)
        dados = outro.get("/api/resultados/").data
        self.assertEqual(len(dados["results"] if "results" in dados else dados), 0)

    def test_aluno_nao_escreve_resultado(self):
        self._enviar(self.client)
        rid = Resultado.objects.get().id
        self.assertEqual(self.client.patch(f"/api/resultados/{rid}/", {"acertos": 1}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/resultados/{rid}/").status_code, 403)

    def test_staff_faz_crud_completo(self):
        from django.contrib.auth.models import User
        self._enviar(self.client)
        rid = Resultado.objects.get().id
        adm = APIClient(); adm.force_authenticate(User.objects.create_user("adm", "adm@x.com", "senha-forte-123", is_staff=True))
        self.assertEqual(adm.get(f"/api/resultados/{rid}/").status_code, 200)
        self.assertEqual(adm.patch(f"/api/resultados/{rid}/", {"brancos": 2}, format="json").status_code, 200)
        self.assertEqual(Resultado.objects.get(pk=rid).brancos, 2)
        self.assertEqual(adm.delete(f"/api/resultados/{rid}/").status_code, 204)
        self.assertEqual(Resultado.objects.count(), 0)

    def test_aluno_apaga_a_propria_submissao_e_nao_a_alheia(self):
        sid = self._enviar(self.client)
        outro = APIClient(); outro.force_authenticate(self.outro.user)
        self.assertEqual(outro.delete(f"/api/submissoes/{sid}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/submissoes/{sid}/").status_code, 204)
        self.assertEqual((Submissao.objects.count(), Resultado.objects.count()), (0, 0))


class CorDoDiaTests(TestCase):
    """Cada dia tem um caderno de 90 questões: as duas áreas do dia têm a mesma cor (2017+: LC/CH e CN/MT; 2016: CH/CN e LC/MT)."""

    @classmethod
    def setUpTestData(cls):
        for ano in ("2016", "2023"):
            call_command("importar_inep", ARQUIVO_ITENS, "--ano", ano, verbosity=0)
        cls.aluno = criar_aluno("dia@x.com")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.aluno.user)

    def _enviar(self, ano, area, cor):
        resp = [{"numero": q.numero, "alternativa": q.gabarito if q.gabarito in list("ABCDE") else ""}
                for q in Questao.objects.filter(edicao__ano=ano, area=area, cor=cor, lingua__in=["", "EN"])]
        r = self.client.post("/api/submissoes/", {"ano": ano, "area": area, "cor": cor, "respostas": resp}, format="json")
        return r

    def test_parceiras_por_ano(self):
        from .services import area_parceira
        self.assertEqual([area_parceira(2023, a) for a in ("LC", "CH", "CN", "MT")], ["CH", "LC", "MT", "CN"])
        self.assertEqual([area_parceira(2016, a) for a in ("LC", "CH", "CN", "MT")], ["MT", "CN", "CH", "LC"])

    def test_mesma_cor_no_par_passa(self):
        self.assertEqual(self._enviar(2023, "CN", "AZUL").status_code, 201)
        self.assertEqual(self._enviar(2023, "MT", "AZUL").status_code, 201)

    def test_cor_diferente_no_par_e_recusada_sem_gravar(self):
        self.assertEqual(self._enviar(2023, "CN", "AZUL").status_code, 201)
        r = self._enviar(2023, "MT", "AMARELA")
        self.assertEqual(r.status_code, 400)
        self.assertIn("mesma cor", str(r.data["cor"]))
        self.assertFalse(Submissao.objects.filter(area="MT").exists())

    def test_dias_diferentes_podem_ter_cores_diferentes(self):
        self.assertEqual(self._enviar(2023, "LC", "AZUL").status_code, 201)
        self.assertEqual(self._enviar(2023, "CN", "AMARELA").status_code, 201)

    def test_area_sem_parceira_enviada_passa(self):
        self.assertEqual(self._enviar(2023, "CH", "ROSA").status_code, 201)

    def test_em_2016_o_par_e_outro(self):
        self.assertEqual(self._enviar(2016, "LC", "AZUL").status_code, 201)
        self.assertEqual(self._enviar(2016, "MT", "AMARELA").status_code, 400)  # MT é parceira de LC em 2016
        self.assertEqual(self._enviar(2016, "CH", "AMARELA").status_code, 201)  # CH não depende de LC em 2016

    def test_excluir_e_reenviar_corrige_a_cor(self):
        errada = self._enviar(2023, "CN", "AMARELA").data["id"]
        self.assertEqual(self._enviar(2023, "MT", "AZUL").status_code, 400)
        self.assertEqual(self.client.delete(f"/api/submissoes/{errada}/").status_code, 204)
        self.assertEqual(self._enviar(2023, "CN", "AZUL").status_code, 201)
        self.assertEqual(self._enviar(2023, "MT", "AZUL").status_code, 201)

    def test_outro_aluno_nao_e_afetado(self):
        self.assertEqual(self._enviar(2023, "CN", "AZUL").status_code, 201)
        outro = criar_aluno("outro@x.com")
        self.client.force_authenticate(outro.user)
        self.assertEqual(self._enviar(2023, "MT", "AMARELA").status_code, 201)

    def test_checar_cores_lista_inconsistencias_antigas(self):
        from io import StringIO
        a, b = (Submissao.objects.create(aluno=self.aluno, edicao=EdicaoEnem.objects.get(ano=2023), area=ar, cor=c)
                for ar, c in (("CN", "AZUL"), ("MT", "AMARELA")))
        out = StringIO(); call_command("checar_cores", stdout=out)
        self.assertIn("CN=AZUL", out.getvalue()); self.assertIn("1 inconsistência", out.getvalue())
        b.delete()
        out = StringIO(); call_command("checar_cores", stdout=out)
        self.assertIn("Nenhuma", out.getvalue())


class ExclusaoNaTelaTests(TestCase):
    def test_dashboard_tem_botao_de_exclusao_com_confirmacao(self):
        html = APIClient().get("/dashboard/").content.decode()
        self.assertIn("data-del", html)
        self.assertIn("Confirmar exclusão", html)

    def test_aluno_apaga_so_a_propria_submissao(self):
        a, b = criar_aluno("del1@x.com"), criar_aluno("del2@x.com")
        ed = EdicaoEnem.objects.create(ano=2023)
        sa = Submissao.objects.create(aluno=a, edicao=ed, area="CN", cor="AZUL")
        c = APIClient(); c.force_authenticate(b.user)
        self.assertEqual(c.delete(f"/api/submissoes/{sa.pk}/").status_code, 404)
        c.force_authenticate(a.user)
        self.assertEqual(c.delete(f"/api/submissoes/{sa.pk}/").status_code, 204)


class ChaosRegressaoTests(TestCase):
    """Achados do chaos test: entradas hostis devem dar 400 tratado, nunca 500."""

    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno("chaos@x.com")

    def setUp(self):
        self.client = APIClient()

    def _post(self, caminho, corpo=None, raw=None):
        if raw is not None:
            return self.client.post(caminho, data=raw, content_type="application/json")
        return self.client.post(caminho, corpo, format="json")

    def test_login_com_corpo_ou_tipos_estranhos_da_400(self):
        for raw in (b"[]", b"null", b'"x"', b"{", b"", b'{"email":null,"senha":null}', b'{"email":true,"senha":1}',
                    b'{"email":[],"senha":{}}', b'{"email":"a\\u0000b@x.com","senha":"x"}', b'{"email":"a@x.com","senha":"\\u0000"}'):
            r = self._post("/api/login/", raw=raw)
            self.assertEqual(r.status_code, 400, raw)

    def test_login_valido_continua_funcionando(self):
        self.assertEqual(self._post("/api/login/", {"email": "chaos@x.com", "senha": "senha-forte-123"}).status_code, 200)

    def test_json_absurdamente_aninhado_da_400(self):
        fundo = ('{"a":' * 200_000 + "1" + "}" * 200_000).encode()
        for caminho in ("/api/cadastro/", "/api/login/"):
            self.assertEqual(self._post(caminho, raw=fundo).status_code, 400, caminho)

    def test_corpo_gigante_e_recusado(self):
        r = self._post("/api/cadastro/", raw=b'{"nome":"' + b"A" * 300_000 + b'"}')
        self.assertEqual(r.status_code, 400)

    def test_respostas_acima_de_90_itens_e_recusado(self):
        self.client.force_authenticate(self.aluno.user)
        r = self._post("/api/submissoes/", {"ano": 2023, "area": "MT", "respostas": [{"numero": 1, "alternativa": "A"}] * 91})
        self.assertEqual(r.status_code, 400)
        self.assertIn("respostas", r.data)

    def test_filtros_de_questoes_hostis_dao_400_ou_200(self):
        self.client.force_authenticate(self.aluno.user)
        for q in ("area=%00", "area=XX", "ano=%C2%B2", "atributos__x=%00", "cor=%00", "lingua=%00", "ano=" + "9" * 400):
            self.assertLess(self.client.get("/api/questoes/?" + q).status_code, 500, q)

    def test_nome_longo_nao_estoura_o_layout(self):
        for pagina in ("home", "dashboard"):
            html = APIClient().get(f"/{pagina}/").content.decode()
            self.assertIn("overflow-wrap:anywhere", html, pagina)


class RaizApiPublicaTests(TestCase):
    def test_raiz_da_api_lista_rotas_sem_login(self):
        r = self.client.get("/api/", follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn("questoes", r.json())

    def test_dados_continuam_exigindo_login(self):
        self.assertEqual(self.client.get("/api/questoes/").status_code, 403)
        self.assertEqual(self.client.get("/api/alunos/").status_code, 403)
