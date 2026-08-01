import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import numpy as np
import sounddevice as sd
import dialogo

SAMPLE_RATE = 16000
sd.default.device = (1, None)

model, ok = dialogo._carregar_silero()
print("silero ok:", ok)

from silero_vad import VADIterator
vad = VADIterator(model, threshold=0.5, sampling_rate=SAMPLE_RATE, min_silence_duration_ms=800, speech_pad_ms=30)

print("GRAVANDO 6s - FALE UMA FRASE CLARA...")
rec = sd.rec(SAMPLE_RATE * 6, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()
audio = rec.flatten()
print(f"gravado {len(audio)/SAMPLE_RATE:.1f}s peak={np.abs(audio).max():.4f}")

import torch
CHUNK = 512
starts = []
ends = []
for i in range(0, len(audio) - CHUNK, CHUNK):
    chunk = audio[i:i+CHUNK].astype("float32")
    res = vad(torch.from_numpy(chunk))
    if res is not None:
        print(f"  ch{i//CHUNK}: {res}")
        if "start" in res:
            starts.append(i)
        if "end" in res:
            ends.append(i)

print(f"starts={len(starts)} ends={len(ends)}")
