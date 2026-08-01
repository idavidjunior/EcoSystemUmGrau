"""Teste do Silero VAD streaming. Fale; mostra quando detecta inicio/fim de fala.
Uso: python _vad_test.py
"""
import sys
from pathlib import Path

import numpy as np
import sounddevice as sd

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import dialogo

SAMPLE_RATE = 16000


def main():
    sess, ok = dialogo._carregar_silero()
    if not ok:
        print("Silero indisponivel")
        return
    vad = dialogo.VadSileroStream(threshold=0.5, min_silence_ms=800)
    print("Escutando (512 samples/32ms)... fale e depois fique em silencio. Ctrl+C para sair.")
    in_speech = False
    while True:
        rec = sd.rec(512, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        chunk = rec.flatten()
        turno = vad.push(chunk, sess)
        if vad.falando and not in_speech:
            in_speech = True
            print("[FALA detectada]", flush=True)
        if not vad.falando and in_speech:
            in_speech = False
            print("[silencio]", flush=True)
        if turno is not False:
            seg = len(turno) / SAMPLE_RATE
            print(f"[TURNO COMPLETO {seg:.2f}s] tamanho={len(turno)}", flush=True)
            texto, fonte = dialogo._stt_whisper(turno)
            print(f"[STT:{fonte}] {texto!r}", flush=True)
            vad.reset()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nFim.")
