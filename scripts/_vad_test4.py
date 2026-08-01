import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import numpy as np
import dialogo
from vox_audio import _stt_whisper, _stt_google

audio = np.load(r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\_fala_gravada.npy")
model, ok = dialogo._carregar_silero()
vad = dialogo.VadSileroStream(model, threshold=0.5, min_silence_ms=800)

CHUNK = 512
turnos = []
buf = np.zeros(0, dtype="float32")
buf = np.concatenate([buf, audio])
while len(buf) >= CHUNK:
    chunk = buf[:CHUNK]
    buf = buf[CHUNK:]
    t = vad.push(chunk)
    if t is not None:
        turnos.append(t)

print(f"{len(turnos)} turnos")
for i, t in enumerate(turnos):
    rms = float(np.sqrt(np.mean(t*t)))
    peak = float(np.abs(t).max())
    print(f"[{i}] {len(t)/16000:.2f}s rms={rms:.4f} peak={peak:.4f}")
    print("  whisper:", _stt_whisper(t))
    print("  google :", _stt_google(t))
    np.save(r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\_turno.npy", t)
