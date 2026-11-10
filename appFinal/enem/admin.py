from django.contrib import admin

from .models import Aluno, EdicaoEnem, Questao, RespostaInformada, Resultado, Submissao


@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    list_display = ("edicao", "area", "cor", "numero", "gabarito", "anulada")
    list_filter = ("edicao", "area", "cor", "anulada")


class RespostaInline(admin.TabularInline):
    model = RespostaInformada
    extra = 0
    raw_id_fields = ("questao",)


@admin.register(Submissao)
class SubmissaoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "edicao", "area", "cor", "criada_em")
    inlines = [RespostaInline]


admin.site.register(Aluno)
admin.site.register(EdicaoEnem)
admin.site.register(Resultado)
