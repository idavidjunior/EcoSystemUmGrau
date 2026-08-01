import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import numpy as np
import torch
import dialogo

audio = np.load(r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\_fala_gravada.npy")

from silero_vad import VADIterator
model, ok = dialogo._carregar_silero()
vad = VADIterator(model, threshold=0.5, sampling_rate=16000, min_silence_duration_ms=800, speech_pad_ms=30)

CHUNK = 512
starts = 0
ends = 0
last = None
for i in range(0, len(audio) - CHUNK, CHUNK):
    chunk = torch.from_numpy(audio[i:i+CHUNK].astype("float32"))
    res = vad(chunk)
    if res is not None:
        print(f"  ch{i//CHUNK}: {res}")
        if "start" in res:
            starts += 1
        if "end" in res:
            ends += 1

print(f"starts={starts} ends={ends}")
