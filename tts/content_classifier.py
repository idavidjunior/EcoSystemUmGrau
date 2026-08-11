"""ContentClassifier — classifica porções do texto por tipo.

O primeiro passo do pipeline: identificar o que é código, markdown,
URL, JSON, etc. para que o ContentExtractor possa tratar cada tipo
adequadamente.
"""
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class ContentType(Enum):
    TEXT = auto()        # Texto corrido normal
    CODE_BLOCK = auto()  # Bloco de código (```)
    CODE_INLINE = auto() # Código inline (`code`)
    MARKDOWN = auto()    # Formatação markdown (##, **, etc.)
    URL = auto()         # URLs (http/https/ftp)
    JSON = auto()        # Blocos JSON
    XML = auto()         # Blocos XML/HTML
    LOG = auto()         # Logs, tracebacks, stacktraces
    TABLE = auto()       # Tabelas markdown
    LIST_ITEM = auto()   # Itens de lista (-, *, 1.)
    HEADER = auto()      # Cabeçalhos (#, ##, ###)
    IMAGE_REF = auto()   # Referências de imagem ![alt](url)
    LINK = auto()        # Links [text](url)
    EMOJI = auto()       # Emojis e símbolos especiais
    WHITESPACE = auto()  # Espaços, quebras de linha
    SPECIAL = auto()     # Caracteres especiais, símbolos


@dataclass
class ClassifiedSegment:
    """Um segmento classificado do texto."""
    content_type: ContentType
    text: str
    start: int
    end: int
    should_speak: bool  # Se deve ser lido em voz alta
    replacement: str = ""  # Substituição para fala (se aplicável)


class ContentClassifier:
    """Classifica segmentos de texto por tipo e determina se devem ser falados.

    Uso:
        classifier = ContentClassifier()
        segments = classifier.classify(texto_completo)
        # segments é uma lista de ClassifiedSegment
    """

    # Padrões regex compilados (ordem importa — mais específicos primeiro)
    _PATTERNS = [
        # Blocos de código (```...```)
        (ContentType.CODE_BLOCK, re.compile(r'```[\s\S]*?```', re.DOTALL), False),
        # JSON (objetos ou arrays complexos)
        (ContentType.JSON, re.compile(
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',
            re.DOTALL
        ), False),
        # XML/HTML tags
        (ContentType.XML, re.compile(r'<[^>]+>', re.DOTALL), False),
        # URLs
        (ContentType.URL, re.compile(
            r'https?://[^\s<>)\]"]+|ftp://[^\s<>)\]"]+|www\.[^\s<>)\]"]+',
            re.IGNORECASE
        ), False),
        # Imagens markdown ![alt](url)
        (ContentType.IMAGE_REF, re.compile(r'!\[([^\]]*)\]\([^)]+\)'), False),
        # Links markdown [text](url)
        (ContentType.LINK, re.compile(r'\[([^\]]+)\]\([^)]+\)'), True),
        # Código inline `code`
        (ContentType.CODE_INLINE, re.compile(r'`[^`]+`'), False),
        # Headers markdown (# Header)
        (ContentType.HEADER, re.compile(r'^#{1,6}\s+.+$', re.MULTILINE), True),
        # Tabelas markdown
        (ContentType.TABLE, re.compile(r'^\|.*\|$', re.MULTILINE), False),
        # List items
        (ContentType.LIST_ITEM, re.compile(r'^\s*[-*+]\s+.+$', re.MULTILINE), True),
        (ContentType.LIST_ITEM, re.compile(r'^\s*\d+[.)]\s+.+$', re.MULTILINE), True),
        # Bold/italic markers
        (ContentType.MARKDOWN, re.compile(r'(\*\*|__|~~|[*_])'), False),
        # Log patterns (traceback, ERROR, WARNING, etc.)
        (ContentType.LOG, re.compile(
            r'(?:Traceback|Error|Exception|File "|raise |except )',
            re.IGNORECASE
        ), False),
    ]

    # Emojis comuns e faixas Unicode
    _EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u200d\u2640-\u2642\u2600-\u2B55\u23cf\u23e9\u231a\ufe0f\u3030"
        "]+",
        flags=re.UNICODE
    )

    def classify(self, text: str) -> List[ClassifiedSegment]:
        """Classifica o texto completo em segmentos tipados.

        Retorna lista ordenada por posição no texto original.
        Segmentos se sobrepondo são resolvidos mantendo o primeiro match.
        """
        if not text:
            return []

        # Coleta todos os matches
        raw_matches = []
        for content_type, pattern, should_speak in self._PATTERNS:
            for match in pattern.finditer(text):
                raw_matches.append((
                    content_type, match.start(), match.end(),
                    match.group(), should_speak
                ))

        # Adiciona emojis
        for match in self._EMOJI_PATTERN.finditer(text):
            raw_matches.append((
                ContentType.EMOJI, match.start(), match.end(),
                match.group(), False
            ))

        # Ordena por posição; em caso de empate, o mais específico vem primeiro
        raw_matches.sort(key=lambda x: (x[1], -(x[2] - x[1])))

        # Resolve sobreposições: mantém o primeiro de cada região
        segments = []
        last_end = 0
        for content_type, start, end, matched_text, should_speak in raw_matches:
            if start < last_end:
                continue  # Sobreposto, pula

            # Texto normal antes deste match
            if start > last_end:
                normal_text = text[last_end:start]
                segments.append(ClassifiedSegment(
                    content_type=ContentType.TEXT,
                    text=normal_text,
                    start=last_end,
                    end=start,
                    should_speak=True,
                ))

            # O match em si
            replacement = ""
            if content_type == ContentType.LINK:
                # Para links, fala apenas o texto visível, não a URL
                link_match = re.match(r'\[([^\]]+)\]\([^)]+\)', matched_text)
                replacement = link_match.group(1) if link_match else ""
                should_speak = True
            elif content_type == ContentType.HEADER:
                # Headers: fala o texto sem os #
                replacement = re.sub(r'^#{1,6}\s+', '', matched_text)
                should_speak = True
            elif content_type == ContentType.LIST_ITEM:
                # List items: fala o texto sem o marcador
                replacement = re.sub(r'^\s*[-*+]\s+', '', matched_text)
                replacement = re.sub(r'^\s*\d+[.)]\s+', '', replacement)
                should_speak = True

            segments.append(ClassifiedSegment(
                content_type=content_type,
                text=matched_text,
                start=start,
                end=end,
                should_speak=should_speak,
                replacement=replacement,
            ))
            last_end = end

        # Texto restante após o último match
        if last_end < len(text):
            segments.append(ClassifiedSegment(
                content_type=ContentType.TEXT,
                text=text[last_end:],
                start=last_end,
                end=len(text),
                should_speak=True,
            ))

        return segments

    def has_blocked_content(self, text: str) -> bool:
        """Verifica rapidamente se o texto contém conteúdo bloqueado."""
        for content_type, pattern, _ in self._PATTERNS:
            if content_type in (ContentType.CODE_BLOCK, ContentType.JSON,
                                ContentType.XML, ContentType.TABLE, ContentType.LOG):
                if pattern.search(text):
                    return True
        return False
