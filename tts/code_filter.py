"""CodeFilter — detecta e filtra blocos de código, JSON, logs e conteúdo técnico.

Fornece métodos estáticos e de instância para identificar e tratar
conteúdo que não deve ser lido em voz alta.
"""
import re
from typing import Optional


class CodeFilter:
    """Filtra conteúdo técnico não falável.

    Uso:
        cf = CodeFilter()
        texto_limpo = cf.remove_code_blocks(texto)
        if cf.has_code(texto):
            # tratar...
    """

    # ── Padrões de detecção ────────────────────────────────────────────

    # Blocos de código
    CODE_BLOCK = re.compile(r'```[\s\S]*?```', re.DOTALL)
    CODE_INLINE = re.compile(r'`[^`]+`')

    # JSON
    JSON_OBJECT = re.compile(
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', re.DOTALL
    )
    JSON_ARRAY = re.compile(
        r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', re.DOTALL
    )

    # XML/HTML
    XML_TAG = re.compile(r'<[^>]+>', re.DOTALL)

    # Tracebacks e logs
    TRACEBACK = re.compile(
        r'(?:Traceback \(most recent call last\):|'
        r'File "[^"]+", line \d+|'
        r'(?:raise|except)\s+\w+|'
        r'(?:ERROR|WARNING|CRITICAL|INFO|DEBUG)\s*[:|])',
        re.IGNORECASE
    )

    # URLs (para não ler o endereço)
    URL = re.compile(
        r'https?://[^\s<>)\]"]+|ftp://[^\s<>)\]"]+|www\.[^\s<>)\]"]+',
        re.IGNORECASE
    )

    # Paths de arquivo Windows/Linux
    FILE_PATH = re.compile(
        r'[A-Za-z]:\\[\w\\. ]+|/[\w/. ]+',
    )

    # ── Métodos públicos ────────────────────────────────────────────────

    @staticmethod
    def has_code(text: str) -> bool:
        """Verifica se o texto contém blocos de código."""
        return bool(CodeFilter.CODE_BLOCK.search(text) or
                    CodeFilter.CODE_INLINE.search(text))

    @staticmethod
    def has_json(text: str) -> bool:
        """Verifica se o texto contém JSON."""
        return bool(CodeFilter.JSON_OBJECT.search(text) or
                    CodeFilter.JSON_ARRAY.search(text))

    @staticmethod
    def has_traceback(text: str) -> bool:
        """Verifica se o texto contém tracebacks/logs."""
        return bool(CodeFilter.TRACEBACK.search(text))

    @staticmethod
    def has_urls(text: str) -> bool:
        """Verifica se o texto contém URLs."""
        return bool(CodeFilter.URL.search(text))

    def remove_code_blocks(self, text: str) -> str:
        """Remove blocos de código e substitui por placeholder."""
        return self.CODE_BLOCK.sub(' trecho de código ', text)

    def remove_inline_code(self, text: str) -> str:
        """Remove código inline e mantém o conteúdo."""
        return self.CODE_INLINE.sub('', text)

    def remove_json(self, text: str) -> str:
        """Remove blocos JSON."""
        text = self.JSON_OBJECT.sub(' trecho de código ', text)
        text = self.JSON_ARRAY.sub(' trecho de código ', text)
        return text

    def remove_xml(self, text: str) -> str:
        """Remove tags XML/HTML."""
        return self.XML_TAG.sub(' ', text)

    def remove_urls(self, text: str) -> str:
        """Remove URLs e substitui por placeholder."""
        return self.URL.sub(' link ', text)

    def remove_file_paths(self, text: str) -> str:
        """Remove paths de arquivo."""
        return self.FILE_PATH.sub(' arquivo ', text)

    def remove_tracebacks(self, text: str) -> str:
        """Remove tracebacks e logs."""
        return self.TRACEBACK.sub(' erro de sistema ', text)

    def filter_all(self, text: str) -> str:
        """Aplica todos os filtros de código de uma vez."""
        text = self.remove_code_blocks(text)
        text = self.remove_json(text)
        text = self.remove_xml(text)
        text = self.remove_urls(text)
        text = self.remove_file_paths(text)
        text = self.remove_tracebacks(text)
        text = self.remove_inline_code(text)
        return text

    def get_summary(self, text: str) -> str:
        """Retorna um resumo do que foi detectado (para debug/logging)."""
        detections = []
        if self.has_code(text):
            detections.append("código")
        if self.has_json(text):
            detections.append("JSON")
        if self.has_traceback(text):
            detections.append("traceback/log")
        if self.has_urls(text):
            detections.append("URLs")
        return ", ".join(detections) if detections else "nenhum conteúdo técnico"
