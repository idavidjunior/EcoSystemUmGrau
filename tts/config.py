"""Configurações centrais do Speech Pipeline.

Todas as constantes de TTS ficam aqui. Módulos importam de config,
nunca definem valores hardcoded.
"""
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
TTS_DIR = Path(__file__).resolve().parent
ECOSSISTEMA_DIR = TTS_DIR.parent
SCRIPTS_DIR = ECOSSISTEMA_DIR / "scripts"
PRON_PATH = SCRIPTS_DIR / "pronuncias.json"
GLOSSARIO_PATH = ECOSSISTEMA_DIR / "config" / "glossario_tecnico.json"

# ── EdgeTTS ────────────────────────────────────────────────────────────
DEFAULT_VOICE = "pt-BR-AntonioNeural"
DEFAULT_RATE = "+0%"
DEFAULT_PITCH = "+0Hz"

# ── Limites ────────────────────────────────────────────────────────────
MAX_TEXT_LENGTH = 2000
MIN_TEXT_LENGTH = 5
MAX_CHUNK_WORDS = 25
SENTENCE_PAUSE_MS = 300

# ── Normalização ───────────────────────────────────────────────────────
# Conectores que ganham vírgula antes (pausa natural)
CONECTORES_MEIO = [
    "mas", "porque", "pois", "então", "depois", "porém", "contudo",
    "quando", "enquanto", "por isso", "portanto", "além disso",
]
CONECTORES_INICIAIS = [
    "então", "portanto", "agora", "bom", "olha", "assim", "enfim",
    "porém", "contudo", "finalmente", "primeiro", "depois", "aliás",
    "provavelmente", "atualmente", "resumindo", "vamos",
]
RESPIRACAO = CONECTORES_MEIO + ["e", "ou"]

# ── Validação ──────────────────────────────────────────────────────────
# Caracteres que NUNCA devem aparecer no texto final para TTS
FORBIDDEN_CHARS = set('`*#<>{}[]|\\^~')

# Categorias Unicode a serem removidas (símbolos, controle)
REMOVE_UNICODE_CATEGORIES = frozenset(["Cc", "Cf", "Cs", "Co", "Mn"])

# ── Limites de segurança ──────────────────────────────────────────────
TTS_TIMEOUT_SECONDS = 30
MAX_RETRIES = 2

# ── TTS Text Normalizer V2 ─────────────────────────────────────────────
# Configuração centralizada da camada de normalização estrutural.
# Ativa/desativa regras sem espalhar flags pelo projeto.
TTS_NORMALIZER_ENABLED = True          # liga/desliga toda a camada
REMOVE_CODE_BLOCKS = True              # remove blocos ``` ... ```
REMOVE_CODE_INLINE = True              # remove código inline `...`
REMOVE_MARKDOWN = True                 # remove formatação markdown
REMOVE_METADATA = True                 # remove role/tool_call/system/etc.
NORMALIZE_LINKS = True                 # [texto](url) -> texto; URLs -> "o link"
NORMALIZE_FILE_PATHS = True            # caminhos -> nome do arquivo
NORMALIZE_EXTENSIONS = True            # .py -> "ponto p y", .json -> "ponto jason"
NORMALIZE_SYMBOLS = True               # >= == != etc. -> linguagem natural
NORMALIZE_EMOJIS = True                # emojis decorativos removidos
NORMALIZE_JSON = True                  # estruturas JSON não verbalizadas
NORMALIZE_XML = True                   # tags XML/HTML removidas (preserva texto)
NORMALIZE_TABLES = True                # tabelas markdown -> texto corrido
NORMALIZE_UNICODE = True               # remove zero-width/BOM/controle
EMOJI_MODE = "remove"                  # "remove" | "convert" (emojis de pasta/arquivo)
URL_MODE = "link"                      # "link" (fala "o link") | "site" | "remove"
TTS_NORMALIZER_DEBUG = False           # log de debug por etapa (nunca em prod)
