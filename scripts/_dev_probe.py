import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
sd.default.device = (1, None)

n = {"i": 0, "peaks": []}
def callback(indata, frames, time_info, status):
    x = indata[:, 0]
    p = float(np.abs(x).max())
    r = float(np.sqrt(np.mean(x * x)))
    n["i"] += 1
    if n["i"] % 20 == 0:
        print(f"chunk {n['i']}: rms={r:.4f} peak={p:.4f}", flush=True)

print("GRAVANDO 8s - FALE AGORA...")
stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback)
with stream:
    import time
    time.sleep(8)
print("fim")
