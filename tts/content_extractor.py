"""ContentExtractor — extrai texto falável dos segmentos classificados.

Recebe os segmentos do ContentClassifier e monta o texto final que será
enviado ao TTS, substituindo/removendo conteúdo não falável.
"""
from typing import List

from .content_classifier import ClassifiedSegment, ContentType


class ContentExtractor:
    """Extrai texto falável de segmentos classificados.

    Uso:
        extractor = ContentExtractor()
        texto_falavel = extractor.extract(segments)
    """

    # Substituições para quando queremos mencionar que algo existe
    # mas sem ler o conteúdo
    _BLOCK_LABELS = {
        ContentType.CODE_BLOCK: " trecho de código ",
        ContentType.JSON: " trecho de código ",
        ContentType.XML: " trecho de código ",
        ContentType.TABLE: " tabela ",
        ContentType.LOG: " log de sistema ",
    }

    def extract(self, segments: List[ClassifiedSegment]) -> str:
        """Extrai texto falável de uma lista de segmentos classificados.

        Args:
            segments: Lista de ClassifiedSegment do ContentClassifier.

        Returns:
            Texto limpo, pronto para normalização e síntese.
        """
        parts = []
        for seg in segments:
            if seg.should_speak:
                # Tem substituição? Usa. Senão, usa o texto original.
                text = seg.replacement if seg.replacement else seg.text
                parts.append(text)
            elif seg.content_type in self._BLOCK_LABELS:
                # Para blocos bloqueados, insere uma menção leve
                label = self._BLOCK_LABELS[seg.content_type]
                parts.append(label)
            # Para outros tipos não faláveis (emojis, markdown markers),
            # simplesmente não adiciona nada

        return " ".join(parts)

    def extract_with_context(self, segments: List[ClassifiedSegment]) -> str:
        """Versão mais elaborada: preserva contexto para o falante.

        Exemplo: se o texto tem "Veja o código: ```...```", retorna
        "Veja o código, trecho de código." ao invés de apenas "Veja o código."
        """
        parts = []
        prev_type = None

        for seg in segments:
            if seg.should_speak:
                text = seg.replacement if seg.replacement else seg.text
                parts.append(text)
            elif seg.content_type in self._BLOCK_LABELS:
                label = self._BLOCK_LABELS[seg.content_type]
                # Se o texto anterior termina com ":", não duplica a vírgula
                if parts and parts[-1].rstrip().endswith(':'):
                    parts.append(label.strip())
                else:
                    parts.append(label)

            prev_type = seg.content_type

        return " ".join(parts)
