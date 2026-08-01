import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import numpy as np
import dialogo
from vox_audio import _stt_whisper, _stt_google

audio = dialogo.capturar_vad()
dur = len(audio) / 16000
print(f"turno {dur:.2f}s")
np.save(r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\_turno2.npy", audio)

# recorta silencio das bordas para o STT nao sofrer
rms = np.sqrt(np.mean(audio**2))
print(f"rms={rms:.4f} peak={np.abs(audio).max():.4f}")
