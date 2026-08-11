"""Teste isolado: MCI vs SpeechPipeline."""
import time, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from tts import SpeechPipeline
from vox_audio import _tocar_mci
from pathlib import Path
import tempfile

p = SpeechPipeline()
TEXT = "Teste de velocidade"

# Gera áudio
mp3 = Path(tempfile.gettempdir()) / "test_mci.mp3"
t0 = time.time()
p.save(TEXT, str(mp3))
t1 = time.time()
print(f"SpeechPipeline.save (com cache): {t1-t0:.2f}s")

# Toca via MCI
t2 = time.time()
_tocar_mci(str(mp3))
t3 = time.time()
print(f"MCI play: {t3-t2:.2f}s")
print(f"Total: {t3-t0:.2f}s")
