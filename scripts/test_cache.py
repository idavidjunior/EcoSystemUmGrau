"""Teste de cache TTS: mede latência com e sem cache.

Executa sem dispositivo de áudio real — faz mock do playback MCI
e do SpeechPipeline para forçar o caminho edge-tts (único que preenche cache).
"""
import hashlib
import shutil
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vox_audio
from vox_audio import AUDIO_CACHE_DIR, _falar

# Limpa cache
shutil.rmtree(AUDIO_CACHE_DIR, ignore_errors=True)
AUDIO_CACHE_DIR.mkdir(exist_ok=True)

TEXT = "Entendido. Vou processar isso agora."
cache_key = hashlib.md5(TEXT.encode("utf-8")).hexdigest()[:12]
cache_file = AUDIO_CACHE_DIR / f"{cache_key}.mp3"


def _noop(*args, **kwargs):
    pass


with patch.object(vox_audio, "_tocar_mci", side_effect=_noop), \
     patch.object(vox_audio, "_tocar_e_limpar", side_effect=_noop), \
     patch.object(vox_audio, "_speech_pipeline") as mock_sp, \
     patch.object(vox_audio, "SPEECH_PIPELINE_AVAILABLE", True):

    # SpeechPipeline retorna False → força fallback edge-tts → preenche cache
    mock_sp.save.return_value = False

    # Primeira vez (gera TTS via edge-tts e salva no cache)
    t0 = time.time()
    _falar(TEXT)
    t1 = time.time()

    if not cache_file.exists():
        print("ERRO: arquivo de cache não foi criado")
        print("Verifique se edge-tts está instalado: pip install edge-tts")
        sys.exit(1)

    print(f"Primeira vez (gera TTS): {t1-t0:.2f}s")
    print(f"Cache criado: {cache_file.name} ({cache_file.stat().st_size} bytes)")

    # Segunda vez (cache hit — deve ser instantâneo)
    t2 = time.time()
    _falar(TEXT)
    t3 = time.time()

    delta_1 = t1 - t0
    delta_2 = t3 - t2
    reducao = (1 - delta_2 / delta_1) * 100 if delta_1 > 0 else 0

    print(f"Segunda vez (cache hit): {delta_2:.4f}s")
    print(f"Reducao: {reducao:.0f}%")

    if delta_2 < delta_1:
        print("OK: cache reduz latência")
    else:
        print("AVISO: cache não reduziu latência (pode ser normal em máquina rápida)")
