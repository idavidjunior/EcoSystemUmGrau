"""Teste de cache TTS: mede latência com e sem cache."""
import time, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from vox_audio import _falar, AUDIO_CACHE_DIR
import shutil

# Limpa cache
shutil.rmtree(AUDIO_CACHE_DIR, ignore_errors=True)
AUDIO_CACHE_DIR.mkdir(exist_ok=True)

TEXT = "Entendido. Vou processar isso agora."

# Primeira vez (sem cache)
t0 = time.time()
_falar(TEXT)
t1 = time.time()
print(f"Primeira vez (gera TTS): {t1-t0:.2f}s")

# Segunda vez (com cache)
t2 = time.time()
_falar(TEXT)
t3 = time.time()
print(f"Segunda vez (cache hit): {t3-t2:.2f}s")
print(f"Reducao: {(1 - (t3-t2)/(t1-t0))*100:.0f}%")
