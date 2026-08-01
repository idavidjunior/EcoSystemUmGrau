"""Grava 5s de voz e valida o Silero VAD no audio. Uso: python _vad_probe.py
Fale algo por ~4s quando aparecer 'GRAVANDO'."""
import sys
from pathlib import Path

import numpy as np
import sounddevice as sd

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from faster_whisper.utils import get_assets_path
from faster_whisper.vad import SileroVADModel, VadOptions, get_speech_timestamps

SAMPLE_RATE = 16000
sd.default.device = (1, None)  # Microfone Realtek que capta melhor
print("GRAVANDO 5s - FALE AGORA (claro e firme)...", flush=True)
rec = sd.rec(SAMPLE_RATE * 5, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()
audio = rec.flatten()
print(f"gravado {len(audio)/SAMPLE_RATE:.1f}s rms={float(np.sqrt(np.mean(audio**2))):.4f} peak={float(np.abs(audio).max()):.4f}", flush=True)

# normaliza (AGC leve)
p = float(np.abs(audio).max())
if p > 0 and p < 0.9:
    audio = audio * (0.7 / p)
    np.clip(audio, -1.0, 1.0, out=audio)
    print(f"normalizado peak={float(np.abs(audio).max()):.4f}", flush=True)

path = str(get_assets_path()) + "\\silero_vad_v6.onnx"
opts = VadOptions(
    threshold=0.5,
    min_speech_duration_ms=250,
    min_silence_duration_ms=800,
    speech_pad_ms=400,
)
ts = get_speech_timestamps(audio, vad_options=opts, sampling_rate=SAMPLE_RATE)
print(f"segmentos detectados: {len(ts)}", flush=True)
for t in ts:
    print(f"  fala: {t['start']/SAMPLE_RATE:.2f}s -> {t['end']/SAMPLE_RATE:.2f}s", flush=True)

import vox_audio
texto, fonte = vox_audio._stt_whisper(audio)
print(f"[STT WHISPER:] {texto!r} ({fonte})", flush=True)
texto2, fonte2 = vox_audio._stt_google(audio)
print(f"[STT GOOGLE:] {texto2!r} ({fonte2})", flush=True)
