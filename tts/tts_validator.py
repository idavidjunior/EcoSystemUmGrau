"""TTSValidator — valida texto antes da síntese TTS.

Última verificação antes de enviar ao motor de voz. Garante que o texto
está dentro dos limites e não contém caracteres problemáticos.
"""
import re
from typing import Tuple

from .config import (
    MIN_TEXT_LENGTH,
    MAX_TEXT_LENGTH,
    FORBIDDEN_CHARS,
)
from .exceptions import TextTooShortError, TextTooLongError, ValidationError


class TTSValidator:
    """Valida texto para TTS.

    Uso:
        validator = TTSValidator()
        texto_valido = validator.validate(texto)
    """

    def __init__(self, min_length: int = MIN_TEXT_LENGTH, max_length: int = MAX_TEXT_LENGTH):
        self._min_length = min_length
        self._max_length = max_length

    def validate(self, text: str) -> str:
        """Valida e sanitiza o texto final para TTS.

        Args:
            text: Texto já processado pelo pipeline.

        Returns:
            Texto validado e pronto para síntese.

        Raises:
            TextTooShortError: Se texto muito curto.
            TextTooLongError: Se texto excede limite.
            ValidationError: Se contém caracteres proibidos.
        """
        if not text:
            raise TextTooShortError("Texto vazio")

        text = text.strip()

        # Comprimento mínimo
        if len(text) < self._min_length:
            raise TextTooShortError(
                f"Texto muito curto ({len(text)} < {self._min_length})"
            )

        # Caracteres proibidos
        found_forbidden = set(text) & FORBIDDEN_CHARS
        if found_forbidden:
            # Remove caracteres proibidos
            text = ''.join(c for c in text if c not in FORBIDDEN_CHARS)

        # Comprimento máximo (recorta se exceder)
        if len(text) > self._max_length:
            # Tenta cortar em ponto final
            cortado = text[:self._max_length]
            ultimo_ponto = max(
                cortado.rfind('.'),
                cortado.rfind('!'),
                cortado.rfind('?'),
            )
            if ultimo_ponto > self._min_length:
                text = cortado[:ultimo_ponto + 1]
            else:
                text = cortado

        # Verificação final de comprimento
        if len(text) < self._min_length:
            raise TextTooShortError(
                f"Texto resultante muito curto ({len(text)} < {self._min_length})"
            )

        return text

    def is_valid(self, text: str) -> Tuple[bool, str]:
        """Verifica validade sem modificar o texto.

        Returns:
            Tupla (é_válido, mensagem_erro).
        """
        if not text or not text.strip():
            return False, "Texto vazio"

        text = text.strip()

        if len(text) < self._min_length:
            return False, f"Texto muito curto ({len(text)} < {self._min_length})"

        if len(text) > self._max_length:
            return False, f"Texto muito longo ({len(text)} > {self._max_length})"

        found_forbidden = set(text) & FORBIDDEN_CHARS
        if found_forbidden:
            return False, f"Caracteres proibidos: {''.join(found_forbidden)}"

        return True, ""

    def sanitize(self, text: str) -> str:
        """Remove apenas caracteres problemáticos, sem validar comprimento."""
        if not text:
            return ""
        text = ''.join(c for c in text if c not in FORBIDDEN_CHARS)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
