"""Dialogo por voz no PC — fale naturalmente, Jarvis ouve, responde e executa.

Modos de ativacao:
  vad      -> maos-livres: detecta fala pelo volume, processa quando silencia
  push     -> segure ESPACO para falar, solte para enviar
  ativacao -> diga "Jarvis" para acordar, depois fale o comando
             ("valeu"/"tchau"/"pode dormir" para dormir de novo)

Uso:
  python scripts/dialogo.py [--modo vad|push|ativacao] [--model base]
  python scripts/dialogo.py --texto "fale uma frase direto (sem microfone)"

Variaveis de ambiente (opcionais):
  VOX_THRESHOLD   RMS p/ considerar voz (default 0.02)
  VOX_SILENCIO    segundos de silencio p/ encerrar fala (default 1.2)
  VOX_MAX_FALA    segundos maximo de fala (default 15)
  VOX_WHISPER_MODEL  modelo whisper (default base)
"""

import argparse
import asyncio
import base64
import ctypes
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from vox_audio import SAMPLE_RATE, _stt_whisper, _stt_google  # noqa: E402
from jarvis_bridge import (  # noqa: E402
    Cliente,
    caminho_rapido,
    gerar_audio,
    melhorar_fala,
    normalizar_hora_display,
)

THRESHOLD = float(os.environ.get("VOX_THRESHOLD", "0.02"))
SILENCIO = float(os.environ.get("VOX_SILENCIO", "1.2"))
MAX_FALA = float(os.environ.get("VOX_MAX_FALA", "15"))
BLOCK = int(SAMPLE_RATE * 0.1)

FALAR_COLOR = "\033[92m"
VOZ_COLOR = "\033[96m"
RESET = "\033[0m"

SLEEP_FRASES = re.compile(
    r"^(valeu|tchau|adeus|ate mais|pode dormir|va dormir|dorme|encerra|pode ir|chega por hoje|obrigado|obrigada|flw)\b",
    re.IGNORECASE,
)


def _espaco_pressionado():
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000)
    except Exception:
        return False


def _beep():
    try:
        print("\a", end="", flush=True)
    except Exception:
        pass


def capturar_vad():
    """Grava enquanto ha voz (RMS > threshold); encerra apos silencio."""
    falando = False
    silencio = 0.0
    frames = []
    total = 0.0
    print(f"{VOZ_COLOR}[escutando] fale naturalmente (Ctrl+C para sair){RESET}", flush=True)
    while True:
        rec = sd.rec(BLOCK, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        x = rec.flatten()
        rms = float(np.sqrt(np.mean(x * x)))
        if not falando:
            if rms > THRESHOLD:
                falando = True
                silencio = 0.0
                frames = [x]
                total = 0.1
                _beep()
        else:
            frames.append(x)
            total += 0.1
            if rms < THRESHOLD:
                silencio += 0.1
                if silencio >= SILENCIO:
                    break
            else:
                silencio = 0.0
            if total >= MAX_FALA:
                break
    return np.concatenate(frames) if frames else np.zeros(0, dtype="float32")


def capturar_push():
    """Segure ESPACO para falar; solte para enviar."""
    print(f"{VOZ_COLOR}[push] segure ESPACO para falar (ESC/Ctrl+C para sair){RESET}", flush=True)
    while not _espaco_pressionado():
        import time
        time.sleep(0.05)
    _beep()
    frames = []
    while _espaco_pressionado():
        rec = sd.rec(BLOCK, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        frames.append(rec.flatten())
    _beep()
    return np.concatenate(frames) if frames else np.zeros(0, dtype="float32")


def transcrever(audio):
    if audio.size < SAMPLE_RATE // 5:
        return ""
    texto, fonte = "", ""
    try:
        texto, fonte = _stt_whisper(audio)
    except Exception as e:
        print(f"[whisper falhou: {e}]")
    if not texto:
        try:
            texto, fonte = _stt_google(audio)
        except Exception as e:
            print(f"[google falhou: {e}]")
    if not texto:
        return ""
    print(f"{VOZ_COLOR}[voce ({fonte})]{RESET} {texto}", flush=True)
    return texto


def tocar_base64(b64):
    if not b64:
        return
    mp3 = Path(tempfile.gettempdir()) / "vox_dialogo.mp3"
    mp3.write_bytes(base64.b64decode(b64))
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


async def responder(cliente, texto):
    r = None
    try:
        r = caminho_rapido(texto)
    except Exception:
        r = None
    if r is None:
        try:
            r = await cliente.perguntar(texto)
        except Exception as e:
            r = f"Erro no processamento: {e}"
    if not r:
        r = "Não consegui gerar uma resposta."
    r_tela = normalizar_hora_display(r)
    print(f"{FALAR_COLOR}[jarvis]{RESET} {r_tela}", flush=True)
    try:
        audio = await gerar_audio(r_tela)
    except Exception as e:
        print(f"[tts: {e}]")
        audio = ""
    tocar_base64(audio)


def _separar_jarvis(texto):
    m = re.match(
        r"^\s*(?:hey|ei|opa|ok|tudo bem)?\s*jarvis\s*[,:.]?\s*(.*)$",
        texto,
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else texto


async def loop_vad(cliente):
    while True:
        audio = capturar_vad()
        texto = transcrever(audio)
        if not texto:
            continue
        await responder(cliente, texto)


async def loop_push(cliente):
    while True:
        audio = capturar_push()
        texto = transcrever(audio)
        if not texto:
            continue
        await responder(cliente, texto)


async def loop_ativacao(cliente):
    acordado = False
    while True:
        audio = capturar_vad()
        texto = transcrever(audio)
        if not texto:
            continue
        t = texto.strip().lower()
        if not acordado:
            if re.search(r"\bjarvis\b", texto, re.IGNORECASE):
                comando = _separar_jarvis(texto)
                if comando:
                    acordado = True
                    await responder(cliente, comando)
                else:
                    acordado = True
                    print(f"{FALAR_COLOR}[jarvis]{RESET} Sim, senhor?", flush=True)
                    tocar_base64(await gerar_audio("Sim, senhor?"))
            continue
        if SLEEP_FRASES.match(t):
            acordado = False
            print(f"{FALAR_COLOR}[jarvis]{RESET} Até logo.", flush=True)
            tocar_base64(await gerar_audio("Até logo."))
            continue
        await responder(cliente, texto)


async def main():
    ap = argparse.ArgumentParser(description="Dialogo por voz com Jarvis")
    ap.add_argument("--modo", choices=["vad", "push", "ativacao"], default="vad")
    ap.add_argument("--model", default=os.environ.get("VOX_WHISPER_MODEL", "base"))
    ap.add_argument("--texto", default=None, help="testa sem microfone")
    args = ap.parse_args()

    if args.model != os.environ.get("VOX_WHISPER_MODEL", "base"):
        os.environ["VOX_WHISPER_MODEL"] = args.model

    cliente = Cliente()
    if args.texto:
        await responder(cliente, args.texto)
        return

    print(f"Modo dialogo ativo ({args.modo}). Ctrl+C para encerrar.", flush=True)
    loop = {"vad": loop_vad, "push": loop_push, "ativacao": loop_ativacao}[args.modo]
    try:
        await loop(cliente)
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado.")
