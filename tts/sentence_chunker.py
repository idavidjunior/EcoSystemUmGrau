"""SentenceChunker — divide texto em sentenças para processamento TTS.

O edge-tts tem limites de tamanho por requisição. Este módulo divide
o texto em sentenças completas, respeitando pontuação e limite de palavras.
"""
import re
from typing import List

from .config import MAX_CHUNK_WORDS


class SentenceChunker:
    """Divide texto em sentenças para processamento TTS.

    Uso:
        chunker = SentenceChunker()
        chunks = chunker.chunk(texto_normalizado)
    """

    # Padrão para quebrar em sentenças (respectando pontuação)
    _SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

    # Padrão para quebrar sentença longa em cláusulas
    _CLAUSE_SPLIT = re.compile(r',\s+')

    def __init__(self, max_words: int = MAX_CHUNK_WORDS):
        self._max_words = max_words

    def chunk(self, text: str) -> List[str]:
        """Divide o texto em chunks prontos para TTS.

        Cada chunk é uma sentença ou cláusula completa, com no máximo
        max_words palavras.

        Args:
            text: Texto normalizado.

        Returns:
            Lista de strings, cada uma pronta para uma chamada TTS.
        """
        if not text:
            return []

        # Primeiro: divide em sentenças
        sentences = self._SENTENCE_SPLIT.split(text.strip())

        # Depois: quebra sentenças longas em cláusulas
        chunks = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            word_count = len(sentence.split())
            if word_count <= self._max_words:
                chunks.append(sentence)
            else:
                # Quebra em cláusulas
                clauses = self._CLAUSE_SPLIT.split(sentence)
                current_chunk = ""
                current_words = 0

                for clause in clauses:
                    clause = clause.strip()
                    if not clause:
                        continue

                    clause_words = len(clause.split())

                    if current_words + clause_words <= self._max_words:
                        if current_chunk:
                            current_chunk += ", " + clause
                        else:
                            current_chunk = clause
                        current_words += clause_words
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = clause
                        current_words = clause_words

                if current_chunk:
                    chunks.append(current_chunk)

        return chunks

    def chunk_for_streaming(self, text: str) -> List[str]:
        """Divide texto para streaming (chunks menores, mais frequentes).

        Usa max_words // 2 para latência menor no playback progressivo.
        """
        original_max = self._max_words
        self._max_words = max(5, original_max // 2)
        chunks = self.chunk(text)
        self._max_words = original_max
        return chunks

    def estimate_duration_ms(self, text: str) -> int:
        """Estima duração em milissegundos do áudio.

        Base: ~150 palavras por minuto para pt-BR (velocidade natural).
        """
        words = len(text.split())
        # 150 palavras/min = 2.5 palavras/seg
        seconds = words / 2.5
        return int(seconds * 1000)
