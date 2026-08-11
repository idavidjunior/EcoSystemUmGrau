"""EdgeTTSEngine — adapter para o motor edge-tts.

Encapsula toda a comunicação com a API do Microsoft Edge TTS.
Fornece métodos síncronos e assíncronos para geração de áudio.
"""
import asyncio
import base64
import logging
from typing import AsyncGenerator, Optional

from .config import DEFAULT_VOICE, DEFAULT_RATE, DEFAULT_PITCH, TTS_TIMEOUT_SECONDS
from .exceptions import TTSynthesisError

logger = logging.getLogger(__name__)

# Tenta importar edge_tts
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    logger.warning("edge_tts não instalado. pip install edge-tts")


class EdgeTTSEngine:
    """Adapter para o motor Microsoft Edge TTS.

    Uso:
        engine = EdgeTTSEngine()
        audio_bytes = await engine.synthesize(texto)
        # ou
        async for chunk in engine.stream(texto):
            processar(chunk)
    """

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE,
        pitch: str = DEFAULT_PITCH,
    ):
        if not HAS_EDGE_TTS:
            raise TTSynthesisError("edge_tts não está instalado")
        self._voice = voice
        self._rate = rate
        self._pitch = pitch

    async def synthesize(self, text: str) -> bytes:
        """Sintetiza texto em áudio (bytes MP3).

        Args:
            text: Texto limpo e validado.

        Returns:
            Bytes do áudio MP3.

        Raises:
            TTSynthesisError: Se a síntese falhar.
        """
        if not text:
            return b""

        try:
            communicate = edge_tts.Communicate(
                text, self._voice, rate=self._rate, pitch=self._pitch
            )
            audio = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio += chunk["data"]
            return audio
        except Exception as e:
            raise TTSynthesisError(f"Falha na síntese TTS: {e}")

    async def synthesize_base64(self, text: str) -> str:
        """Sintetiza texto e retorna base64 do áudio.

        Args:
            text: Texto limpo e validado.

        Returns:
            String base64 do áudio MP3.
        """
        audio = await self.synthesize(text)
        return base64.b64encode(audio).decode()

    async def stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Gera chunks de áudio incrementalmente.

        Yields:
            Bytes de cada chunk MP3 (para streaming progressivo).
        """
        if not text:
            return

        try:
            communicate = edge_tts.Communicate(
                text, self._voice, rate=self._rate, pitch=self._pitch
            )
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            raise TTSynthesisError(f"Falha no streaming TTS: {e}")

    async def stream_base64(self, text: str) -> AsyncGenerator[str, None]:
        """Gera chunks base64 incrementalmente.

        Yields:
            Strings base64 de cada chunk MP3.
        """
        async for chunk in self.stream(text):
            yield base64.b64encode(chunk).decode()

    def synthesize_sync(self, text: str) -> bytes:
        """Versão síncrona de synthesize (bloqueante).

        Útil para contexts não-async (como vox_audio.py).
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Já estamos num event loop — usa run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run, self.synthesize(text)
                    )
                    return future.result(timeout=TTS_TIMEOUT_SECONDS)
            else:
                return loop.run_until_complete(self.synthesize(text))
        except Exception as e:
            raise TTSynthesisError(f"Falha síncrona TTS: {e}")

    def save_sync(self, text: str, path: str) -> bool:
        """Sintetiza e salva em arquivo MP3.

        Returns:
            True se salvo com sucesso.
        """
        try:
            audio = self.synthesize_sync(text)
            if audio:
                with open(path, 'wb') as f:
                    f.write(audio)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao salvar áudio: {e}")
            return False

    @property
    def voice(self) -> str:
        return self._voice

    @voice.setter
    def voice(self, value: str):
        self._voice = value

    @property
    def rate(self) -> str:
        return self._rate

    @rate.setter
    def rate(self, value: str):
        self._rate = value

    @property
    def pitch(self) -> str:
        return self._pitch

    @pitch.setter
    def pitch(self, value: str):
        self._pitch = value
