"""Speech Pipeline — pipeline central de síntese de fala do EcoSystemUmGrau.

Este pacote fornece uma arquitetura modular, determinística e testável
para conversão de texto em áudio (TTS).

Uso básico:
    from tts import SpeechPipeline

    pipeline = SpeechPipeline()
    audio = await pipeline.synthesize("Olá, mundo!")

    # Ou de forma síncrona:
    pipeline.save("Olá, mundo!", "/tmp/fala.mp3")

Componentes:
    - SpeechPipeline: orquestrador central
    - ContentClassifier: classifica tipos de conteúdo
    - ContentExtractor: extrai texto falável
    - MarkdownCleaner: remove formatação markdown
    - CodeFilter: filtra código/JSON/logs
    - TextNormalizer: normaliza para fala natural
    - PronunciationEngine: pronúncias personalizadas
    - SentenceChunker: divide em sentenças
    - TTSValidator: valida antes de síntese
    - EdgeTTSEngine: adapter para Microsoft Edge TTS
"""
from .speech_pipeline import SpeechPipeline, get_pipeline, set_pipeline
from .content_classifier import ContentClassifier, ContentType
from .content_extractor import ContentExtractor
from .markdown_cleaner import MarkdownCleaner
from .code_filter import CodeFilter
from .text_normalizer import TextNormalizer, TTSTextNormalizer, normalize_for_tts
from .pronunciation import PronunciationEngine
from .sentence_chunker import SentenceChunker
from .tts_validator import TTSValidator
from .edge_tts_engine import EdgeTTSEngine
from .numeros_por_extenso import numero_por_extenso, numero_feminino
from .config import (
    DEFAULT_VOICE,
    DEFAULT_RATE,
    DEFAULT_PITCH,
    MAX_TEXT_LENGTH,
    MIN_TEXT_LENGTH,
)
from .exceptions import (
    SpeechPipelineError,
    TextTooShortError,
    TextTooLongError,
    TTSynthesisError,
    ValidationError,
    ConfigurationError,
    ContentExtractionError,
)

__all__ = [
    # Pipeline principal
    "SpeechPipeline",
    "get_pipeline",
    "set_pipeline",
    # Componentes
    "ContentClassifier",
    "ContentType",
    "ContentExtractor",
    "MarkdownCleaner",
    "CodeFilter",
    "TextNormalizer",
    "TTSTextNormalizer",
    "normalize_for_tts",
    "PronunciationEngine",
    "SentenceChunker",
    "TTSValidator",
    "EdgeTTSEngine",
    # Números por extenso
    "numero_por_extenso",
    "numero_feminino",
    # Config
    "DEFAULT_VOICE",
    "DEFAULT_RATE",
    "DEFAULT_PITCH",
    "MAX_TEXT_LENGTH",
    "MIN_TEXT_LENGTH",
    # Exceções
    "SpeechPipelineError",
    "TextTooShortError",
    "TextTooLongError",
    "TTSynthesisError",
    "ValidationError",
    "ConfigurationError",
    "ContentExtractionError",
]

__version__ = "1.0.0"
