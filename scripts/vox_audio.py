"""Vox Audio — STT (Whisper local + fallback Google) e TTS (edge-tts) para o Jarvis.

Modos:
  ouvir            → captura microfone e transcreve (whisper, fallback google)
  ouvir-google     → captura microfone e transcreve via Google Web Speech
  falar "texto"    → gera e toca o áudio via SpeechPipeline (ou fallback legado)
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

# Speech Pipeline — pipeline central de TTS
ECOSSISTEMA_DIR = Path(__file__).resolve().parent.parent
if str(ECOSSISTEMA_DIR) not in sys.path:
    sys.path.insert(0, str(ECOSSISTEMA_DIR))
try:
    from tts import SpeechPipeline
    _speech_pipeline = SpeechPipeline()
    SPEECH_PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"[warning] SpeechPipeline não disponível: {e}")
    SPEECH_PIPELINE_AVAILABLE = False
    _speech_pipeline = None

TTS_VOICE = "pt-BR-AntonioNeural"
TTS_RATE = "+0%"
TTS_PITCH = "+0Hz"

WHISPER_MODEL = os.environ.get("VOX_WHISPER_MODEL", "base")
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"
_WHISPER_MODEL = None

GOOGLE_LANG = "pt-BR"
SAMPLE_RATE = 16000
RECORD_SECONDS = float(os.environ.get("VOX_RECORD_SECONDS", "7"))
ENERGY_THRESHOLD = 300


def _tocar_mci(mp3, parar_evento=None):
    """Toca MP3 via API MCI do Windows (confiavel em scripts; MediaPlayer falha
    em subprocessos). Bloqueia ate o final do audio.

    Se `parar_evento` (threading.Event) for fornecido, o audio para no momento
    em que o evento for setado (barge-in: usuario falou ou apertou tecla)."""
    import ctypes
    import time
    mci = ctypes.windll.winmm.mciSendStringW
    alias = f"vox{int(time.time() * 1000)}"
    r = mci(f'open "{mp3}" type mpegvideo alias {alias}', None, 0, 0)
    if r != 0:
        print(f"[erro mci open: {r}]")
        return
    mci(f'play {alias}', None, 0, 0)
    buf = ctypes.create_unicode_buffer(128)
    mci(f'status {alias} length', buf, 128, 0)
    try:
        duracao_ms = int(buf.value)
    except ValueError:
        duracao_ms = 0
    if parar_evento is not None:
        # toca em steps pequenos, cortando na hora que o evento disparar
        fim = duracao_ms / 1000 + 0.3 if duracao_ms > 0 else 15.0
        decorrido = 0.0
        while decorrido < fim:
            if parar_evento.is_set():
                mci(f'stop {alias}', None, 0, 0)
                break
            time.sleep(0.05)
            decorrido += 0.05
        # se acabou sem interrupcao, close normal; se interrompeu, ja parado
    elif duracao_ms > 0:
        time.sleep(duracao_ms / 1000 + 0.3)
    else:
        time.sleep(1.0)
    try:
        mci(f'close {alias}', None, 0, 0)
    except Exception:
        pass


def _parar_mci_tudo():
    """Para toda reprodução MCI em andamento (barge-in de emergencia)."""
    import ctypes
    try:
        ctypes.windll.winmm.mciSendStringW("stop all", None, 0, 0)
        ctypes.windll.winmm.mciSendStringW("close all", None, 0, 0)
    except Exception:
        pass


def _falar(texto, parar_evento=None):
    """Gera MP3 e toca via MCI. Streaming: toca enquanto gera (reduz latência)."""
    if not texto or not texto.strip():
        return

    # Tenta usar SpeechPipeline primeiro
    if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
        try:
            mp3 = Path(tempfile.gettempdir()) / "vox_fala.mp3"
            if _speech_pipeline.save(texto, str(mp3)):
                _tocar_mci(str(mp3), parar_evento=parar_evento)
                return
        except Exception as e:
            print(f"[SpeechPipeline falhou: {e}]")

    # Streaming: gera áudio em chunks e toca assim que tiver buffer suficiente
    mp3 = Path(tempfile.gettempdir()) / "vox_fala_stream.mp3"
    try:
        asyncio.run(_tts_stream_e_tocar(texto, str(mp3), parar_evento))
    except Exception as e:
        print(f"[erro stream tts] {e}")
        # Fallback: método legado (batch)
        mp3_batch = Path(tempfile.gettempdir()) / "vox_fala.mp3"
        try:
            asyncio.run(_tts_salvar(texto, str(mp3_batch)))
            _tocar_mci(str(mp3_batch), parar_evento=parar_evento)
        except Exception as e2:
            print(f"[erro fallback tts] {e2}")


async def _tts_stream_e_tocar(texto, caminho_mp3, parar_evento=None):
    """Gera áudio via streaming e toca assim que tiver dados suficientes.
    
    Reduz latência significativamente: em vez de aguardar áudio completo,
    toca os primeiros chunks enquanto o resto ainda está sendo gerado.
    """
    import edge_tts
    import threading

    # Prepara communicate
    try:
        from pronunciar_termos import marcar_para_tts
        texto_marcado = marcar_para_tts(texto, formato="ssml")
        if texto_marcado and '<lang' in str(texto_marcado):
            texto_ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">{texto_marcado}</speak>'
            communicate = edge_tts.Communicate(texto_ssml, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
        else:
            communicate = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    except (ImportError, Exception):
        communicate = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)

    # Coleta chunks de áudio
    audio_chunks = []
    total_bytes = 0
    PREBUFFER_BYTES = 8000  # ~8KB = ~200ms de áudio (suficiente para começar a tocar)
    started_playing = False
    
    async for chunk in communicate.stream():
        if parar_evento and parar_evento.is_set():
            break
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
            total_bytes += len(chunk["data"])
            
            # Quando tiver buffer suficiente, começa a tocar em thread separada
            if not started_playing and total_bytes >= PREBUFFER_BYTES:
                started_playing = True
                # Salva o que já tem e começa a tocar
                with open(caminho_mp3, "wb") as f:
                    for c in audio_chunks:
                        f.write(c)
                # Toca em background enquanto continua recebendo
                play_thread = threading.Thread(
                    target=_tocar_mci, 
                    args=(caminho_mp3,), 
                    kwargs={"parar_evento": parar_evento},
                    daemon=True
                )
                play_thread.start()
    
    # Salva áudio completo (para futuras reproduções ou cache)
    if audio_chunks:
        with open(caminho_mp3, "wb") as f:
            for c in audio_chunks:
                f.write(c)
    
    # Se não deu para tocar streaming (texto muito curto), toca agora
    if not started_playing and audio_chunks:
        _tocar_mci(caminho_mp3, parar_evento=parar_evento)


async def _tts_salvar(texto, caminho):
    import edge_tts
    # Marcar termos técnicos em inglês para pronúncia correta via SSML
    try:
        from pronunciar_termos import marcar_para_tts
        texto_marcado = marcar_para_tts(texto, formato="ssml")
        # Se SSML retornou algo diferente, usar; senão, usar texto original
        if texto_marcado and '<lang' in str(texto_marcado):
            # Envolver em SSML completo para edge-tts
            texto_ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">{texto_marcado}</speak>'
            tts = edge_tts.Communicate(texto_ssml, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
        else:
            tts = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    except ImportError:
        tts = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    except Exception:
        # Fallback: usar texto original sem marcação
        tts = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    await tts.save(caminho)


def _gravar_audio(seconds=RECORD_SECONDS):
    """Grava microfone e retorna ndarray float32 mono 16kHz.
    Usa device 11 (WDM-KS) a 44100Hz e faz downsample para 16kHz."""
    import sounddevice as sd
    import numpy as np
    try:
        import scipy.signal
        HAVE_SCIPY = True
    except ImportError:
        HAVE_SCIPY = False
    
    # Device 11 funciona a 44100Hz
    DEVICE_ID = 11
    RECORD_SR = 44100
    
    print(f"Ouvindo... (fale agora, {seconds:.0f}s)")
    try:
        n_samples = int(seconds * RECORD_SR)
        rec = sd.rec(n_samples, samplerate=RECORD_SR, channels=1, dtype="float32", device=DEVICE_ID)
        sd.wait()
        audio = rec.flatten()
        
        # Downsample 44100 -> 16000
        if HAVE_SCIPY:
            audio = scipy.signal.resample(audio, int(len(audio) * SAMPLE_RATE / RECORD_SR))
        else:
            # Fallback simples: decimação linear
            step = RECORD_SR / SAMPLE_RATE
            idx = np.arange(0, len(audio), step).astype(int)
            idx = idx[idx < len(audio)]
            audio = audio[idx]
        
        return audio
    except Exception as e:
        print(f"[erro gravacao device 11: {e}] - tentando default")
        # Fallback: device default
        rec = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        return rec.flatten()


def _stt_whisper(audio, partial_callback=None):
    """Transcreve audio com Whisper. Se `partial_callback` for fornecido,
    ela e chamada com cada segmento a medida que completar (streaming parcial),
    permitindo feedback em tempo real ao inves de bloquear ate o final."""
    from faster_whisper import WhisperModel
    import numpy as np
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
    print(f"Transcrevendo com Whisper ({WHISPER_MODEL})...")
    audio_16k = (audio * 32767).astype(np.int16)
    segments, info = _WHISPER_MODEL.transcribe(
        audio_16k,
        language="pt",
        beam_size=5,
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
        log_prob_threshold=-1.0,
    )
    texto = ""
    for s in segments:
        seg_text = s.text.strip()
        if seg_text:
            texto += seg_text + " "
            if partial_callback:
                partial_callback(texto.strip())
            print(f"\r{VOZ_COLOR}[voce (streaming)]{RESET} {texto.strip()}", flush=True, end="", file=sys.stderr)
    print()
    return texto.strip(), f"whisper:{WHISPER_MODEL}"


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


def cmd_ouvir(force_google=False, partial_callback=None):
    audio = _gravar_audio()
    texto = ""
    fonte = ""
    if not force_google:
        try:
            texto, fonte = _stt_whisper(audio, partial_callback=partial_callback)
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


async def _falar_async(texto, parar_evento=None):
    """Versão async de _falar para uso dentro de event loop. Streaming: toca enquanto gera."""
    if not texto or not texto.strip():
        return

    # Tenta usar SpeechPipeline primeiro
    if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
        try:
            mp3 = Path(tempfile.gettempdir()) / "vox_fala.mp3"
            if _speech_pipeline.save(texto, str(mp3)):
                _tocar_mci(str(mp3), parar_evento=parar_evento)
                return
        except Exception as e:
            print(f"[SpeechPipeline falhou: {e}]")

    # Streaming: gera áudio em chunks e toca assim que tiver buffer suficiente
    mp3 = Path(tempfile.gettempdir()) / "vox_fala_stream.mp3"
    try:
        await _tts_stream_e_tocar(texto, str(mp3), parar_evento)
    except Exception as e:
        print(f"[erro stream tts] {e}")
        # Fallback: método legado (batch)
        mp3_batch = Path(tempfile.gettempdir()) / "vox_fala.mp3"
        try:
            await _tts_salvar(texto, str(mp3_batch))
            _tocar_mci(str(mp3_batch), parar_evento=parar_evento)
        except Exception as e2:
            print(f"[erro fallback tts] {e2}")


async def cmd_falar_async(texto, interruptivel=False):
    import threading
    evento = threading.Event()
    await _falar_async(texto, parar_evento=evento)
    print(f"[Falado {len(texto)} chars]" + (" (interruptivel)" if interruptivel else ""))


def cmd_falar(texto, interruptivel=False):
    import threading
    evento = threading.Event()
    _falar(texto, parar_evento=evento)
    print(f"[Falado {len(texto)} chars]" + (" (interruptivel)" if interruptivel else ""))


def cmd_testar_mic():
    import sounddevice as sd
    print("Dispositivos de entrada:")
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{i}] {d['name']} (in: {d['max_input_channels']}ch, default: {d['default_samplerate']}Hz)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Vox Audio (STT + TTS)")
    ap.add_argument("modo", choices=["ouvir", "ouvir-google", "falar", "testar-mic"])
    ap.add_argument("--partial", action="store_true", help="mostra resultados parciais durante a transcricao")
    ap.add_argument("texto", nargs="*", default=None)
    args = ap.parse_args()

    if args.modo == "ouvir":
        cmd_ouvir(partial_callback=(lambda t: print(f"\r{VOZ_COLOR}[streaming] {t}{RESET}", end="", flush=True)) if args.partial else None)
    elif args.modo == "ouvir-google":
        cmd_ouvir_google()
    elif args.modo == "falar":
        cmd_falar(" ".join(args.texto) if args.texto else "Nada para falar", interruptivel=True)
    elif args.modo == "testar-mic":
        cmd_testar_mic()
