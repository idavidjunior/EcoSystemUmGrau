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
