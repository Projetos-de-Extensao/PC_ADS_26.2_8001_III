import random

from django.core.management.base import BaseCommand
from django.db import transaction

from enem.matriz import competencia_de
from enem.models import AREAS, QUESTOES_POR_AREA, EdicaoEnem, Questao

ANOS = range(2016, 2026)  # ENEM 2016 a 2025
ASSUNTOS = {
    "LC": ["Interpretação de texto", "Gêneros textuais", "Variação linguística", "Literatura", "Língua estrangeira"],
    "CH": ["História do Brasil", "Geografia física", "Filosofia", "Sociologia", "Geopolítica"],
    "CN": ["Ecologia", "Genética", "Física - Mecânica", "Química orgânica", "Eletricidade"],
    "MT": ["Geometria", "Estatística", "Funções", "Probabilidade", "Razão e proporção"],
}


class Command(BaseCommand):
    help = "Carrega edições 2016-2025 e 45 questões por área. Idempotente."

    @transaction.atomic
    def handle(self, *args, **opts):
        criadas = 0
        for ano in ANOS:
            edicao, _ = EdicaoEnem.objects.get_or_create(ano=ano)
            for area, _nome in AREAS:
                if Questao.objects.filter(edicao=edicao, area=area).exists():
                    continue  # já há questões (ex.: importadas do INEP): não sobrescreve
                rng = random.Random(f"{ano}-{area}")  # determinístico
                for n in range(1, QUESTOES_POR_AREA + 1):
                    hab = f"H{rng.randint(1, 30)}"
                    _, nova = Questao.objects.get_or_create(
                        edicao=edicao, area=area, numero=n,
                        defaults={
                            "gabarito": rng.choice("ABCDE"),
                            "atributos": {
                                "habilidade": hab,
                                "competencia": competencia_de(area, hab),
                                "assunto": rng.choice(ASSUNTOS[area]),
                            },
                            "param_a": round(rng.uniform(0.8, 2.2), 2),
                            "param_b": round(rng.uniform(-1.5, 2.0), 2),
                            "param_c": 0.2,
                        },
                    )
                    criadas += nova
        self.stdout.write(self.style.SUCCESS(f"Seed concluído: {criadas} questões novas."))
