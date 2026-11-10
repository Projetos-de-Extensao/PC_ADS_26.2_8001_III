from django.core.management.base import BaseCommand

from enem.models import Submissao
from enem.services import PARES_2016, PARES_PADRAO


class Command(BaseCommand):
    help = "Lista submissões cujas áreas do mesmo dia (mesmo caderno) têm cores diferentes. Não altera nada."

    def handle(self, *args, **opts):
        ultimas = {}
        for s in Submissao.objects.select_related("aluno", "edicao").order_by("criada_em", "pk"):
            ultimas[(s.aluno_id, s.edicao.ano, s.area)] = s
        achou = 0
        for (aluno_id, ano, _), s in sorted(ultimas.items(), key=lambda kv: kv[0][:2]):
            for a, b in (PARES_2016 if ano == 2016 else PARES_PADRAO):
                if s.area != a:
                    continue
                o = ultimas.get((aluno_id, ano, b))
                if o and o.cor != s.cor:
                    achou += 1
                    self.stdout.write(f"{s.aluno.email} · ENEM {ano}: {a}={s.cor} (id {s.pk}) x {b}={o.cor} (id {o.pk})")
        self.stdout.write(self.style.WARNING(f"{achou} inconsistência(s). Exclua o envio errado e reenvie.") if achou
                          else self.style.SUCCESS("Nenhuma inconsistência de cor."))
