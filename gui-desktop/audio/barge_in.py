"""Barge-in detection — hear the user while Jarvis is speaking.

Runs a continuous microphone monitor (sounddevice InputStream callback) that
measures RMS amplitude. When speech above a threshold is sustained for
``min_speech_ms`` while the assistant is speaking, ``on_speech`` fires once
so the caller can stop playback and start listening.

The listener degrades gracefully: if sounddevice/PortAudio is unavailable the
methods are no-ops and :attr:`available` is False.

Reaproveitado de spidertje/jarvis-pyqt (MIT). Sem mudanças funcionais — o
RMS-based detector é compatível com o ecossistema; em desktop com
speaker+mic pode haver falsos positivos (decisão consciente).
"""

import logging
import time

logger = logging.getLogger(__name__)


class BargeInListener:
    def __init__(
        self,
        on_speech=None,
        threshold: float = 300.0,
        min_speech_ms: float = 250.0,
        sample_rate: int = 16000,
        blocksize: int = 512,
        device: int | None = None,
    ):
        self.on_speech = on_speech
        self.threshold = threshold
        self.min_speech_ms = min_speech_ms
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.device = device
        self._sd = None
        self._stream = None
        self._active = False
        self._speech_since: float | None = None
        try:
            import sounddevice as sd
            self._sd = sd
        except Exception as e:
            logger.warning(f"sounddevice unavailable — barge-in disabled: {e}")

    @property
    def available(self) -> bool:
        return self._sd is not None

    def set_active(self, active: bool) -> None:
        self._active = active
        self._speech_since = None

    def start(self) -> None:
        if not self.available or self._stream is not None:
            return
        try:
            kwargs = {
                "samplerate": self.sample_rate,
                "channels": 1,
                "dtype": "float32",
                "blocksize": self.blocksize,
                "callback": self._callback,
            }
            if self.device is not None:
                kwargs["device"] = self.device
            self._stream = self._sd.InputStream(**kwargs)
            self._stream.start()
            logger.info("Barge-in listener started")
        except Exception as e:
            logger.warning(f"Could not start barge-in listener: {e}")
            self._stream = None

    def stop(self) -> None:
        self._active = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _callback(self, indata, frames, time_info, status) -> None:
        if not self._active or not self.on_speech:
            return
        import numpy as np

        samples = np.frombuffer(indata[:, 0].tobytes(), dtype=np.float32).astype(np.float64)
        rms = float(np.sqrt(np.mean(samples ** 2))) * 32768.0
        now = time.monotonic()
        if rms >= self.threshold:
            if self._speech_since is None:
                self._speech_since = now
            elif (now - self._speech_since) * 1000.0 >= self.min_speech_ms:
                self._active = False
                self._speech_since = None
                logger.info(f"Barge-in: sustained speech detected (RMS={rms:.0f})")
                try:
                    self.on_speech()
                except Exception as e:
                    logger.error(f"Barge-in callback error: {e}")
        else:
            self._speech_since = None
