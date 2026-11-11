from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.routers import APIRootView, DefaultRouter

from . import views


class RaizPublica(APIRootView):
    """Índice dos endpoints (/api/). Só lista as rotas; os dados continuam exigindo login."""
    permission_classes = [AllowAny]


class RouterApollo(DefaultRouter):
    APIRootView = RaizPublica


router = RouterApollo()
router.register("edicoes", views.EdicaoViewSet, basename="edicao")
router.register("questoes", views.QuestaoViewSet, basename="questao")
router.register("alunos", views.AlunoViewSet, basename="aluno")
router.register("submissoes", views.SubmissaoViewSet, basename="submissao")
router.register("resultados", views.ResultadoViewSet, basename="resultado")

urlpatterns = [
    path("cadastro/", views.cadastro),
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("dashboard/", views.dashboard),
    path("matriz/", views.matriz),
    path("", include(router.urls)),
]
