"""Vox Audio — STT (Whisper local + fallback Google) e TTS (edge-tts) para o Jarvis.

Modos:
  ouvir            → captura microfone e transcreve (whisper, fallback google)
  ouvir-google     → captura microfone e transcreve via Google Web Speech
  falar "texto"    → gera e toca o áudio via edge-tts + WPF MediaPlayer
  testar-mic       → lista dispositivos de áudio de entrada
"""

import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TTS_VOICE = "pt-BR-AntonioNeural"
TTS_RATE = "+0%"
TTS_PITCH = "+0Hz"

WHISPER_MODEL = os.environ.get("VOX_WHISPER_MODEL", "base")
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

GOOGLE_LANG = "pt-BR"
SAMPLE_RATE = 16000
RECORD_SECONDS = float(os.environ.get("VOX_RECORD_SECONDS", "7"))
ENERGY_THRESHOLD = 300


def _falar(texto):
    """Gera MP3 com edge-tts e toca com WPF MediaPlayer (suporta MP3)."""
    if not texto or not texto.strip():
        return
    mp3 = Path(tempfile.gettempdir()) / "vox_fala.mp3"
    try:
        asyncio.run(
            _tts_salvar(texto, str(mp3))
        )
    except Exception as e:
        print(f"[erro tts] {e}")
        return
    if not mp3.exists():
        return
    ps = (
        "Add-Type -AssemblyName PresentationCore; "
        f"`$p = [System.Windows.Media.MediaPlayer]::new(); "
        f"`$p.Open([Uri]::new('{mp3}')); `$p.Play(); "
        "Start-Sleep -Seconds 2; while (`$p.NaturalDuration.HasTimeSpan -and "
        "(`$p.Position -lt `$p.NaturalDuration.TimeSpan)) { Start-Sleep -Milliseconds 200 }; "
        "`$p.Close()"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, timeout=120,
        )
    except Exception as e:
        print(f"[erro play] {e}")


async def _tts_salvar(texto, caminho):
    import edge_tts
    tts = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    await tts.save(caminho)


def _gravar_audio(seconds=RECORD_SECONDS):
    """Grava microfone e retorna ndarray float32 mono 16kHz."""
    import sounddevice as sd
    import numpy as np
    print(f"Ouvindo... (fale agora, {seconds:.0f}s, `^C` para cortar)")
    rec = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    return rec.flatten()


def _stt_whisper(audio):
    from faster_whisper import WhisperModel
    import numpy as np
    print(f"Transcrevendo com Whisper ({WHISPER_MODEL})...")
    model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
    audio_16k = (audio * 32767).astype(np.int16)
    segments, info = model.transcribe(audio_16k, language="pt", beam_size=5)
    texto = " ".join(s.text.strip() for s in segments).strip()
    return texto, f"whisper:{WHISPER_MODEL}"


def _stt_google(audio):
    import speech_recognition as sr
    import numpy as np
    pcm = (audio * 32767).astype(np.int16).tobytes()
    rec = sr.AudioData(pcm, SAMPLE_RATE, 2)
    r = sr.Recognizer()
    try:
        texto = r.recognize_google(rec, language=GOOGLE_LANG)
        return texto, "google"
    except sr.UnknownValueError:
        return "", "google"
    except sr.RequestError as e:
        return f"[erro google: {e}]", "google"


def cmd_ouvir(force_google=False):
    audio = _gravar_audio()
    texto = ""
    fonte = ""
    if not force_google:
        try:
            texto, fonte = _stt_whisper(audio)
        except Exception as e:
            print(f"[whisper falhou, fallback google] {e}")
            texto = ""
    if not texto:
        texto, fonte = _stt_google(audio)
    print(f"[STT:{fonte}] {texto}")
    return texto


def cmd_ouvir_google():
    audio = _gravar_audio()
    texto, fonte = _stt_google(audio)
    print(f"[STT:{fonte}] {texto}")
    return texto


def cmd_falar(texto):
    _falar(texto)
    print(f"[Falado {len(texto)} chars]")


def cmd_testar_mic():
    import sounddevice as sd
    print("Dispositivos de entrada:")
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{i}] {d['name']} (in: {d['max_input_channels']}ch, default: {d['default_samplerate']}Hz)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Vox Audio (STT + TTS)")
    ap.add_argument("modo", choices=["ouvir", "ouvir-google", "falar", "testar-mic"])
    ap.add_argument("texto", nargs="*", default=None)
    args = ap.parse_args()

    if args.modo == "ouvir":
        cmd_ouvir()
    elif args.modo == "ouvir-google":
        cmd_ouvir_google()
    elif args.modo == "falar":
        cmd_falar(" ".join(args.texto) if args.texto else "Nada para falar")
    elif args.modo == "testar-mic":
        cmd_testar_mic()
