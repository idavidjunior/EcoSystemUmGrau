"""SpeechPipeline — orquestrador central do pipeline de fala.

Esta é a ÚNICA porta de entrada para geração de fala no ecossistema.
Nenhum consumidor (jarvis_bridge, vox_audio, narrador_desktop, dialogo)
deve ter lógica própria de limpeza/preparação de texto.

Fluxo:
    Texto Bruto
        ↓
    ContentClassifier (detecta tipos)
        ↓
    ContentExtractor (extrai texto falável)
        ↓
    MarkdownCleaner (remove formatação residual)
        ↓
    CodeFilter (filtra código/JSON/logs)
        ↓
    TextNormalizer (horas, datas, pontuação)
        ↓
    PronunciationEngine (substituições personalizadas)
        ↓
    SentenceChunker (divide em sentenças)
        ↓
    TTSValidator (valida antes de síntese)
        ↓
    EdgeTTSEngine (gera áudio)
        ↓
    Áudio (bytes ou base64)
"""
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Tuple, Union

from .config import MIN_TEXT_LENGTH
from .content_classifier import ContentClassifier
from .content_extractor import ContentExtractor
from .markdown_cleaner import MarkdownCleaner
from .code_filter import CodeFilter
from .text_normalizer import TextNormalizer
from .pronunciation import PronunciationEngine
from .sentence_chunker import SentenceChunker
from .tts_validator import TTSValidator
from .edge_tts_engine import EdgeTTSEngine
from .exceptions import (
    TextTooShortError,
    TTSynthesisError,
    SpeechPipelineError,
)

logger = logging.getLogger(__name__)


class SpeechPipeline:
    """Pipeline central de síntese de fala.

    Uso básico:
        pipeline = SpeechPipeline()
        audio = await pipeline.synthesize("Olá, mundo!")

    Uso com streaming:
        async for chunk in pipeline.stream("Olá, mundo!"):
            processar(chunk)

    Uso síncrono (para vox_audio, narrador):
        audio = pipeline.synthesize_sync("Olá, mundo!")
        pipeline.save("Olá, mundo!", "/tmp/fala.mp3")
    """

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        pron_path: Optional[Path] = None,
    ):
        """Inicializa o pipeline com componentes configuráveis.

        Args:
            voice: Voz do edge-tts (default: pt-BR-AntonioNeural).
            rate: Taxa de fala (default: +0%).
            pitch: Tom (default: +0Hz).
            pron_path: Caminho para pronuncias.json (default: auto).
        """
        # Componentes do pipeline
        self._classifier = ContentClassifier()
        self._extractor = ContentExtractor()
        self._cleaner = MarkdownCleaner()
        self._code_filter = CodeFilter()
        self._normalizer = TextNormalizer()
        self._pronunciation = PronunciationEngine(pron_path)
        self._chunker = SentenceChunker()
        self._validator = TTSValidator()

        # Motor TTS (lazy init)
        self._tts_engine: Optional[EdgeTTSEngine] = None
        self._voice = voice
        self._rate = rate
        self._pitch = pitch

    def _get_tts(self) -> EdgeTTSEngine:
        """Retorna (ou cria) o motor TTS."""
        if self._tts_engine is None:
            kwargs = {}
            if self._voice:
                kwargs['voice'] = self._voice
            if self._rate:
                kwargs['rate'] = self._rate
            if self._pitch:
                kwargs['pitch'] = self._pitch
            self._tts_engine = EdgeTTSEngine(**kwargs)
        return self._tts_engine

    # ── API Principal ───────────────────────────────────────────────────

    def prepare(self, text: str) -> Tuple[str, dict]:
        """Prepara o texto para TTS (pipeline completo de processamento).

        NÃO gera áudio — apenas processa o texto. Útil quando o consumidor
        quer ver o texto preparado antes de sintetizar.

        Args:
            text: Texto bruto da LLM.

        Returns:
            Tupla (texto_preparado, metadata) onde metadata contém
            informações sobre o que foi processado.
        """
        if not text:
            return "", {"skipped": True, "reason": "empty"}

        original_length = len(text)
        metadata = {
            "original_length": original_length,
            "had_code": self._code_filter.has_code(text),
            "had_urls": self._code_filter.has_urls(text),
            "had_json": self._code_filter.has_json(text),
            "had_traceback": self._code_filter.has_traceback(text),
        }

        # 1. Classificar
        segments = self._classifier.classify(text)
        metadata["segments"] = len(segments)

        # 2. Extrair texto falável
        texto = self._extractor.extract(segments)

        # 3. Limpar markdown residual
        texto = self._cleaner.clean(texto)

        # 4. Filtrar código residual
        texto = self._code_filter.filter_all(texto)

        # 5. Normalizar para fala
        texto = self._normalizer.normalize(texto)

        # 6. Aplicar pronúncias
        texto, pronunciado = self._pronunciation.apply(texto)
        metadata["pronunciation_applied"] = pronunciado

        # 7. Validar
        try:
            texto = self._validator.validate(texto)
            metadata["valid"] = True
        except TextTooShortError as e:
            metadata["valid"] = False
            metadata["error"] = str(e)
            return "", metadata

        metadata["final_length"] = len(texto)
        return texto, metadata

    async def synthesize(self, text: str) -> str:
        """Sintetiza texto em áudio (base64 MP3).

        Esta é a função principal do pipeline. Processa o texto
        e gera o áudio completo.

        Args:
            text: Texto bruto da LLM.

        Returns:
            String base64 do áudio MP3.

        Raises:
            TextTooShortError: Se texto muito curto após processamento.
            TTSynthesisError: Se síntese falhar.
        """
        texto, metadata = self.prepare(text)
        if not texto:
            raise TextTooShortError("Texto vazio após processamento")

        tts = self._get_tts()
        return await tts.synthesize_base64(texto)

    async def synthesize_bytes(self, text: str) -> bytes:
        """Sintetiza texto em áudio (bytes MP3)."""
        texto, metadata = self.prepare(text)
        if not texto:
            raise TextTooShortError("Texto vazio após processamento")

        tts = self._get_tts()
        return await tts.synthesize(texto)

    async def stream(self, text: str) -> AsyncGenerator[str, None]:
        """Gera chunks de áudio incrementalmente (streaming).

        Yields:
            Strings base64 de cada chunk MP3.
        """
        texto, metadata = self.prepare(text)
        if not texto:
            return

        tts = self._get_tts()
        async for chunk in tts.stream_base64(texto):
            yield chunk

    def synthesize_sync(self, text: str) -> str:
        """Versão síncrona de synthesize (bloqueante).

        Útil para contexts não-async (vox_audio.py, narrador_desktop.py).
        """
        texto, metadata = self.prepare(text)
        if not texto:
            raise TextTooShortError("Texto vazio após processamento")

        tts = self._get_tts()
        audio = tts.synthesize_sync(texto)
        import base64
        return base64.b64encode(audio).decode()

    def save(self, text: str, path: str) -> bool:
        """Sintetiza e salva em arquivo MP3. Com cache para baixa latência.

        Returns:
            True se salvo com sucesso.
        """
        # Cache: verifica se já tem áudio gerado para este texto
        import hashlib
        cache_key = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        from .config import TTS_DIR
        cache_dir = TTS_DIR.parent / "runtime" / "tts_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{cache_key}.mp3"
        
        if cache_file.exists():
            # Cache hit — copia direto (0ms latência de rede)
            import shutil
            shutil.copy2(str(cache_file), path)
            return True
        
        # Cache miss — gera áudio
        texto, metadata = self.prepare(text)
        if not texto:
            return False

        tts = self._get_tts()
        ok = tts.save_sync(texto, path)
        
        if ok:
            # Salva no cache para próximas vezes
            import shutil
            shutil.copy2(path, str(cache_file))
            # Limpa cache antigo (máx 50 arquivos)
            try:
                arquivos = sorted(cache_dir.glob("*.mp3"), key=lambda f: f.stat().st_atime)
                while len(arquivos) > 50:
                    arquivos.pop(0).unlink(missing_ok=True)
            except Exception:
                pass
        
        return ok

    def speak(self, text: str, block: bool = True) -> bool:
        """Sintetiza e toca o áudio (para uso local no PC). Com cache para baixa latência.

        Args:
            text: Texto a ser falado.
            block: Se True, bloqueia até terminar de falar.

        Returns:
            True se reproduziu com sucesso.
        """
        # Cache: verifica se já tem áudio gerado para este texto
        import hashlib
        cache_key = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        from .config import TTS_DIR
        cache_dir = TTS_DIR.parent / "runtime" / "tts_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{cache_key}.mp3"
        
        mp3_path = Path(tempfile.gettempdir()) / "speech_pipeline_fala.mp3"
        
        if cache_file.exists():
            # Cache hit — copia direto
            import shutil
            shutil.copy2(str(cache_file), str(mp3_path))
        else:
            # Cache miss — gera áudio
            texto, metadata = self.prepare(text)
            if not texto:
                return False

            tts = self._get_tts()
            audio = tts.synthesize_sync(texto)
            if not audio:
                return False

            with open(mp3_path, 'wb') as f:
                f.write(audio)
            
            # Salva no cache
            import shutil
            shutil.copy2(str(mp3_path), str(cache_file))
            # Limpa cache antigo
            try:
                arquivos = sorted(cache_dir.glob("*.mp3"), key=lambda f: f.stat().st_atime)
                while len(arquivos) > 50:
                    arquivos.pop(0).unlink(missing_ok=True)
            except Exception:
                pass

        mci = ctypes.windll.winmm.mciSendStringW
        alias = f"sp{int(time.time() * 1000)}"
        r = mci(f'open "{mp3_path}" type mpegvideo alias {alias}', None, 0, 0)
        if r != 0:
            return False

        mci(f'play {alias}', None, 0, 0)

        if block:
            buf = ctypes.create_unicode_buffer(128)
            mci(f'status {alias} length', buf, 128, 0)
            try:
                duracao_ms = int(buf.value)
            except ValueError:
                duracao_ms = 0
            time.sleep(duracao_ms / 1000 + 0.3 if duracao_ms > 0 else 1.0)

        try:
            mci(f'close {alias}', None, 0, 0)
        except Exception:
            pass

        return True

    # ── API de Pronúncia ────────────────────────────────────────────────

    def add_pronunciation(self, palavra: str, fala: str) -> bool:
        """Adiciona uma pronúncia ao dicionário."""
        return self._pronunciation.add_pronunciation(palavra, fala)

    def get_pronunciations(self) -> dict:
        """Retorna todas as pronúncias registradas."""
        return self._pronunciation.get_all()

    # ── API de Configuração ─────────────────────────────────────────────

    @property
    def voice(self) -> str:
        return self._get_tts().voice

    @voice.setter
    def voice(self, value: str):
        self._voice = value
        self._tts_engine = None  # Força recriação

    @property
    def rate(self) -> str:
        return self._get_tts().rate

    @rate.setter
    def rate(self, value: str):
        self._rate = value
        self._tts_engine = None

    @property
    def pitch(self) -> str:
        return self._get_tts().pitch

    @pitch.setter
    def pitch(self, value: str):
        self._pitch = value
        self._tts_engine = None


# ── Instância global (singleton) ──────────────────────────────────────

_default_pipeline: Optional[SpeechPipeline] = None


def get_pipeline() -> SpeechPipeline:
    """Retorna a instância padrão do pipeline (singleton)."""
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = SpeechPipeline()
    return _default_pipeline


def set_pipeline(pipeline: SpeechPipeline):
    """Define a instância padrão do pipeline."""
    global _default_pipeline
    _default_pipeline = pipeline
