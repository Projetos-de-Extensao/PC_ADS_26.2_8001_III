from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from django.db import models

AREAS = [
    ("LC", "Linguagens, Códigos e suas Tecnologias"),
    ("CH", "Ciências Humanas e suas Tecnologias"),
    ("CN", "Ciências da Natureza e suas Tecnologias"),
    ("MT", "Matemática e suas Tecnologias"),
]
ALTERNATIVAS = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E")]
QUESTOES_POR_AREA = 45
# Linguagens: as questões 1–5 existem em inglês e em espanhol; as demais são comuns (lingua vazia).
LINGUAS = [("", "Comum"), ("EN", "Inglês"), ("ES", "Espanhol")]
# Cadernos regulares do dia: 4 cores por área/ano (variam por edição). AZUL é o padrão.
CORES = [("AZUL", "Azul"), ("AMARELA", "Amarela"), ("ROSA", "Rosa"), ("BRANCA", "Branca"), ("CINZA", "Cinza"), ("VERDE", "Verde")]


class Aluno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="aluno", null=True, blank=True)
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.nome


class EdicaoEnem(models.Model):
    ano = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["ano"]
        verbose_name = "edição do ENEM"
        verbose_name_plural = "edições do ENEM"

    def __str__(self):
        return f"ENEM {self.ano}"


class Questao(models.Model):
    edicao = models.ForeignKey(EdicaoEnem, on_delete=models.CASCADE, related_name="questoes")
    area = models.CharField(max_length=2, choices=AREAS)
    cor = models.CharField(max_length=10, choices=CORES, default="AZUL")  # caderno (a numeração muda por cor)
    numero = models.PositiveSmallIntegerField()
    lingua = models.CharField(max_length=2, choices=LINGUAS, blank=True, default="")
    # Item abandonado/anulado pelo INEP: aparece na prova, mas não entra na pontuação nem na análise.
    anulada = models.BooleanField(default=False)
    gabarito = models.CharField(max_length=1, choices=ALTERNATIVAS)
    # Atributos livres: habilidade, competencia, assunto... (JSONB, índice GIN)
    atributos = models.JSONField(default=dict, blank=True)
    # Parâmetros TRI (modelo logístico de 3 parâmetros)
    param_a = models.FloatField(default=1.0)
    param_b = models.FloatField(default=0.0)
    param_c = models.FloatField(default=0.2)

    class Meta:
        ordering = ["edicao__ano", "area", "cor", "numero", "lingua"]
        constraints = [
            models.UniqueConstraint(fields=["edicao", "area", "cor", "numero", "lingua"], name="questao_unica_por_edicao_area_cor_numero_lingua"),
        ]
        indexes = [GinIndex(fields=["atributos"], name="questao_atributos_gin")]
        verbose_name = "questão"
        verbose_name_plural = "questões"

    def __str__(self):
        return f"{self.edicao} · {self.area} · Q{self.numero}"


class Submissao(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="submissoes")
    edicao = models.ForeignKey(EdicaoEnem, on_delete=models.PROTECT, related_name="submissoes")
    area = models.CharField(max_length=2, choices=AREAS)
    cor = models.CharField(max_length=10, choices=CORES, default="AZUL")
    lingua = models.CharField(max_length=2, choices=LINGUAS, blank=True, default="")  # idioma escolhido (só LC)
    criada_em = models.DateTimeField(auto_now_add=True)
    questoes = models.ManyToManyField(Questao, through="RespostaInformada", related_name="submissoes")

    class Meta:
        ordering = ["-criada_em"]
        verbose_name = "submissão"
        verbose_name_plural = "submissões"

    def __str__(self):
        return f"{self.aluno} · {self.edicao} · {self.area}"


class RespostaInformada(models.Model):
    submissao = models.ForeignKey(Submissao, on_delete=models.CASCADE, related_name="respostas")
    questao = models.ForeignKey(Questao, on_delete=models.PROTECT, related_name="respostas")
    alternativa = models.CharField(max_length=1, choices=ALTERNATIVAS, blank=True)  # vazio = em branco
    correta = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["submissao", "questao"], name="resposta_unica_por_questao"),
        ]


class Resultado(models.Model):
    submissao = models.OneToOneField(Submissao, on_delete=models.CASCADE, related_name="resultado")
    acertos = models.PositiveSmallIntegerField()
    erros = models.PositiveSmallIntegerField()
    brancos = models.PositiveSmallIntegerField()
    nota_tri = models.DecimalField(max_digits=6, decimal_places=1)
    analise = models.JSONField(default=dict, blank=True)  # erros por habilidade nesta submissão
