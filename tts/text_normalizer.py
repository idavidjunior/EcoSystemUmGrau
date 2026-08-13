"""TextNormalizer — normaliza texto para fala natural em pt-BR.

Responsável por:
- Converter horas digitais para leitura natural
- Ajustar pontuação para pausas
- Inserir vírgulas de respiração em frases longas
- Capitalizar inícios de frase
- Garantir pontuação final
"""
import re
from typing import List

from .config import (
    CONECTORES_INICIAIS,
    CONECTORES_MEIO,
    RESPIRACAO,
    MAX_TEXT_LENGTH,
)


class TextNormalizer:
    """Normaliza texto para fala natural em português brasileiro.

    Uso:
        normalizer = TextNormalizer()
        texto_normal = normalizer.normalize(texto_bruto)
    """

    def __init__(self):
        # Compila regex de respiração uma vez
        self._respiracao_pattern = re.compile(
            r'(?<![,.;:!?])\s+(?:' +
            '|'.join(re.escape(c) for c in RESPIRACAO) +
            r')\s+',
            re.IGNORECASE
        )

    def normalize(self, text: str) -> str:
        """Normaliza o texto completo para fala natural.

        Args:
            text: Texto já limpo de markdown/código.

        Returns:
            Texto normalizado, pronto para síntese.
        """
        if not text:
            return ""

        t = text.strip()

        # 1. Normalizar espaços
        t = re.sub(r'\s+', ' ', t)

        # 2. Converter horas para leitura natural
        t = self._normalize_hours(t)

        # 3. Converter datas para leitura natural
        t = self._normalize_dates(t)

        # 4. Converter números por extenso quando apropriado
        t = self._normalize_numbers(t)

        # 5. Normalizar pontuação
        t = self._normalize_punctuation(t)

        # 6. Inserir respirações em frases longas
        t = self._insert_breathing(t)

        # 7. Capitalizar inícios de frase
        t = self._capitalize_sentences(t)

        # 8. Garantir pontuação final
        t = self._ensure_final_punctuation(t)

        # 9. Limpeza final
        t = self._final_cleanup(t)

        return t

    def _normalize_hours(self, text: str) -> str:
        """Converte horas digitais para leitura natural.

        "21:44" -> "21 horas e 44"
        "22:00" -> "22 horas em ponto"
        """
        # HH:00 -> HH horas em ponto
        text = re.sub(r'\b(\d{1,2}):00\b', r'\1 horas em ponto', text)
        # HH:MM -> HH horas e MM
        text = re.sub(r'\b(\d{1,2}):(\d{2})\b', r'\1 horas e \2', text)
        return text

    def _normalize_dates(self, text: str) -> str:
        """Converte formatos de data para leitura natural.

        "31/07/2026" -> "31 de julho de 2026"
        "01/08" -> "1 de agosto"
        """
        meses = {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto",
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
        }

        def _replace_date(m):
            dia = int(m.group(1))
            mes = int(m.group(2))
            ano = m.group(3)
            if mes in meses:
                resultado = f"{dia} de {meses[mes]}"
                if ano:
                    resultado += f" de {ano}"
                return resultado
            return m.group(0)

        # DD/MM/AAAA ou DD/MM/AA
        text = re.sub(
            r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b',
            _replace_date,
            text
        )
        return text

    def _normalize_numbers(self, text: str) -> str:
        """Converte números para extenso quando apropriado.

        Exemplos:
        - "CPU em 85%" -> "CPU em 85 por cento"
        - "bateria em 20%" -> "bateria em 20 por cento"
        """
        # Porcentagem
        text = re.sub(r'(\d+)%', r'\1 por cento', text)
        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Normaliza pontuação para pausas naturais.

        - Travessões -> vírgula
        - Vírgulas extras -> uma vírgula
        - Espaço antes de pontuação -> remove
        - Espaço depois de pontuação -> garante
        """
        # Travessões e rays -> vírgula
        text = re.sub(r'\s*[—–]\s*', ', ', text)
        text = re.sub(r'\s+-\s+', ', ', text)

        # Ponto e vírgula e dois-pontos -> vírgula (pausa natural)
        text = text.replace(';', ',')
        text = text.replace(':', ',')

        # Remove pontuação no início
        text = re.sub(r'^[,;\s]+', '', text)

        # Remove espaços antes de pontuação
        text = re.sub(r'\s+([,.;:?!])', r'\1', text)

        # Garante espaço depois de pontuação
        text = re.sub(r'([,.;:?!])(?=\S)', r'\1 ', text)

        # Remove vírgulas múltiplas
        text = re.sub(r',{2,}', ',', text)

        # Remove espaço antes de reticências
        text = re.sub(r'\.{3,}', '...', text)

        return text

    def _insert_breathing(self, text: str) -> str:
        """Insere vírgulas de respiração em frases longas.

        Obras com mais de 16 palavras ganham vírgula antes do conectivo
        mais próximo do meio da frase.
        """
        oracoes = re.split(r'(?<=[.!?])\s+', text)
        resultado = []
        for oracao in oracoes:
            oracao = oracao.strip()
            if not oracao:
                continue
            if len(oracao.split()) > 16:
                oracao = self._add_breathing_point(oracao)
            resultado.append(oracao)
        return ' '.join(resultado)

    def _add_breathing_point(self, sentence: str) -> str:
        """Adiciona ponto de respiração em oração longa."""
        matches = list(self._respiracao_pattern.finditer(sentence))
        if not matches:
            return sentence
        centro = len(sentence) // 2
        melhor = min(matches, key=lambda m: abs(m.start() - centro))
        return sentence[:melhor.start()].rstrip() + ', ' + sentence[melhor.start():].strip()

    def _capitalize_sentences(self, text: str) -> str:
        """Capitaliza a primeira letra de cada frase."""
        def _cap(m):
            return m.group(1) + m.group(2).upper()

        # Capitaliza após início de texto
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        # Capitaliza após . ? ! seguido de espaço
        text = re.sub(r'([.!?]\s+)(\w)', _cap, text)

        # Capitaliza conectores iniciais
        for c in CONECTORES_INICIAIS:
            text = re.sub(
                rf'^(?i:{re.escape(c)})\s+',
                f'{c.capitalize()}, ',
                text
            )

        return text

    def _ensure_final_punctuation(self, text: str) -> str:
        """Garante que o texto termina com pontuação."""
        text = text.rstrip()
        if text and text[-1] not in '.!?...':
            text += '.'
        return text

    def _final_cleanup(self, text: str) -> str:
        """Limpeza final: espaços extras, vírgulas solitárias, etc."""
        # Remove vírgula no início
        text = re.sub(r'^,\s*', '', text)

        # Remove ponto no início
        text = re.sub(r'^\.\s*', '', text)

        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text)

        # Remove "e," ou "ou," antes de conectivo
        text = re.sub(
            r'\b(e|ou)\s*,\s*(?=depois|então|porém|contudo|portanto|finalmente|enfim)\b',
            r'\1 ',
            text,
            flags=re.IGNORECASE
        )

        return text.strip()
