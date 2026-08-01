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
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from vox_audio import SAMPLE_RATE, _stt_whisper, _stt_google, _tocar_mci, _parar_mci_tudo  # noqa: E402
from jarvis_bridge import (  # noqa: E402
    Cliente,
    briefing_espontaneo,
    caminho_rapido,
    gerar_audio,
    gerar_status_natural,
    melhorar_fala,
    normalizar_hora_display,
)

THRESHOLD = float(os.environ.get("VOX_THRESHOLD", "0.5"))
SILENCIO = float(os.environ.get("VOX_SILENCIO", "0.8"))
MAX_FALA = float(os.environ.get("VOX_MAX_FALA", "15"))
VAD_MIN_SILENCE_MS = int(os.environ.get("VOX_VAD_MIN_SILENCE_MS", str(int(SILENCIO * 1000))))
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


def _rms(x):
    return float(np.sqrt(np.mean(x * x)))


# --- Silero VAD streaming (oficial: silero-vad + VADIterator) ---

_SILERO = None


def _carregar_silero():
    """Carrega o Silero VAD oficial (ONNX, CPU) e mantem instancia global."""
    global _SILERO
    if _SILERO is not None:
        return _SILERO, True
    try:
        from silero_vad import load_silero_vad

        _SILERO = load_silero_vad(onnx=True)
        return _SILERO, True
    except Exception as e:
        print(f"[silero indisponivel: {e}]")
        _SILERO = False
        return None, False


class VadSileroStream:
    """Turno de fala usando o VADIterator oficial. Acumula os chunks entre o
    start e o end que o VADIterator retorna (ele nao guarda o audio)."""

    def __init__(self, model, threshold=0.5, min_silence_ms=800, speech_pad_ms=30):
        from silero_vad import VADIterator

        self.vad = VADIterator(
            model,
            threshold=threshold,
            sampling_rate=SAMPLE_RATE,
            min_silence_duration_ms=min_silence_ms,
            speech_pad_ms=speech_pad_ms,
        )
        self.model = model
        self.min_speech_ms = 250
        self.ultima_prob = 0.0
        self.reset()

    def reset(self):
        self.frames = []
        self.speech_ms = 0
        self.ativo = False

    def push(self, chunk_512):
        """Recebe 512 samples (numpy float32). Devolve o audio do turno ao
        terminar a fala, ou None."""
        import torch

        chunk_512 = np.ascontiguousarray(chunk_512, dtype="float32")
        t = torch.from_numpy(chunk_512)
        self.ultima_prob = float(self.model(t, SAMPLE_RATE).item())
        res = self.vad(t)
        if res is not None and "start" in res:
            self.reset()
            self.ativo = True
            self.frames.append(chunk_512.copy())
            self.speech_ms += 32
            return None
        if self.ativo:
            self.frames.append(chunk_512.copy())
            self.speech_ms += 32
        if res is not None and "end" in res:
            self.ativo = False
            audio = np.concatenate(self.frames) if self.frames else np.zeros(0, dtype="float32")
            if self.speech_ms >= self.min_speech_ms:
                return audio
            return None
        return None


def capturar_vad():
    """Escuta o microfone e devolve um turno de fala completo usando o Silero VAD
    oficial (VADIterator). Usa InputStream continuo (sem gaps) no microfone
    Realtek [1], que e o que melhor capta voz nesta maquina."""
    model, ok = _carregar_silero()
    if not ok:
        return _capturar_vad_fallback()
    vad = VadSileroStream(model, threshold=THRESHOLD, min_silence_ms=VAD_MIN_SILENCE_MS)
    print(f"{VOZ_COLOR}[escutando] fale naturalmente (Ctrl+C p/ sair){RESET}", flush=True)
    _beep()
    sd.default.device = (1, None)  # Microfone (Realtek High Definit)
    CHUNK = 512
    buf = np.zeros(0, dtype="float32")
    result = {"turno": None, "n": 0}
    estado = {"mostrando": False}

    def callback(indata, frames, time_info, status):
        nonlocal buf, result, estado
        if result["turno"] is not None:
            return
        x = indata[:, 0]
        buf = np.concatenate([buf, x])
        while len(buf) >= CHUNK:
            chunk = buf[:CHUNK]
            buf = buf[CHUNK:]
            turno = vad.push(chunk)
            prob = vad.ultima_prob
            # feedback visual em tempo real
            if prob >= 0.5 and not estado["mostrando"]:
                print(f"{VOZ_COLOR}[ouvindo...]{RESET}", flush=True)
                estado["mostrando"] = True
            elif prob < 0.5 and estado["mostrando"]:
                estado["mostrando"] = False
            if turno is not None:
                result["turno"] = turno
                return

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback
    )
    try:
        with stream:
            while result["turno"] is None:
                time.sleep(0.05)
        return result["turno"]
    except KeyboardInterrupt:
        return np.zeros(0, dtype="float32")


def _capturar_vad_fallback():
    """Fallback por RMS caso o Silero nao carregue."""
    print(f"{VOZ_COLOR}[vad fallback rms] fale (Ctrl+C p/ sair){RESET}", flush=True)
    limiar = max(THRESHOLD * 0.02, 0.02)
    consec = 0
    falando = False
    silencio = 0.0
    frames = []
    total = 0.0
    while True:
        rec = sd.rec(BLOCK, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        x = rec.flatten()
        rms = _rms(x)
        voz = rms > limiar
        if not falando:
            if voz:
                consec += 1
                if consec >= 3:
                    falando = True
                    silencio = 0.0
                    frames = [x]
                    total = 0.1
            else:
                consec = 0
        else:
            frames.append(x)
            total += 0.1
            if not voz:
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


def _parece_alucinacao(texto):
    """Whisper base alucina padroes repetitivos em audio de fala curta/noise
    (ex.: 'N-n-n-n-n', 'Tua, tua, tua'). Detecta para cair no Google."""
    if not texto:
        return False
    t = texto.strip()
    # repete a mesma silaba/palavra 3+ vezes
    palavras = re.findall(r"[a-zA-Záéíóúâêôãõçà]+", t)
    if not palavras:
        return True
    repetidas = {}
    for p in palavras:
        base = re.sub(r"(.)\1+", r"\1", p.lower())
        repetidas[base] = repetidas.get(base, 0) + 1
    top = max(repetidas.values())
    if top >= 3:
        return True
    # poucas palavras todas curtas e iguais entre si
    if len(palavras) >= 3 and len(set(p.lower() for p in palavras)) == 1:
        return True
    return False


def transcrever(audio):
    if audio.size < SAMPLE_RATE // 5:
        print(f"{VOZ_COLOR}[segmento curto {audio.size} ignorado]{RESET}", flush=True)
        return ""
    texto, fonte = "", ""
    try:
        texto, fonte = _stt_whisper(audio)
    except Exception as e:
        print(f"[whisper falhou: {e}]")
    if _parece_alucinacao(texto):
        print(f"{VOZ_COLOR}[whisper suspeito '{texto[:40]}', tentando google]{RESET}", flush=True)
        texto = ""
    if not texto:
        try:
            texto, fonte = _stt_google(audio)
        except Exception as e:
            print(f"[google falhou: {e}]")
    if not texto:
        return ""
    print(f"{VOZ_COLOR}[voce ({fonte})]{RESET} {texto}", flush=True)
    return texto


def tocar_base64(b64, parar_evento=None):
    if not b64:
        return
    mp3 = Path(tempfile.gettempdir()) / "vox_dialogo.mp3"
    mp3.write_bytes(base64.b64decode(b64))
    try:
        _tocar_mci(str(mp3), parar_evento=parar_evento)
    except Exception as e:
        print(f"[erro play] {e}")


# --- Barge-in: interromper a fala do Jarvis ---

def _tecla_pressionada(vk):
    """True se a tecla virtual `vk` esta pressionada agora."""
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


def _monitorar_teclado(parar_evento):
    """Fica em thread: se o usuario apertar ESC ou Enter, dispara a parada da fala."""
    while not parar_evento.is_set():
        if _tecla_pressionada(0x1B) or _tecla_pressionada(0x0D):  # ESC ou Enter
            print(f"{VOZ_COLOR}[interrompido pelo teclado]{RESET}", flush=True)
            parar_evento.set()
            return
        time.sleep(0.05)


def _monitorar_microfone(parar_evento, limiar_rms=None):
    """Fica em thread: se detectar fala do usuario (RMS acima do limiar) durante
    a fala do Jarvis, dispara a parada (barge-in por voz)."""
    if limiar_rms is None:
        limiar_rms = float(os.environ.get("VOX_BARGEIN_RMS", "0.03"))
    sd.default.device = (1, None)  # Microfone (Realtek High Definit)
    BLOCK = int(SAMPLE_RATE * 0.1)
    consec = 0
    while not parar_evento.is_set():
        try:
            rec = sd.rec(BLOCK, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()
            rms = _rms(rec.flatten())
            if rms > limiar_rms:
                consec += 1
                if consec >= 2:  # ~200ms de fala continua = barge-in
                    print(f"{VOZ_COLOR}[interrompido pela voz]{RESET}", flush=True)
                    parar_evento.set()
                    return
            else:
                consec = 0
        except Exception:
            return


def falar_com_bargein(b64):
    """Toca o audio enquanto escuta teclado (ESC/Enter) e microfone. Se houver
    interrupcao, corta o audio imediatamente e devolve True (usuario quer falar)."""
    if not b64:
        return False
    parar_evento = threading.Event()
    threads = [
        threading.Thread(target=_monitorar_teclado, args=(parar_evento,), daemon=True),
        threading.Thread(target=_monitorar_microfone, args=(parar_evento,), daemon=True),
    ]
    for t in threads:
        t.start()
    tocar_base64(b64, parar_evento=parar_evento)
    # se a fala terminou naturalmente, rearma o evento (nao matou por interrupcao)
    interrompido = parar_evento.is_set()
    if interrompido:
        time.sleep(0.2)  # deixa o microfone estabilizar apos cortar
    return interrompido


async def responder(cliente, texto, interrompivel=True):
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
    if interrompivel:
        falar_com_bargein(audio)
    else:
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
                    falar_com_bargein(await gerar_audio("Sim, senhor?"))
            continue
        if SLEEP_FRASES.match(t):
            acordado = False
            print(f"{FALAR_COLOR}[jarvis]{RESET} Até logo.", flush=True)
            falar_com_bargein(await gerar_audio("Até logo."))
            continue
        await responder(cliente, texto)


async def saudar_inicio(cliente):
    """Saudação criativa via LLM — mesmo núcleo do app de celular (jarvis_bridge.saudar)."""
    status = gerar_status_natural()
    try:
        extra = briefing_espontaneo()
    except Exception:
        extra = ""
    saudacao = ""
    try:
        saudacao = await cliente.saudar(extra, status)
    except Exception as e:
        print(f"[saudar: {e}]")
    if not saudacao:
        abridores = [
            "Olá", "Opa", "E aí", "Fala", "Oi", "Bom te ver", "Salve", "Chegou, chegou"
        ]
        fechos = [
            "Como posso ajudar?", "O que vamos fazer hoje?", "Estou por aqui. O que precisa?",
            "Diga o que você precisa.", "O que posso fazer por você hoje?"
        ]
        import random
        saudacao = f"{random.choice(abridores)}! {extra}{status}{random.choice(fechos)}"
    saudacao_tela = normalizar_hora_display(saudacao)
    print(f"{FALAR_COLOR}[jarvis]{RESET} {saudacao_tela}", flush=True)
    try:
        audio = await gerar_audio(saudacao_tela)
    except Exception as e:
        print(f"[tts saudacao: {e}]")
        audio = ""
    falar_com_bargein(audio)


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
    try:
        await saudar_inicio(cliente)
    except Exception as e:
        print(f"[saudacao falhou: {e}]")
        tocar_base64(await gerar_audio("Estou ouvindo. Pode falar."))
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
