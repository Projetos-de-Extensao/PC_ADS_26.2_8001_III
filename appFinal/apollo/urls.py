from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from enem.views import health

urlpatterns = [
    path("", ensure_csrf_cookie(TemplateView.as_view(template_name="landing.html")), name="landing"),
    path("login/", ensure_csrf_cookie(TemplateView.as_view(template_name="login.html")), name="login"),
    path("home/", ensure_csrf_cookie(TemplateView.as_view(template_name="home.html")), name="home"),
    path("enviar/", ensure_csrf_cookie(TemplateView.as_view(template_name="enviar.html")), name="enviar"),
    path("dashboard/", ensure_csrf_cookie(TemplateView.as_view(template_name="dashboard.html")), name="dashboard"),
    path("health/", health),
    path("admin/", admin.site.urls),
    path("api/", include("enem.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
