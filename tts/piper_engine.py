"""PiperTTSEngine — adapter para o motor Piper TTS local.

Integração com piper-tts (pip install piper-tts).
Executa inteiramente no CPU, sem chave de API, suporta pt-BR.
Modelo baixado em scripts/piper_models/.
"""
import asyncio
import logging
import os
import struct
from pathlib import Path
from typing import AsyncGenerator

from .exceptions import TTSynthesisError

logger = logging.getLogger(__name__)

# Tenta importar piper-tts
try:
    from piper.voice import PiperVoice
    HAS_PIPER = True
except ImportError:
    HAS_PIPER = False
    logger.warning("piper-tts não instalado. pip install piper-tts")

# Caminho padrão dos modelos Piper no ecossistema
DEFAULT_PIPER_MODEL_DIR = Path(__file__).resolve().parent.parent / "scripts" / "piper_models"
DEFAULT_PIPER_VOICE = "pt_BR-faber-medium"


class PiperTTSEngine:
    """Adapter para o motor Piper TTS local (CPU-only, sem API key).

    Uso:
        engine = PiperTTSEngine()
        audio_bytes = await engine.synthesize("Olá, mundo!")
        # ou
        async for chunk in engine.stream("Olá, mundo!"):
            processar(chunk)
    """

    def __init__(
        self,
        model_path: str = None,
        voice: str = None,
    ):
        if not HAS_PIPER:
            raise TTSynthesisError("piper-tts não está instalado (pip install piper-tts)")
        self._voice_name = voice or DEFAULT_PIPER_VOICE
        self._model_path = model_path or str(
            DEFAULT_PIPER_MODEL_DIR / f"{self._voice_name}.onnx"
        )
        self._voice: PiperVoice = None
        self._sample_rate = 22050
        self._sample_width = 2  # int16
        self._sample_channels = 1

    def _get_voice(self) -> PiperVoice:
        """Retorna (ou cria) o PiperVoice, com lazy init."""
        if self._voice is None:
            if not os.path.exists(self._model_path):
                raise TTSynthesisError(
                    f"Modelo Piper não encontrado: {self._model_path}. "
                    f"Baixe com: python -m piper.download_voices {self._voice_name}"
                )
            logger.info(f"Carregando modelo Piper: {self._model_path}")
            self._voice = PiperVoice.load(self._model_path)
            self._sample_rate = self._voice.config.sample_rate
            logger.info(f"Modelo Piper carregado (sample_rate={self._sample_rate})")
        return self._voice

    async def synthesize(self, text: str) -> bytes:
        """Sintetiza texto em áudio PCM int16.

        Args:
            text: Texto limpo e validado.

        Returns:
            Bytes do áudio PCM int16 (raw, não MP3).

        Raises:
            TTSynthesisError: Se a síntese falhar.
        """
        if not text:
            return b""
        try:
            voice = self._get_voice()
            audio_bytes = b""
            async for chunk in self.stream(text):
                audio_bytes += chunk
            return audio_bytes
        except TTSynthesisError:
            raise
        except Exception as e:
            raise TTSynthesisError(f"Falha na síntese Piper TTS: {e}")

    def synthesize_sync(self, text: str) -> bytes:
        """Versão síncrona de synthesize (bloqueante)."""
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop is not None:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self.synthesize(text))
                    return future.result()
            else:
                return asyncio.run(self.synthesize(text))
        except Exception as e:
            raise TTSynthesisError(f"Falha síncrona Piper TTS: {e}")

    async def stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Gera chunks de áudio PCM int16 incrementalmente."""
        if not text:
            return
        try:
            voice = self._get_voice()
            gen = voice.synthesize(text)
            for chunk in gen:
                yield chunk.audio_int16_bytes
        except Exception as e:
            raise TTSynthesisError(f"Falha no streaming Piper TTS: {e}")

    async def stream_base64(self, text: str) -> AsyncGenerator[str, None]:
        """Gera chunks base64 incrementalmente."""
        import base64
        async for chunk in self.stream(text):
            yield base64.b64encode(chunk).decode()

    def save_sync(self, text: str, path: str) -> bool:
        """Sintetiza e salva em arquivo WAV.

        Returns:
            True se salvo com sucesso.
        """
        try:
            audio = self.synthesize_sync(text)
            if audio:
                self._save_wav(path, audio)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao salvar áudio Piper: {e}")
            return False

    def _save_wav(self, path: str, audio_bytes: bytes):
        """Salva bytes PCM int16 como arquivo WAV."""
        import wave
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(self._sample_channels)
            wf.setsampwidth(self._sample_width)
            wf.setframerate(self._sample_rate)
            wf.writeframes(audio_bytes)

    def _ensure_wav(self, path: str, audio_bytes: bytes) -> str:
        """Converte WAV para MP3 se necessário (via ffmpeg),
        retornando o caminho do arquivo de áudio."""
        if not path.endswith('.wav'):
            wav_path = path.rsplit('.', 1)[0] + '.wav'
        else:
            wav_path = path
        self._save_wav(wav_path, audio_bytes)
        return wav_path

    @property
    def voice(self) -> str:
        return self._voice_name

    @property
    def available(self) -> bool:
        return HAS_PIPER and os.path.exists(self._model_path)