import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import numpy as np
import sounddevice as sd
import dialogo

SAMPLE_RATE = 16000
sd.default.device = (1, None)

model, ok = dialogo._carregar_silero()
print("silero ok:", ok)

print("GRAVANDO 6s - FALE UMA FRASE CLARA E ALTA...")
rec = sd.rec(SAMPLE_RATE * 6, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()
audio = rec.flatten()
print(f"gravado {len(audio)/SAMPLE_RATE:.1f}s peak={np.abs(audio).max():.4f} rms={np.sqrt(np.mean(audio**2)):.4f}")

import torch
CHUNK = 512
# processa cada chunk individualmente para ver a prob
probs = []
for i in range(0, len(audio) - CHUNK, CHUNK):
    chunk = torch.from_numpy(audio[i:i+CHUNK].astype("float32"))
    out = model(chunk, SAMPLE_RATE)  # OnnxWrapper aceita 1D
    p = out.item()
    probs.append(p)
    if p > 0.3:
        print(f"  ch{i//CHUNK}: prob={p:.3f}")

import numpy as np2
probs = np2.array(probs)
print(f"prob max={probs.max():.3f} mean={probs.mean():.3f} >0.3:{(probs>0.3).sum()} >0.5:{(probs>0.5).sum()}")
