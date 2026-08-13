"""Teste de cache SpeechPipeline."""
import time, hashlib, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from tts import SpeechPipeline
from pathlib import Path
import tempfile

p = SpeechPipeline()
TEXT = "Teste de velocidade do Jarvis"

# Verifica cache
cache_key = hashlib.md5(TEXT.encode("utf-8")).hexdigest()[:12]
cache_dir = Path("runtime/tts_cache")
cache_file = cache_dir / (cache_key + ".mp3")
print(f"Cache dir: {cache_dir.absolute()}")
print(f"Cache key: {cache_key}")
print(f"Cache exists: {cache_file.exists()}")

# Primeira vez
mp3_1 = Path(tempfile.gettempdir()) / "test1.mp3"
t0 = time.time()
p.save(TEXT, str(mp3_1))
t1 = time.time()
print(f"Primeira vez: {t1-t0:.2f}s")

# Segunda vez
mp3_2 = Path(tempfile.gettempdir()) / "test2.mp3"
t2 = time.time()
p.save(TEXT, str(mp3_2))
t3 = time.time()
print(f"Segunda vez: {t3-t2:.2f}s")

if t1 - t0 > 0:
    print(f"Reducao: {(1 - (t3-t2)/(t1-t0))*100:.0f}%")
else:
    print("Primeira vez muito rapida para calcular")
