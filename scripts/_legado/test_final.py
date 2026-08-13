"""Teste de latência final: vox_audio com cache."""
import time, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from vox_audio import _falar, _tocar_mci, AUDIO_CACHE_DIR

TEXT = "Entendido. Vou processar isso agora."

# Limpa cache
import shutil
shutil.rmtree(AUDIO_CACHE_DIR, ignore_errors=True)
AUDIO_CACHE_DIR.mkdir(exist_ok=True)

# Primeira vez (gera TTS + salva cache)
t0 = time.time()
_falar(TEXT)
t1 = time.time()
print(f"Primeira vez (gera TTS): {t1-t0:.2f}s")

# Segunda vez (cache hit)
t2 = time.time()
_falar(TEXT)
t3 = time.time()
print(f"Segunda vez (cache hit): {t3-t2:.2f}s")
print(f"Reducao: {(1 - (t3-t2)/(t1-t0))*100:.0f}%")
