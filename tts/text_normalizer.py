"""TextNormalizer — normaliza texto para fala natural em pt-BR.

V2 (Text-to-Speech Text Normalizer):
- Camada independente que transforma TEXTO DA IA -> TEXTO DESTINADO À VOZ.
- Orquestra os componentes existentes (CodeFilter, MarkdownCleaner,
  TextNormalizer de pontuação) e adiciona regras estruturais que faltavam:
  metadados, caminhos, extensões, símbolos técnicos, emojis, JSON/XML,
  tabelas, caracteres Unicode invisíveis.
- Idempotente: normalize(normalize(t)) == normalize(t) na prática.
- Nunca altera a resposta original: recebe str, devolve nova str.
- Nunca retorna None. Segura para Unicode. Não lança por caracteres inesperados.

Fluxo (ordem recomendada pela spec):
    validação de entrada
    -> remoção de metadados internos
    -> remoção de blocos de código
    -> remoção de código inline
    -> remoção/transformação de Markdown
    -> tratamento de links e URLs
    -> tratamento de caminhos
    -> tratamento de extensões
    -> tratamento de símbolos técnicos
    -> tratamento de emojis
    -> normalização de caracteres Unicode
    -> normalização de espaços
    -> normalização de pontuação (delega ao TextNormalizer clássico)
    -> validação final
"""
import os
import re
import unicodedata
from typing import List

from .config import (
    CONECTORES_INICIAIS,
    CONECTORES_MEIO,
    RESPIRACAO,
    TTS_NORMALIZER_ENABLED,
    REMOVE_CODE_BLOCKS,
    REMOVE_CODE_INLINE,
    REMOVE_MARKDOWN,
    REMOVE_METADATA,
    NORMALIZE_LINKS,
    NORMALIZE_FILE_PATHS,
    NORMALIZE_EXTENSIONS,
    NORMALIZE_SYMBOLS,
    NORMALIZE_EMOJIS,
    NORMALIZE_JSON,
    NORMALIZE_XML,
    NORMALIZE_TABLES,
    NORMALIZE_UNICODE,
    EMOJI_MODE,
    URL_MODE,
    TTS_NORMALIZER_DEBUG,
)
from .code_filter import CodeFilter
from .markdown_cleaner import MarkdownCleaner
from .numeros_por_extenso import numero_feminino, numero_por_extenso


# ── Dicionário de pronúncia de extensões ──────────────────────────────
# Usado quando NORMALIZE_EXTENSIONS está ativo. Não duplica o pronuncias.json:
# este mapeamento é ESTRUTURAL (extensões de arquivo), o pronuncias.json
# continua sendo o dicionário de pronúncia de palavras/termos.
EXTENSAO_FALA = {
    "py": "p y",
    "js": "j s",
    "ts": "t s",
    "json": "jason",
    "xml": "x m l",
    "html": "html",
    "htm": "html",
    "css": "c s s",
    "md": "m d",
    "markdown": "m d",
    "txt": "texto",
    "exe": "executável",
    "apk": "apk",
    "zip": "zip",
    "rar": "rar",
    "tar": "tar",
    "gz": "g z",
    "pdf": "p d f",
    "docx": "dócuuê x",
    "doc": "dócuuê",
    "xlsx": "excel",
    "xls": "excel",
    "csv": "c s v",
    "png": "p n g",
    "jpg": "jota p g",
    "jpeg": "jota p e g",
    "gif": "gif",
    "svg": "s v g",
    "bmp": "b m p",
    "webp": "uéb p",
    "mp3": "m p três",
    "mp4": "m p quatro",
    "wav": "uave",
    "ogg": "ogue",
    "java": "java",
    "kt": "k t",
    "kotlin": "kotlin",
    "sql": "s q l",
    "sh": "sh",
    "bat": "b a t",
    "ps1": "p o u e r xé e l",
    "yml": "y a m l",
    "yaml": "y a m l",
    "toml": "tom l",
    "ini": "i n i",
    "cfg": "c f g",
    "conf": "conf",
    "log": "log",
    "db": "d b",
    "sqlite": "s q lite",
    "cpp": "c p p",
    "c": "c",
    "h": "h",
    "cs": "c sharp",
    "go": "gó",
    "rs": "r s",
    "rb": "r b",
    "php": "p h p",
    "swift": "suíft",
}

# Extensões que, quando encontradas em caminho, geram leitura por extensão.
# Captura palavra inteira + extensão: "config.json" -> nome="config", ext="json".
_EXTENSAO_PATTERN = re.compile(r'\b([\w.-]+)\.([A-Za-z0-9]{1,6})\b')

# Datas (dd/mm, dd/mm/yyyy ou dd/mm/yy) e horas hh:mm — protegidos na camada
# V2 contra a remoção de '/' e a expansão numérica prematura.
_RE_DATA = re.compile(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b')
_RE_HORA = re.compile(r'\b(\d{1,2}):(\d{2})\b')
# Decimais/milhares (1.234, 2.5, 12,5) — preservados contra expansão e contra
# inserção de espaço após pontuação no componente clássico. Só continua com
# pares separador+dígitos, para não engolir pontuação final (ex.: "45,90.").
_RE_DECIMAL = re.compile(r'\d+[.,]\d+(?:[.,]\d+)*')


# ── Símbolos técnicos -> linguagem natural (contextuais) ──────────────
_SYMBOL_REPLACEMENTS = [
    # Operadores de comparação (contexto: entre números/variáveis simples)
    (re.compile(r'\s*>=\s*'), ' maior ou igual a '),
    (re.compile(r'\s*<=\s*'), ' menor ou igual a '),
    (re.compile(r'\s*===\s*'), ' é estritamente igual a '),
    (re.compile(r'\s*==\s*'), ' é igual a '),
    (re.compile(r'\s*!==\s*'), ' é diferente de '),
    (re.compile(r'\s*!=\s*'), ' é diferente de '),
    (re.compile(r'\s*<>\s*'), ' é diferente de '),
    (re.compile(r'\s*&&\s*'), ' e '),
    (re.compile(r'\s*\|\|\s*'), ' ou '),
    (re.compile(r'\s*->\s*'), ' aponta para '),
    (re.compile(r'\s*=>\s*'), ' resulta em '),
    (re.compile(r'\s*\+\+\s*'), ' '),
    (re.compile(r'\s*--\s*'), ' '),
    # Símbolos soltos que NUNCA devem ser lidos literalmente
    (re.compile(r'[{}()\[\]]'), ' '),
    (re.compile(r'[\\/]'), ' '),
    (re.compile(r'[|]'), ' '),
    (re.compile(r'[_~^]'), ' '),
    (re.compile(r'[*+#]'), ' '),
    (re.compile(r'@'), ' '),
]


class TTSTextNormalizer:
    """Camada de normalização estrutural de texto para TTS (V2).

    Responsável por transformar a resposta da IA em texto natural para voz,
    removendo código, markdown, metadados, símbolos, emojis, caminhos, URLs,
    JSON/XML e caracteres invisíveis — SEM alterar a resposta original.

    Uso:
        normalizer = TTSTextNormalizer()
        texto_limpo = normalizer.normalize(resposta_ia)

    Ou via função de conveniência:
        from tts.text_normalizer import normalize_for_tts
        texto_limpo = normalize_for_tts(resposta_ia)
    """

    def __init__(self, config: dict = None):
        """Inicializa a camada de normalização V2.

        Args:
            config: dict opcional que sobrescreve flags de tts/config.py.
        """
        self._cfg = dict(
            enabled=TTS_NORMALIZER_ENABLED,
            remove_code_blocks=REMOVE_CODE_BLOCKS,
            remove_code_inline=REMOVE_CODE_INLINE,
            remove_markdown=REMOVE_MARKDOWN,
            remove_metadata=REMOVE_METADATA,
            normalize_links=NORMALIZE_LINKS,
            normalize_file_paths=NORMALIZE_FILE_PATHS,
            normalize_extensions=NORMALIZE_EXTENSIONS,
            normalize_symbols=NORMALIZE_SYMBOLS,
            normalize_emojis=NORMALIZE_EMOJIS,
            normalize_json=NORMALIZE_JSON,
            normalize_xml=NORMALIZE_XML,
            normalize_tables=NORMALIZE_TABLES,
            normalize_unicode=NORMALIZE_UNICODE,
            emoji_mode=EMOJI_MODE,
            url_mode=URL_MODE,
            debug=TTS_NORMALIZER_DEBUG,
        )
        if config:
            self._cfg.update(config)

        # Reutiliza componentes existentes (DRY — não duplica lógica)
        self._code_filter = CodeFilter()
        self._markdown_cleaner = MarkdownCleaner()
        self._punct_normalizer = _TextNormalizerClasico()
        self._sensitive = ([], [], [])

        # Debug log opcional (nunca em produção)
        if os.environ.get("TTS_NORMALIZER_DEBUG", "").lower() in ("1", "true", "sim"):
            self._cfg["debug"] = True

        # Padrões compilados uma vez (performance)
        self._re_code_block = re.compile(r'```[\s\S]*?```', re.DOTALL)
        self._re_code_inline = re.compile(r'`[^`]+`')
        self._re_fence_lang = re.compile(r'```[a-zA-Z0-9_+-]*\s*')
        self._re_header = re.compile(r'^#{1,6}\s+', re.MULTILINE)
        self._re_md_link = re.compile(r'\[([^\]]+)\]\([^)]+\)')
        self._re_image = re.compile(r'!\[([^\]]*)\]\([^)]+\)')
        self._re_table_sep = re.compile(r'^\s*\|?[\s:|-]+\|?\s*$', re.MULTILINE)
        self._re_table_row = re.compile(r'^\s*\|.*\|$', re.MULTILINE)
        self._re_bold = re.compile(r'(\*\*|__|~~|\*|_)')
        self._re_blockquote = re.compile(r'^>\s+', re.MULTILINE)
        self._re_list_marker = re.compile(r'^\s*[-*+]\s+', re.MULTILINE)
        self._re_list_marker_num = re.compile(r'^\s*\d+[.)]\s+', re.MULTILINE)
        self._re_url = re.compile(
            r'https?://[^\s<>)\]"\']+|ftp://[^\s<>)\]"\']+|www\.[^\s<>)\]"\']+',
            re.IGNORECASE,
        )
        self._re_win_path = re.compile(
            r'(?:[A-Za-z]:\\|\\)[^\s<>"\']+',
            re.IGNORECASE,
        )
        self._re_unix_path = re.compile(r'(?:/[\w.-]+)+')
        self._re_dot_path = re.compile(r'(?:\.\.?/)[\w./-]+')
        self._re_metadata_tag = re.compile(
            r'<[/]?(?:system|assistant|user|tool_call|function_call|'
            r'thinking|reasoning|metadata|content)[^>]*>',
            re.IGNORECASE,
        )
        self._re_role_marker = re.compile(
            r'^\s*(?:system|assistant|user|tool_call|function_call|role)\s*:\s*',
            re.IGNORECASE | re.MULTILINE,
        )
        # "role: assistant" no meio do texto (metadado de tool)
        self._re_role_inline = re.compile(
            r'\brole\s*:\s*(?:system|assistant|user|tool|function|content)\b',
            re.IGNORECASE,
        )
        self._re_attr = re.compile(
            r'\b(?:id|class|data-[\w-]+|role|href|src|style|alt)="[^"]*"',
            re.IGNORECASE,
        )
        self._re_zero_width = re.compile(
            '[\u200b\u200c\u200d\u2060\ufeff\u00ad\u200e\u200f]'
        )
        self._re_control = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
        self._re_spaces = re.compile(r'[ \t]+')
        self._re_blank_lines = re.compile(r'\n{3,}')

    # ── Debug ──────────────────────────────────────────────────────────

    def _debug(self, etapa: str, texto: str):
        if self._cfg.get("debug"):
            print(f"[TTS NORMALIZER] AFTER {etapa}:\n{texto}\n---")

    # ── API principal ──────────────────────────────────────────────────

    _data_holder_pat = re.compile(r'§DATA(\d+)§')
    _hora_holder_pat = re.compile(r'§HORA(\d+)§')
    _decimal_holder_pat = re.compile(r'§DEC([a-z])§')

    def _protect_sensitive(self, text: str) -> tuple:
        """Protege horas, datas e decimais contra destrutores e expansão.

        Horas/datas precisam de '/' e ':' até o clássico (que os converte por
        extenso); decimais/milhares precisam ser preservados em forma numérica
        (o texto RESTAURADO sai do clássico com espaço após '.'/',').
        """
        datas, horas, decimais = [], [], []
        t = text

        def _captura_data(m):
            datas.append(m.group(0))
            return f'§DATA{len(datas) - 1}§'

        def _captura_hora(m):
            horas.append(m.group(0))
            return f'§HORA{len(horas) - 1}§'

        def _captura_decimal(m):
            decimais.append(m.group(0))
            # Índice em letras (a=aª ocorrência) para o clássico não expandir o
            # dígito do placeholder como número.
            letra = chr(ord('a') + len(decimais) - 1)
            return f'§DEC{letra}§'

        t = _RE_DATA.sub(_captura_data, t)
        t = _RE_HORA.sub(_captura_hora, t)
        t = _RE_DECIMAL.sub(_captura_decimal, t)
        return t, (datas, horas, decimais)

    def _restore_sensitive(self, text: str) -> str:
        """Restaura datas/horas (§DATAi§/§HORAi§) para o componente clássico.

        Decimais (§DECi§) permanecem protegidos até depois do clássico para
        não ganharem espaço após separador.
        """
        if not text:
            return text
        datas, horas, _ = self._sensitive or ([], [], [])
        texto = text

        def _restaura_data(m):
            i = int(m.group(1))
            return datas[i] if i < len(datas) else m.group(0)

        def _restaura_hora(m):
            i = int(m.group(1))
            return horas[i] if i < len(horas) else m.group(0)

        texto = self._data_holder_pat.sub(_restaura_data, texto)
        texto = self._hora_holder_pat.sub(_restaura_hora, texto)
        return texto

    def _restore_decimals(self, text: str) -> str:
        """Restaura decimais/milhares (§DECa§, §DECb§…) após o clássico."""
        if not text:
            return text
        decimais = self._sensitive[2] if self._sensitive and len(self._sensitive) > 2 else []
        if not decimais:
            return text

        def _restaura_decimal(m):
            i = ord(m.group(1)) - ord('a')
            return decimais[i] if i < len(decimais) else m.group(0)

        return self._decimal_holder_pat.sub(_restaura_decimal, text)

    def normalize(self, text: str) -> str:
        """Normaliza texto completo da IA para TTS (determinístico).

        Args:
            text: Texto bruto (resposta da IA).

        Returns:
            str sempre. "" se entrada vazia.
        """
        # 1. Validação de entrada
        if not self._cfg.get("enabled"):
            return text if isinstance(text, str) else str(text or "")
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        if not text:
            return ""
        t = text

        # 1b. Protege horas/datas (dd/mm, hh:mm) contra destrutores de '/' e
        # de expansão numérica prematura. Restauradas antes do clássico.
        t, self._sensitive = self._protect_sensitive(t)
        self._debug("PROTECT", t)

        # 2. Remoção de metadados internos
        if self._cfg.get("remove_metadata"):
            t = self.remove_metadata(t)
            self._debug("METADATA", t)

        # 3. Blocos de código
        if self._cfg.get("remove_code_blocks"):
            t = self.remove_code_blocks(t)
            self._debug("CODE BLOCKS", t)

        # 4. Código inline
        if self._cfg.get("remove_code_inline"):
            t = self.remove_inline_code(t)
            self._debug("INLINE CODE", t)

        # 4b. JSON / XML (ANTES dos símbolos — estes removeriam {} e <> que
        # são usados para detectar as estruturas)
        if self._cfg.get("normalize_json"):
            t = self.remove_json(t)
        if self._cfg.get("normalize_xml"):
            t = self.remove_xml(t)
        self._debug("JSON/XML", t)

        # 5. Markdown
        if self._cfg.get("remove_markdown"):
            t = self.remove_markdown(t)
            self._debug("MARKDOWN", t)

        # 6. Tabelas
        if self._cfg.get("normalize_tables"):
            t = self.normalize_tables(t)
            self._debug("TABLES", t)

        # 7. Links e URLs
        if self._cfg.get("normalize_links"):
            t = self.normalize_links(t)
            self._debug("LINKS", t)

        # 8. Caminhos de arquivo
        if self._cfg.get("normalize_file_paths"):
            t = self.normalize_file_paths(t)
            self._debug("PATHS", t)

        # 9. Extensões
        if self._cfg.get("normalize_extensions"):
            t = self.normalize_extensions(t)
            self._debug("EXTENSIONS", t)

        # 10. Símbolos técnicos
        if self._cfg.get("normalize_symbols"):
            t = self.normalize_symbols(t)
            self._debug("SYMBOLS", t)

        # 11. Emojis
        if self._cfg.get("normalize_emojis"):
            t = self.normalize_emojis(t)
            self._debug("EMOJIS", t)

        # 12. Normalização Unicode
        if self._cfg.get("normalize_unicode"):
            t = self.normalize_unicode(t)
            self._debug("UNICODE", t)

        # 14. Espaços (colapso básico)
        t = self._re_spaces.sub(' ', t)
        t = self._re_blank_lines.sub('\n', t)

        # 15. Pontuação / respiração / horas / datas (componente clássico)
        t = self._restore_sensitive(t)
        t = self._punct_normalizer.normalize(t)
        self._debug("PUNCTUATION", t)

        # 15b. Decimais permanecem protegidos (§DECx§) para sobreviver à validação
        # final (que insere espaço após ','/'.'); restaurados no passo 16b.
        self._debug("DECIMALS", t)

        # 16. Validação final
        t = self._final_validation(t)
        self._debug("FINAL", t)

        # 16b. Restaura decimais/milhares (após a validação final, para que a
        # inserção de espaço após ',' / '.' não quebre 12,5 / 1.234)
        t = self._restore_decimals(t)
        self._debug("DECIMALS2", t)

        return t

    # ── Etapas individuais (públicas para teste/diagnóstico) ──────────

    def remove_metadata(self, text: str) -> str:
        """Remove metadados internos: tags <system>, role:, id="", etc."""
        t = text
        t = self._re_metadata_tag.sub(' ', t)
        t = self._re_role_marker.sub('', t)
        t = self._re_role_inline.sub(' ', t)
        t = self._re_attr.sub(' ', t)
        return t

    def remove_code_blocks(self, text: str) -> str:
        """Remove blocos de código (``` ... ```) preservando texto ao redor."""
        return self._re_code_block.sub(' ', text)

    def remove_inline_code(self, text: str) -> str:
        """Remove código inline `...`, mantendo o conteúdo (sem crase)."""
        def _keep(m):
            return m.group(1) if len(m.group(0)) >= 2 else m.group(1)
        # `code` -> code (remove apenas as crases)
        return self._re_code_inline.sub(lambda m: m.group(0)[1:-1], text)

    def remove_markdown(self, text: str) -> str:
        """Remove formatação markdown preservando texto humano."""
        t = text
        # Imagens ![alt](url) removidas
        t = self._re_image.sub('', t)
        # Links [texto](url) -> texto (já tratado em normalize_links, mas
        # como segurança quando links estiverem desativados)
        t = self._re_md_link.sub(r'\1', t)
        # Headers
        t = self._re_header.sub('', t)
        # Bold/italic/strikethrough
        t = self._re_bold.sub('', t)
        # Blockquotes
        t = self._re_blockquote.sub('', t)
        # Horizontal rules
        t = re.sub(r'^[-*_]{3,}\s*$', '', t, flags=re.MULTILINE)
        # List markers
        t = self._re_list_marker.sub('', t)
        t = self._re_list_marker_num.sub('', t)
        return t

    def normalize_tables(self, text: str) -> str:
        """Converte tabelas markdown em texto corrido.

        "| Nome | Status |\n|------|--------|\n| Jarvis | OK |"
        -> "Nome: Status. Jarvis, OK."
        """
        # Detecta blocos de tabela (linhas de separador entre |...|)
        linhas = text.split('\n')
        resultado = []
        in_table = False
        for linha in linhas:
            if self._re_table_sep.match(linha):
                in_table = True
                continue
            if self._re_table_row.match(linha):
                in_table = True
                # Extrai células
                celulas = [c.strip() for c in linha.strip().strip('|').split('|')]
                celulas = [c for c in celulas if c]
                # Ignora linha de separador (---)
                if all(re.match(r'^[\s:|-]+$', c) for c in celulas):
                    continue
                resultado.append(', '.join(celulas) + '.')
                continue
            if in_table and linha.strip():
                # Fim da tabela, texto normal
                resultado.append(linha)
                in_table = False
            else:
                resultado.append(linha)
        return '\n'.join(resultado)

    def normalize_links(self, text: str) -> str:
        """Trata links markdown e URLs.

        [documentação](https://exemplo.com) -> documentação
        https://exemplo.com/docs -> o link (URL_MODE="link")
        """
        t = text
        # Markdown links: mantém apenas o texto visível
        t = self._re_md_link.sub(r'\1', t)
        # URLs soltas
        modo = self._cfg.get("url_mode", "link")
        if modo == "link":
            t = self._re_url.sub(' o link ', t)
        elif modo == "site":
            t = self._re_url.sub(' o site ', t)
        else:  # remove
            t = self._re_url.sub(' ', t)
        return t

    def normalize_file_paths(self, text: str) -> str:
        """Converte caminhos de arquivo em referência natural.

        C:\\Users\\David\\Documents\\arquivo.py -> arquivo ponto p y
        ./src/main.py -> main ponto p y
        /home/user/projeto/main.py -> main ponto p y
        """
        t = text
        def _path_to_nome(m):
            caminho = m.group(0)
            nome = caminho.replace('\\', '/').rstrip('/').split('/')[-1]
            if not nome or nome == caminho:
                return ' '
            if self._cfg.get("normalize_extensions"):
                base, dot, ext = nome.rpartition('.')
                if dot and base:
                    fala = self._extensao_fala(ext)
                    return f' {base} ponto {fala} ' if fala else f' {base} '
            return f' {nome} '
        # Ordem: dot-path primeiro, depois Windows, depois Unix
        t = self._re_dot_path.sub(_path_to_nome, t)
        t = self._re_win_path.sub(_path_to_nome, t)
        t = self._re_unix_path.sub(_path_to_nome, t)
        return t

    def normalize_extensions(self, text: str) -> str:
        """Converte extensões de arquivo em leitura natural.

        config.json -> config ponto jason
        arquivo.py -> arquivo ponto p y
        """
        def _ext(m):
            nome = m.group(1)
            ext = m.group(2)
            if len(nome) < 2:
                return m.group(0)
            fala = self._extensao_fala(ext)
            if fala:
                return f'{nome} ponto {fala}'
            return f'{nome} ponto {ext}'
        # Só aplica a palavras com ponto (não a números decimais, nem URLs já tratadas)
        return _EXTENSAO_PATTERN.sub(_ext, text)

    def _extensao_fala(self, ext: str) -> str:
        """Retorna a pronúncia de uma extensão (ou a própria se desconhecida)."""
        key = ext.lower()
        if key in EXTENSAO_FALA:
            return EXTENSAO_FALA[key]
        return key

    def normalize_symbols(self, text: str) -> str:
        """Converte símbolos técnicos em linguagem natural (contextual)."""
        t = text
        for pattern, replacement in _SYMBOL_REPLACEMENTS:
            t = pattern.sub(replacement, t)
        return t

    def normalize_emojis(self, text: str) -> str:
        """Trata emojis. Modo "remove" remove; modo "convert" converte
        emojis de pasta/arquivo em palavras naturais."""
        t = text
        if self._cfg.get("emoji_mode") == "convert":
            t = t.replace('📁', ' pasta ').replace('📂', ' pasta ')
            t = t.replace('📄', ' arquivo ').replace('📝', ' nota ')
            t = t.replace('✅', ' ok ').replace('❌', ' ')
            t = t.replace('🚀', ' ').replace('🔥', ' ')
            t = t.replace('💡', ' ideia ').replace('🧠', ' ')
        # Remoção de emojis restantes (delega ao MarkdownCleaner)
        return self._markdown_cleaner._EMOJI_PATTERN.sub('', t)

    def remove_json(self, text: str) -> str:
        """Remove estruturas JSON remanescentes."""
        return self._code_filter.remove_json(text)

    def remove_xml(self, text: str) -> str:
        """Remove tags XML/HTML preservando texto humano."""
        t = self._code_filter.remove_xml(text)
        # Preserva texto entre tags: <p>Olá</p> -> Olá
        return self._re_spaces.sub(' ', t)

    def normalize_unicode(self, text: str) -> str:
        """Remove caracteres invisíveis e de controle, preservando acentos.

        - Zero-width, BOM, soft hyphen: removidos.
        - Newlines/tabs/controles: convertidos em espaço (nunca removidos,
          para não colar palavras).
        - Preserva acentos e letras (Ll/Lu/Nd/etc.).
        """
        t = text
        # Normaliza NFC (junta acentos combinados)
        t = unicodedata.normalize("NFC", t)
        # Remove zero-width, BOM, soft hyphen, etc.
        t = self._re_zero_width.sub('', t)
        # Newlines e CR -> espaço (para não colar palavras)
        t = t.replace('\r', ' ').replace('\n', ' ')
        # Outros controles -> espaço
        t = self._re_control.sub(' ', t)
        # Categorias especiais (símbolos não padrão) -> espaço quando não faláveis
        t = ''.join(
            c for c in t
            if unicodedata.category(c) not in ("Co", "Cs")
        )
        return t

    def _final_validation(self, text: str) -> str:
        """Limpeza e validação final do texto."""
        t = text.strip()
        # Colapsa múltiplos espaços em um
        t = self._re_spaces.sub(' ', t)
        # Remove pontuação dupla/vazia
        t = re.sub(r'\s+([,.;:!?])', r'\1', t)
        t = re.sub(r'([,.;:!?])(?=\S)', r'\1 ', t)
        t = re.sub(r',{2,}', ',', t)
        t = re.sub(r'\s{2,}', ' ', t)
        # Garante que não termina com marcador estrutural
        t = t.rstrip('`*#|~_-')
        return t.strip()


# ── TextNormalizer clássico (pontuação, horas, datas, respiração) ─────
# Extraído do TextNormalizer v1 para reuso na camada V2 sem duplicar regex.
class _TextNormalizerClasico:
    def __init__(self):
        self._respiracao_pattern = re.compile(
            r'(?<![,.;:!?])\s+(?:' +
            '|'.join(re.escape(c) for c in RESPIRACAO) +
            r')\s+',
            re.IGNORECASE
        )

    def normalize(self, text: str) -> str:
        if not text:
            return ""
        t = text.strip()
        t = re.sub(r'\s+', ' ', t)
        t = self._normalize_hours(t)
        t = self._normalize_dates(t)
        t = self._normalize_numbers(t)
        t = self._normalize_punctuation(t)
        t = self._insert_breathing(t)
        t = self._capitalize_sentences(t)
        t = self._ensure_final_punctuation(t)
        t = self._final_cleanup(t)
        return t

    def _normalize_hours(self, text: str) -> str:
        def _hora_falada(m):
            hora = int(m.group(1))
            minutos = int(m.group(2))
            palavra_hora = numero_feminino(hora)
            unidade_hora = "hora" if hora == 1 else "horas"
            if minutos == 0:
                return f"{palavra_hora} {unidade_hora} em ponto"
            return f"{palavra_hora} {unidade_hora} e {numero_por_extenso(minutos)}"
        text = re.sub(r'\b(\d{1,2}):(\d{2})\b', _hora_falada, text)
        return text

    def _normalize_dates(self, text: str) -> str:
        meses = {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto",
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
        }
        def _dia_por_extenso(dia: int) -> str:
            if dia == 1:
                return "primeiro"
            return numero_por_extenso(dia)
        def _ano_por_extenso(ano: str) -> str:
            return numero_por_extenso(int(ano))
        def _replace_date(m):
            dia = int(m.group(1))
            mes = int(m.group(2))
            ano = m.group(3)
            if mes in meses:
                resultado = f"{_dia_por_extenso(dia)} de {meses[mes]}"
                if ano:
                    resultado += f" de {_ano_por_extenso(ano)}"
                return resultado
            return m.group(0)
        text = re.sub(
            r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b',
            _replace_date,
            text
        )
        return text

    def _normalize_numbers(self, text: str) -> str:
        text = re.sub(
            r'(?<![.,])(\d{1,6})%',
            lambda m: f'{numero_por_extenso(int(m.group(1)))} por cento',
            text
        )
        # Expande inteiros soltos (1..999999) sem tocar decimais/separadores
        # (bloqueia precedência por '.'/',' — ex.: 1.234, 12,5)
        text = re.sub(
            r'(?<![\d.,])(\d{1,6})(?![\d,]|\.\d)',
            lambda m: numero_por_extenso(int(m.group(1))),
            text
        )
        return text

    def _normalize_punctuation(self, text: str) -> str:
        text = re.sub(r'\s*[—–]\s*', ', ', text)
        text = re.sub(r'\s+-\s+', ', ', text)
        text = text.replace(';', ',')
        text = text.replace(':', ',')
        text = re.sub(r'^[,;\s]+', '', text)
        text = re.sub(r'\s+([,.;:?!])', r'\1', text)
        text = re.sub(r'([,.;:?!])(?=\S)', r'\1 ', text)
        text = re.sub(r',{2,}', ',', text)
        text = re.sub(r'\.{3,}', '...', text)
        return text

    def _insert_breathing(self, text: str) -> str:
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
        matches = list(self._respiracao_pattern.finditer(sentence))
        if not matches:
            return sentence
        centro = len(sentence) // 2
        melhor = min(matches, key=lambda m: abs(m.start() - centro))
        return sentence[:melhor.start()].rstrip() + ', ' + sentence[melhor.start():].strip()

    def _capitalize_sentences(self, text: str) -> str:
        def _cap(m):
            return m.group(1) + m.group(2).upper()
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        text = re.sub(r'([.!?]\s+)(\w)', _cap, text)
        for c in CONECTORES_INICIAIS:
            text = re.sub(
                rf'^(?i:{re.escape(c)})\s+',
                f'{c.capitalize()}, ',
                text
            )
        return text

    def _ensure_final_punctuation(self, text: str) -> str:
        text = text.rstrip()
        if text and text[-1] not in '.!?...':
            text += '.'
        return text

    def _final_cleanup(self, text: str) -> str:
        text = re.sub(r'^,\s*', '', text)
        text = re.sub(r'^\.\s*', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(
            r'\b(e|ou)\s*,\s*(?=depois|então|porém|contudo|portanto|finalmente|enfim)\b',
            r'\1 ',
            text,
            flags=re.IGNORECASE
        )
        return text.strip()


class TextNormalizer:
    """Compat: TextNormalizer v1 mantido para quem importa diretamente.

    Delega para a camada V2 (pontuação, horas, datas, respiração).
    """

    def __init__(self):
        self._respiracao_pattern = re.compile(
            r'(?<![,.;:!?])\s+(?:' +
            '|'.join(re.escape(c) for c in RESPIRACAO) +
            r')\s+',
            re.IGNORECASE
        )

    def normalize(self, text: str) -> str:
        return _TextNormalizerClasico().normalize(text)

    def _normalize_hours(self, text: str) -> str:
        return _TextNormalizerClasico()._normalize_hours(text)

    def _normalize_dates(self, text: str) -> str:
        return _TextNormalizerClasico()._normalize_dates(text)

    def _normalize_numbers(self, text: str) -> str:
        return _TextNormalizerClasico()._normalize_numbers(text)

    def _normalize_punctuation(self, text: str) -> str:
        return _TextNormalizerClasico()._normalize_punctuation(text)

    def _insert_breathing(self, text: str) -> str:
        return _TextNormalizerClasico()._insert_breathing(text)

    def _add_breathing_point(self, sentence: str) -> str:
        return _TextNormalizerClasico()._add_breathing_point(sentence)

    def _capitalize_sentences(self, text: str) -> str:
        return _TextNormalizerClasico()._capitalize_sentences(text)

    def _ensure_final_punctuation(self, text: str) -> str:
        return _TextNormalizerClasico()._ensure_final_punctuation(text)

    def _final_cleanup(self, text: str) -> str:
        return _TextNormalizerClasico()._final_cleanup(text)


# ── Função de conveniência ─────────────────────────────────────────────

_normalizer_instance: TTSTextNormalizer = None


def normalize_for_tts(text: str, config: dict = None) -> str:
    """Normaliza texto da IA para TTS (função de conveniência).

    Reutiliza instância única para performance. Pode receber config
    opcional por chamada.

    Args:
        text: Texto bruto da IA.
        config: dict opcional para sobrescrever flags.

    Returns:
        str sempre. Nunca None.
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = TTSTextNormalizer(config)
    elif config:
        _normalizer_instance = TTSTextNormalizer(config)
    return _normalizer_instance.normalize(text)