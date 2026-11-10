import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.db.models import Avg, Count, Q
from django.db.models.fields.json import KeyTextTransform
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .matriz import matriz_publica, titulo_competencia
from .models import AREAS, CORES, Aluno, EdicaoEnem, Questao, RespostaInformada, Resultado, Submissao
from .serializers import (AlunoSerializer, CadastroSerializer, EdicaoSerializer, QuestaoPublicaSerializer,
                          QuestaoSerializer, ResultadoCrudSerializer, SubmissaoEntradaSerializer, SubmissaoSerializer)
from .services import registrar_submissao

CHAVE_ATRIBUTO = re.compile(r"^atributos__[A-Za-z_][A-Za-z0-9_]*$")


def health(_request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "db_indisponivel"}, status=503)


class SomenteLeituraOuStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


class EdicaoViewSet(viewsets.ModelViewSet):
    queryset = EdicaoEnem.objects.all()
    serializer_class = EdicaoSerializer
    permission_classes = [SomenteLeituraOuStaff]


class QuestaoViewSet(viewsets.ModelViewSet):
    """Filtros: ?ano=2023&area=MT&atributos__habilidade=H12 (consulta JSONB indexada)."""
    permission_classes = [SomenteLeituraOuStaff]

    def get_serializer_class(self):
        return QuestaoSerializer if self.request.user.is_staff else QuestaoPublicaSerializer

    def get_queryset(self):
        qs = Questao.objects.select_related("edicao")
        params = self.request.query_params
        if any("\0" in v for v in params.values()):
            raise ValidationError({"detail": "Parâmetro inválido."})
        if params.get("ano"):
            if not (params["ano"].isascii() and params["ano"].isdigit()):
                raise ValidationError({"ano": "Informe um ano numérico."})
            qs = qs.filter(edicao__ano=int(params["ano"]))
        if params.get("area"):
            if params["area"] not in [a for a, _ in AREAS]:
                raise ValidationError({"area": "Área inválida."})
            qs = qs.filter(area=params["area"])
        if params.get("cor"):
            if params["cor"] not in [c for c, _ in CORES]:
                raise ValidationError({"cor": "Cor inválida."})
            qs = qs.filter(cor=params["cor"])
        if params.get("lingua"):
            if params["lingua"] not in ("EN", "ES"):
                raise ValidationError({"lingua": "Use EN ou ES."})
            qs = qs.filter(lingua__in=["", params["lingua"]])
        for chave, valor in params.items():
            if CHAVE_ATRIBUTO.match(chave):
                qs = qs.filter(**{chave: valor})
        return qs


class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    permission_classes = [permissions.IsAdminUser]


class SubmissaoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = SubmissaoSerializer

    def get_queryset(self):
        qs = (Submissao.objects.select_related("edicao", "resultado")
              .prefetch_related("respostas__questao"))
        user = self.request.user
        return qs if user.is_staff else qs.filter(aluno__user=user)

    def create(self, request, *args, **kwargs):
        aluno = getattr(request.user, "aluno", None)
        if aluno is None:
            return Response({"detail": "Usuário sem perfil de aluno."}, status=status.HTTP_403_FORBIDDEN)
        entrada = SubmissaoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        submissao = registrar_submissao(aluno, dados["ano"], dados["area"], dados["respostas"], dados["lingua"], dados["cor"])
        submissao = self.get_queryset().get(pk=submissao.pk)
        return Response(SubmissaoSerializer(submissao).data, status=status.HTTP_201_CREATED)


class ResultadoViewSet(viewsets.ModelViewSet):
    """Leitura: o aluno vê só os seus resultados. Criar/editar/apagar: só staff (o resultado normal nasce na submissão)."""
    serializer_class = ResultadoCrudSerializer
    permission_classes = [SomenteLeituraOuStaff]

    def get_queryset(self):
        qs = Resultado.objects.select_related("submissao")
        user = self.request.user
        return qs if user.is_staff else qs.filter(submissao__aluno__user=user)


@api_view(["GET"])
def matriz(_request):
    """Matriz de Referência: competências de cada área e suas habilidades."""
    return Response(matriz_publica())


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def cadastro(request):
    s = CadastroSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data
    with transaction.atomic():
        user = User.objects.create_user(username=d["email"], email=d["email"], password=d["senha"])
        aluno = Aluno.objects.create(user=user, nome=d["nome"], email=d["email"])
    return Response({"id": aluno.id, "nome": aluno.nome, "email": aluno.email}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    dados = request.data if hasattr(request.data, "get") else {}
    email, senha = dados.get("email"), dados.get("senha")
    if not isinstance(email, str) or not isinstance(senha, str) or "\0" in email or "\0" in senha or len(email) > 254 or len(senha) > 1024:
        return Response({"detail": "Credenciais inválidas."}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, username=email.lower(), password=senha)
    if user is None:
        return Response({"detail": "Credenciais inválidas."}, status=status.HTTP_400_BAD_REQUEST)
    login(request, user)
    return Response({"detail": "ok"})


@api_view(["POST"])
def logout_view(request):
    logout(request)
    return Response({"detail": "ok"})


@api_view(["GET"])
def dashboard(request):
    """Nota TRI por área, evolução e prioridades (mais erros) do aluno logado. `?area=MT` filtra por área."""
    aluno = getattr(request.user, "aluno", None)
    if aluno is None:
        return Response({"detail": "Usuário sem perfil de aluno."}, status=status.HTTP_403_FORBIDDEN)
    area = request.query_params.get("area")
    if area and area not in dict(AREAS):
        raise ValidationError({"area": "Use LC, CH, CN ou MT."})
    resultados = Resultado.objects.filter(submissao__aluno=aluno)
    respondidas = RespostaInformada.objects.filter(submissao__aluno=aluno, questao__anulada=False)
    if area:
        resultados = resultados.filter(submissao__area=area)
        respondidas = respondidas.filter(submissao__area=area)
    por_area = (resultados.values("submissao__area")
                .annotate(media_nota_tri=Avg("nota_tri"), provas=Count("id")).order_by("submissao__area"))
    habilidade = KeyTextTransform("habilidade", "questao__atributos")
    erros = (respondidas
             .annotate(hab=habilidade).values("hab", "questao__area")
             .annotate(total=Count("id"), erros=Count("id", filter=Q(correta=False)))
             .filter(erros__gt=0).order_by("-erros")[:10])
    comp = KeyTextTransform("competencia", "questao__atributos")
    por_comp = (respondidas
                .annotate(comp=comp).values("comp", "questao__area")
                .annotate(total=Count("id"), erros=Count("id", filter=Q(correta=False)))
                .filter(erros__gt=0).order_by("-erros"))[:10]
    eixo = KeyTextTransform("eixo", "questao__atributos")
    por_eixo = (respondidas
                .annotate(eixo=eixo).exclude(eixo__isnull=True).values("eixo", "questao__area")
                .annotate(total=Count("id"), erros=Count("id", filter=Q(correta=False)))
                .filter(erros__gt=0).order_by("-erros"))[:10]
    return Response({
        "aluno": aluno.nome,
        "eixos_prioritarios": [{"eixo": e["eixo"], "area": e["questao__area"], "erros": e["erros"],
                                "total": e["total"], "taxa_erro": round(e["erros"] / e["total"], 2)} for e in por_eixo],
        "competencias_prioritarias": [{"competencia": e["comp"], "area": e["questao__area"],
                                       "titulo": titulo_competencia(e["questao__area"], e["comp"]),
                                       "erros": e["erros"], "total": e["total"],
                                       "taxa_erro": round(e["erros"] / e["total"], 2)} for e in por_comp],
        "por_area": [{"area": r["submissao__area"], "media_nota_tri": round(float(r["media_nota_tri"]), 1),
                      "provas": r["provas"]} for r in por_area],
        "habilidades_prioritarias": [{"habilidade": e["hab"], "area": e["questao__area"], "erros": e["erros"],
                                      "total": e["total"], "taxa_erro": round(e["erros"] / e["total"], 2)} for e in erros],
        "historico": [{"submissao": r.submissao_id, "ano": r.submissao.edicao.ano, "area": r.submissao.area, "cor": r.submissao.cor,
                       "lingua": r.submissao.lingua, "criada_em": r.submissao.criada_em.isoformat(),
                       "nota_tri": float(r.nota_tri), "acertos": r.acertos, "erros": r.erros, "brancos": r.brancos}
                      for r in resultados.select_related("submissao__edicao").order_by("-submissao__criada_em")[:50]],
    })
