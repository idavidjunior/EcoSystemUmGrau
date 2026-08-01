import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
sd.default.device = (1, None)
print("GRAVANDO 6s - FALE UMA FRASE CLARA E COMPLETA...")
rec = sd.rec(SAMPLE_RATE * 6, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()
audio = rec.flatten()
np.save(r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\_fala_gravada.npy", audio)
print(f"gravado peak={np.abs(audio).max():.4f} salvo")
