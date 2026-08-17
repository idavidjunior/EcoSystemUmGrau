"""MarkdownCleaner — remove formatação markdown e preserva texto puro.

Trabalha sobre texto já classificado/extraído. Foca em limpar resíduos
de markdown que possam ter passado pelo ContentExtractor.
"""
import re
import unicodedata


class MarkdownCleaner:
    """Remove formatação markdown, emojis e símbolos especiais.

    Uso:
        cleaner = MarkdownCleaner()
        texto_limpo = cleaner.clean(texto)
    """

    # Padrões de limpeza (ordem importa)
    _CLEAN_PATTERNS = [
        # Headers residuais
        (re.compile(r'^#{1,6}\s+', re.MULTILINE), ''),
        # Bold/italic/strikethrough
        (re.compile(r'(\*\*|__|~~|[*_])'), ''),
        # Blockquotes
        (re.compile(r'^>\s+', re.MULTILINE), ''),
        # Horizontal rules
        (re.compile(r'^[-*_]{3,}\s*$', re.MULTILINE), ''),
        # Code blocks residuais (já removidos pelo classifier, mas por segurança)
        (re.compile(r'```[\s\S]*?```', re.DOTALL), ' '),
        # Inline code residual
        (re.compile(r'`([^`]+)`'), r'\1'),
        # Links residuais
        (re.compile(r'\[([^\]]+)\]\([^)]+\)'), r'\1'),
        # Imagens residuais
        (re.compile(r'!\[([^\]]*)\]\([^)]+\)'), ''),
    ]

    # Caracteres de controle e símbolos a remover
    _REMOVE_CATEGORIES = frozenset(["Cc", "Cf", "Cs", "Co", "Mn"])

    # Emojis
    _EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u200d\u2640-\u2642\u2600-\u2B55\u23cf\u23e9\u231a\ufe0f\u3030"
        "]+",
        flags=re.UNICODE
    )

    def clean(self, text: str) -> str:
        """Remove toda formatação markdown e retorna texto puro.

        Args:
            text: Texto com possível formatação markdown.

        Returns:
            Texto puro, sem markdown, emojis ou símbolos especiais.
        """
        if not text:
            return ""

        # Normaliza Unicode
        text = unicodedata.normalize("NFC", text)

        # Aplica padrões de limpeza
        for pattern, replacement in self._CLEAN_PATTERNS:
            text = pattern.sub(replacement, text)

        # Remove emojis
        text = self._EMOJI_PATTERN.sub('', text)

        # Remove caracteres de controle e símbolos
        text = self._remove_special_chars(text)

        # Normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _remove_special_chars(self, text: str) -> str:
        """Remove caracteres Unicode indesejados, preservando acentos e pontuação."""
        result = []
        for char in text:
            if char.isspace():
                result.append(' ')
            elif unicodedata.category(char) in self._REMOVE_CATEGORIES:
                continue  # Remove
            elif unicodedata.category(char).startswith('S'):
                # Símbolos (S*) — remove exceto pontuação básica
                if char not in '.,;:!?-\'"':
                    continue
                result.append(char)
            else:
                result.append(char)
        return ''.join(result)

    def strip_markdown_formatting(self, text: str) -> str:
        """Remove apenas formatação markdown, sem remover emojis/símbolos.

        Útil quando queremos preservar a estrutura mas limpar a formatação.
        """
        if not text:
            return ""

        for pattern, replacement in self._CLEAN_PATTERNS:
            text = pattern.sub(replacement, text)

        text = re.sub(r'\s+', ' ', text)
        return text.strip()
