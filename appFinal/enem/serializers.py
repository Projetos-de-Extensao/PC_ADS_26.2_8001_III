from rest_framework import serializers

from .models import ALTERNATIVAS, AREAS, CORES, Aluno, EdicaoEnem, Questao, RespostaInformada, Resultado, Submissao


class EdicaoSerializer(serializers.ModelSerializer):
    total_questoes = serializers.SerializerMethodField()  # conta uma prova (inglês), sem duplicar o espanhol

    def get_total_questoes(self, obj):
        return obj.questoes.filter(cor="AZUL").exclude(lingua="ES").count()

    def get_cores(self, obj):
        """Cadernos disponíveis por área: {"LC": ["AZUL", "AMARELA", ...], ...} (AZUL primeiro)."""
        ordem = [c for c, _ in CORES]
        achadas = obj.questoes.order_by().values_list("area", "cor").distinct()
        saida = {}
        for area, cor in achadas:
            saida.setdefault(area, []).append(cor)
        return {a: sorted(cs, key=ordem.index) for a, cs in sorted(saida.items())}

    cores = serializers.SerializerMethodField()

    class Meta:
        model = EdicaoEnem
        fields = ["id", "ano", "total_questoes", "cores"]


class QuestaoSerializer(serializers.ModelSerializer):
    """Visão administrativa (inclui gabarito e parâmetros TRI)."""

    class Meta:
        model = Questao
        fields = ["id", "edicao", "area", "cor", "numero", "lingua", "anulada", "gabarito", "atributos", "param_a", "param_b", "param_c"]


class QuestaoPublicaSerializer(serializers.ModelSerializer):
    """Visão do aluno: nunca expõe gabarito."""

    class Meta:
        model = Questao
        fields = ["id", "edicao", "area", "cor", "numero", "lingua", "anulada", "atributos"]


class AlunoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = ["id", "nome", "email"]


class RespostaSerializer(serializers.ModelSerializer):
    numero = serializers.IntegerField(source="questao.numero", read_only=True)
    habilidade = serializers.CharField(source="questao.atributos.habilidade", read_only=True, default=None)
    anulada = serializers.BooleanField(source="questao.anulada", read_only=True)

    class Meta:
        model = RespostaInformada
        fields = ["numero", "alternativa", "correta", "anulada", "habilidade"]


class ResultadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resultado
        fields = ["acertos", "erros", "brancos", "nota_tri", "analise"]


class ResultadoCrudSerializer(serializers.ModelSerializer):
    """CRUD do resultado (escrita só staff; o aluno lê os seus)."""

    class Meta:
        model = Resultado
        fields = ["id", "submissao", "acertos", "erros", "brancos", "nota_tri", "analise"]


class SubmissaoSerializer(serializers.ModelSerializer):
    """Leitura: submissão com respostas e resultado aninhados."""
    respostas = RespostaSerializer(many=True, read_only=True)
    resultado = ResultadoSerializer(read_only=True)
    ano = serializers.IntegerField(source="edicao.ano", read_only=True)

    class Meta:
        model = Submissao
        fields = ["id", "ano", "area", "cor", "lingua", "criada_em", "resultado", "respostas"]


class ItemRespostaSerializer(serializers.Serializer):
    numero = serializers.IntegerField(min_value=1, max_value=90)
    alternativa = serializers.ChoiceField(choices=[c[0] for c in ALTERNATIVAS], allow_blank=True, required=False)


class SubmissaoEntradaSerializer(serializers.Serializer):
    ano = serializers.IntegerField()
    area = serializers.ChoiceField(choices=[a[0] for a in AREAS])
    cor = serializers.ChoiceField(choices=[c[0] for c in CORES], required=False, default="AZUL")  # caderno da prova
    lingua = serializers.ChoiceField(choices=["EN", "ES"], required=False, default="EN")  # só vale em LC
    respostas = ItemRespostaSerializer(many=True, allow_empty=False, max_length=90)

    def validate_ano(self, valor):
        try:
            return EdicaoEnem.objects.get(ano=valor)
        except EdicaoEnem.DoesNotExist:
            raise serializers.ValidationError(f"Edição {valor} não cadastrada.")


class CadastroSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, valor):
        if Aluno.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return valor.lower()
