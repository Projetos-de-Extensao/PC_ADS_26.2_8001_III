from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser

LIMITE_CORPO = 256 * 1024  # uma prova válida tem ~3 KB; 256 KB já é muito folgado


class JSONSeguro(JSONParser):
    """JSON com tamanho limitado e sem estouro de recursão (aninhamento absurdo vira 400, não 500)."""

    def parse(self, stream, media_type=None, parser_context=None):
        request = (parser_context or {}).get("request")
        tam = request.META.get("CONTENT_LENGTH") if request is not None else None
        if tam and tam.isdigit() and int(tam) > LIMITE_CORPO:
            raise ParseError("Corpo da requisição grande demais.")
        try:
            return super().parse(stream, media_type, parser_context)
        except RecursionError:
            raise ParseError("JSON aninhado demais.")
