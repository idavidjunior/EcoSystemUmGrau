"""Vox Audio — STT (Whisper local + fallback Google) e TTS (edge-tts) para o Jarvis.

Modos:
  ouvir            → captura microfone e transcreve (whisper, fallback google)
  ouvir-google     → captura microfone e transcreve via Google Web Speech
  falar "texto"    → gera e toca o áudio via SpeechPipeline (ou fallback legado)
  testar-mic       → lista dispositivos de áudio de entrada
"""

import argparse
import asyncio
import os
import re
import sys
import tempfile
import threading
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

# Cache de áudio para frases comuns (elimina latência de rede)
AUDIO_CACHE_DIR = Path(tempfile.gettempdir()) / "jarvis_tts_cache"
AUDIO_CACHE_DIR.mkdir(exist_ok=True)
AUDIO_CACHE_MAX = 50  # máximo de arquivos em cache

# Flag global de parada (mesmo arquivo do widget/servicos)
STOP_FLAG = ECOSSISTEMA_DIR / "runtime" / "parar_fala.flag"

WHISPER_MODEL = os.environ.get("VOX_WHISPER_MODEL", "base")
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"
_WHISPER_MODEL = None
_PLAYBACK_LOCK = threading.RLock()

# Filtros de alucinação (padrão isair/jarvis): segmentos que o próprio Whisper
# avalia como sem fala (no_speech_prob alto) ou com confiança muito baixa
# (avg_logprob muito negativo) são descartados — mata transcrições fantasmas
# em silêncio/ruído. Ajustáveis via env para calibrar sem editar código.
WHISPER_MIN_AVG_LOGPROB = float(os.environ.get("VOX_WHISPER_MIN_LOGPROB", "-2.0"))
WHISPER_MAX_NO_SPEECH = float(os.environ.get("VOX_WHISPER_NO_SPEECH", "0.5"))

# --- Hallucination filter: lista de frases conhecidas que o Whisper
# costuma gerar do nada (silêncio/ruído), validada em ICASSP 2025
# (arXiv:2501.11378 — Bag of Hallucinations) e usada pelo Hermes Agent. ---
WHISPER_HALLUCINATIONS = {
    # Português Brasileiro
    "obrigado", "obrigada", "obrigado pela audiência", "obrigado por assistir",
    "obrigada pela audiência", "obrigada por assistir",
    "inscreva-se", "inscreva-se no canal", "inscreva-se no meu canal",
    "se inscreva", "se inscreva no canal", "se inscreva no meu canal",
    "like and subscribe", "like and subscribe",
    "até mais", "até logo", "até amanhã", "até amanhã",
    "volte sempre", "volte para cá", "volte sempre",
    "comentem aqui embaixo", "deixe seu comentário", "deixe seu comentario",
    "curta o vídeo", "curta esse vídeo", "curta o vídeo",
    "compartilhe com os amigos", "compartilhe esse vídeo",
    "ativinho", "ativinho do dia", "ativinho de vocês",
    "você é incrível", "você é o melhor",
    # Inglês
    "thank you", "thank you very much", "thanks for watching",
    "thanks for your time", "please subscribe",
    "please like and subscribe", "please like the video",
    "bye", "bye bye", "see you", "see you later", "see you soon",
    "the end", "that's all", "that's it", "that is all",
    "you're amazing", "you're the best", "you're awesome",
    "have a nice day", "have a great day", "good night",
    "good morning", "good evening", "goodbye",
    "don't forget to", "make sure to", "remember to",
    # Genéricos — padrões que costumam aparecer como alucinação
    "welcome to", "welcome back", "welcome to the",
    "before we go", "before we start", "before we end",
    "in today's video", "in this video", "in this tutorial",
    "i hope you", "i hope you enjoyed", "i hope you liked",
    "if you liked", "if you enjoyed", "if you found this helpful",
    "stay tuned", "stay safe", "stay healthy",
    "now let's", "now let me", "now let's get",
    "so what are you waiting", "so let's get started",
    "today we're going to", "today we're gonna",
    "in this video i", "in this tutorial i",
}

_HALLUCINATION_REPEAT_RE = re.compile(
    r'^(?:n[-\s]?n[-\s]?n)+$',
    flags=re.IGNORECASE,
)

_HALLUCINATION_SINGLE_CHARS_RE = re.compile(
    r'^(?:[a-z]\s*[-,\s]*\s*)+$',
    flags=re.IGNORECASE,
)


def _is_hallucination(texto):
    """Detecta alucinações conhecidas do Whisper usando lista de frases
    conhecidas + padrões repetitivos. Baseado em pesquisa ICASSP 2025
    (arXiv:2501.11378) e implementação Hermes Agent."""
    if not texto or not texto.strip():
        return True
    t = texto.strip().lower()
    if not t:
        return True
    if t in WHISPER_HALLUCINATIONS:
        return True
    if _HALLUCINATION_REPEAT_RE.match(t):
        return True
    if _HALLUCINATION_SINGLE_CHARS_RE.match(t):
        return True
    return False

GOOGLE_LANG = "pt-BR"
SAMPLE_RATE = 16000
RECORD_SECONDS = float(os.environ.get("VOX_RECORD_SECONDS", "7"))
ENERGY_THRESHOLD = 300


def _tocar_mci(mp3, parar_evento=None, stop_flag=None):
    """Toca MP3 ou WAV via API MCI do Windows. Auto-detecta o tipo.

    Se `parar_evento` (threading.Event) for fornecido, o audio para no momento
    em que o evento for setado (barge-in: usuario falou ou apertou tecla).
    Se `stop_flag` (Path) for fornecido, o audio para se o arquivo existir
    (mecanismo de parada global do widget/servicos)."""
    import ctypes
    import time
    from pathlib import Path
    with _PLAYBACK_LOCK:
        mci = ctypes.windll.winmm.mciSendStringW
        alias = f"vox{int(time.time() * 1000)}"
        ext = Path(str(mp3)).suffix.lower()
        mci_type = "waveaudio" if ext in (".wav", ".wave") else "mpegvideo"
        r = mci(f'open "{mp3}" type {mci_type} alias {alias}', None, 0, 0)
        if r != 0:
            print(f"[erro mci open: {r}]")
            return
        mci(f'play {alias}', None, 0, 0)
        buf = ctypes.create_unicode_buffer(128)
        mci(f"status {alias} length", buf, 128, 0)
        try:
            duracao_ms = int(buf.value)
        except ValueError:
            duracao_ms = 0
        fim = duracao_ms / 1000 + 0.3 if duracao_ms > 0 else 15.0
        decorrido = 0.0
        while decorrido < fim:
            if parar_evento is not None and parar_evento.is_set():
                mci(f'stop {alias}', None, 0, 0)
                break
            if stop_flag is not None and isinstance(stop_flag, Path) and stop_flag.exists():
                try:
                    stop_flag.unlink(missing_ok=True)
                except Exception:
                    pass
                mci(f'stop {alias}', None, 0, 0)
                break
            time.sleep(0.05)
            decorrido += 0.05
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


def _limpar_cache_tts():
    """Remove arquivos antigos do cache TTS se exceder o limite."""
    try:
        arquivos = sorted(AUDIO_CACHE_DIR.glob("*.mp3"), key=lambda f: f.stat().st_atime)
        while len(arquivos) > AUDIO_CACHE_MAX:
            arquivos.pop(0).unlink(missing_ok=True)
    except Exception:
        pass


def _novo_mp3_temp(prefixo="vox_fala"):
    """Cria caminho MP3 temporário único (evita [WinError 32]: processos
    concorrentes escrevendo no mesmo nome fixo em %TEMP%)."""
    fd, caminho = tempfile.mkstemp(prefix=f"{prefixo}_", suffix=".mp3")
    os.close(fd)
    return Path(caminho)


def _novo_audio_temp(prefixo="vox_fala", extensao=".wav"):
    """Cria caminho de áudio temporário único com extensão personalizada."""
    fd, caminho = tempfile.mkstemp(prefix=f"{prefixo}_", suffix=extensao)
    os.close(fd)
    return Path(caminho)


def _normalizar_fallback_tts(texto):
    """Aplica a camada V2 (TTS Text Normalizer) no texto quando o
    SpeechPipeline não está disponível. Nunca falha: retorna o texto
    original se a normalização não puder ser aplicada."""
    if not texto or not texto.strip():
        return texto
    try:
        from tts.text_normalizer import normalize_for_tts
        return normalize_for_tts(texto)
    except Exception:
        return texto


def _tocar_e_limpar(mp3, parar_evento=None, stop_flag=None):
    """Toca via MCI e remove o arquivo temporário ao final (não deixa órfãos)."""
    try:
        _tocar_mci(str(mp3), parar_evento=parar_evento, stop_flag=stop_flag)
    finally:
        try:
            mp3.unlink(missing_ok=True)
        except Exception:
            pass


def _falar(texto, parar_evento=None, stop_flag=None):
    """Gera MP3 e toca via MCI. Otimizado para baixa latência com cache."""
    if not texto or not texto.strip():
        return

    # Tenta usar SpeechPipeline primeiro
    if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
        try:
            mp3 = _novo_mp3_temp("vox_fala")
            if _speech_pipeline.save(texto, str(mp3)):
                _tocar_e_limpar(mp3, parar_evento, stop_flag)
                return
            mp3.unlink(missing_ok=True)
        except Exception as e:
            print(f"[SpeechPipeline falhou: {e}]")

    # Cache: verifica se já tem áudio gerado para este texto
    import hashlib
    cache_key = hashlib.md5(texto.encode("utf-8")).hexdigest()[:12]
    cache_file = AUDIO_CACHE_DIR / f"{cache_key}.mp3"
    
    if cache_file.exists():
        # Áudio em cache — toca instantaneamente (0ms latência)
        try:
            _tocar_mci(str(cache_file), parar_evento=parar_evento, stop_flag=stop_flag)
            return
        except Exception:
            pass  # cache corrompido, gera de novo
    
    # Fallback: gera e toca diretamente via edge-tts
    mp3 = _novo_mp3_temp("vox_fala")
    try:
        asyncio.run(_tts_salvar(texto, str(mp3)))
    except Exception as e:
        print(f"[erro tts] {e}")
        mp3.unlink(missing_ok=True)
        # Fallback: tenta Piper TTS local
        try:
            from tts.piper_engine import PiperTTSEngine
            piper = PiperTTSEngine()
            if piper.available:
                wav_path = str(_novo_audio_temp("vox_fala", ".wav"))
                if piper.save_sync(texto, wav_path):
                    _tocar_e_limpar(wav_path, parar_evento, stop_flag)
                    return
                print("[piper falhou ao salvar WAV]")
        except Exception as pe:
            print(f"[erro piper] {pe}")
        return
    if not mp3.exists():
        mp3.unlink(missing_ok=True)
        return
    
    # Salva no cache para próximas vezes
    try:
        import shutil
        shutil.copy2(str(mp3), str(cache_file))
        # Limpa cache antigo se muito grande
        _limpar_cache_tts()
    except Exception:
        pass
    
    try:
        _tocar_e_limpar(mp3, parar_evento, stop_flag)
    except Exception as e:
        print(f"[erro play] {e}")
        try:
            mp3.unlink(missing_ok=True)
        except Exception:
            pass


async def _tts_stream_e_tocar(texto, caminho_mp3=None, parar_evento=None, stop_flag=None):
    """Gera áudio via streaming por sentença e toca cada uma assim que pronta.

    Divide o texto em sentenças (SentenceChunker) e sintetiza/toca cada
    sentença em sequência. Como a primeira sentença é curta, ela começa a
    tocar (via buffer) enquanto as demais ainda estão sendo geradas —
    reduzindo o time-to-first-audio.

    Cada sentença é finalizada antes da reprodução. Isso evita tocar um
    arquivo temporário enquanto ele ainda está sendo sobrescrito.
    """
    import edge_tts

    # Prepara texto: normaliza via camada V2 quando disponível
    texto = _normalizar_fallback_tts(texto)

    # Sentence chunking: divide em sentenças para time-to-first-audio menor
    chunks = [texto]
    try:
        if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
            c = _speech_pipeline.sentence_chunker.chunk_for_streaming(texto)
            if c:
                chunks = c
    except Exception:
        pass

    # Sintetiza e toca cada sentença em sequência (playback não sobreposto)
    for sentenca in chunks:
        if parar_evento and parar_evento.is_set():
            break

        # Prepara communicate para esta sentença
        try:
            from pronunciar_termos import marcar_para_tts
            texto_marcado = marcar_para_tts(sentenca, formato="ssml")
            if texto_marcado and '<lang' in str(texto_marcado):
                texto_ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">{texto_marcado}</speak>'
                communicate = edge_tts.Communicate(texto_ssml, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
            else:
                communicate = edge_tts.Communicate(sentenca, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
        except (ImportError, Exception):
            communicate = edge_tts.Communicate(sentenca, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)

        # Arquivo temporário único para esta sentença
        tmp = _novo_mp3_temp("vox_stream")

        # Coleta todos os chunks antes de tocar a sentença.
        audio_chunks = []

        async for chunk in communicate.stream():
            if parar_evento and parar_evento.is_set():
                break
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        if audio_chunks:
            with open(tmp, "wb") as f:
                for c in audio_chunks:
                    f.write(c)
            _tocar_mci(str(tmp), parar_evento=parar_evento, stop_flag=stop_flag)

        tmp.unlink(missing_ok=True)


async def _tts_salvar(texto, caminho):
    import edge_tts
    # Normaliza via camada V2 quando disponível
    texto = _normalizar_fallback_tts(texto)
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
    """Captura fala guiada por VAD e retorna ndarray float32 mono 16kHz.

    Com VOX_FORCE_FIXED=1 grava `seconds` secs fixos (modo deterministico p/
    testes); senao usa o mesmo motor de turno do dialogo (vad_captura: Silero
    streaming -> bloqueante -> fallback RMS). Se a captura VAD falhar, cai
    para a gravacao fixa original."""
    if os.environ.get("VOX_FORCE_FIXED", "0") != "1":
        try:
            from vad_captura import capturar_turno

            print("Ouvindo... (fale; o silencio encerra)")
            audio = capturar_turno()
            if audio is not None and audio.size > 0:
                return audio
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[vad indisponivel, gravacao fixa: {e}]")
    return _gravar_fixo(seconds)


def _gravar_fixo(seconds=RECORD_SECONDS):
    """Grava microfone por `seconds` segundos e retorna ndarray float32 mono
    16kHz. Usa o device escolhido pelo MicrofoneManager (benchmark real +
    hot-plug), capturando na taxa nativa quando necessario e fazendo downsample
    p/ 16kHz."""
    import sounddevice as sd
    import numpy as np
    try:
        import scipy.signal
        HAVE_SCIPY = True
    except ImportError:
        HAVE_SCIPY = False

    # Device selecionado dinamicamente (WDM-KS costuma só aceitar taxa nativa)
    try:
        from microfone_manager import MicrofoneManager
        mm = MicrofoneManager()
        DEVICE_ID = mm.device.selecionar()
        if DEVICE_ID is None:
            DEVICE_ID = 11
    except Exception:
        DEVICE_ID = 11

    try:
        import sounddevice as _sd
        RECORD_SR = int(_sd.query_devices(DEVICE_ID)["default_samplerate"])
    except Exception:
        RECORD_SR = 44100

    print(f"Ouvindo... (fale agora, {seconds:.0f}s)")
    try:
        n_samples = int(seconds * RECORD_SR)
        rec = sd.rec(n_samples, samplerate=RECORD_SR, channels=1, dtype="float32", device=DEVICE_ID)
        sd.wait()
        audio = rec.flatten()

        # Downsample RECORD_SR -> 16000
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
        print(f"[erro gravacao device {DEVICE_ID}: {e}] - tentando default")
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
        compression_ratio_threshold=2.4,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 800,
            "threshold": 0.5,
            "min_speech_duration_ms": 250,
        },
    )
    texto = ""
    descartados = 0
    for s in segments:
        # Filtro de alucinação por segmento: o Whisper é confiante em frases
        # fantasmas; o próprio sinal no_speech_prob/avg_logprob denuncia.
        try:
            if s.no_speech_prob is not None and s.no_speech_prob > WHISPER_MAX_NO_SPEECH:
                descartados += 1
                continue
            if s.avg_logprob is not None and s.avg_logprob < WHISPER_MIN_AVG_LOGPROB:
                descartados += 1
                continue
        except Exception:
            pass
        seg_text = s.text.strip()
        if seg_text and not _is_hallucination(seg_text):
            texto += seg_text + " "
            if partial_callback:
                partial_callback(texto.strip())
            print(f"\r{VOZ_COLOR}[voce (streaming)]{RESET} {texto.strip()}", flush=True, end="", file=sys.stderr)
        elif seg_text:
            descartados += 1
    if descartados:
        print(f"[whisper: {descartados} segmento(s) filtrados como alucinacao]", file=sys.stderr)
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


async def _falar_async(texto, parar_evento=None, stop_flag=None):
    """Versão async de _falar para uso dentro de event loop. Streaming: toca enquanto gera."""
    if not texto or not texto.strip():
        return

    # Tenta usar SpeechPipeline primeiro
    if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
        try:
            mp3 = _novo_mp3_temp("vox_fala")
            if _speech_pipeline.save(texto, str(mp3)):
                _tocar_e_limpar(mp3, parar_evento, stop_flag)
                return
            mp3.unlink(missing_ok=True)
        except Exception as e:
            print(f"[SpeechPipeline falhou: {e}]")

    # Streaming: gera áudio em chunks por sentença e toca conforme cada uma fica pronta
    try:
        await _tts_stream_e_tocar(texto, None, parar_evento, stop_flag)
    except Exception as e:
        print(f"[erro stream tts] {e}")
        # Fallback: método legado (batch)
        mp3_batch = _novo_mp3_temp("vox_fala")
        try:
            await _tts_salvar(texto, str(mp3_batch))
            _tocar_e_limpar(mp3_batch, parar_evento, stop_flag)
        except Exception as e2:
            print(f"[erro fallback tts] {e2}")
            mp3_batch.unlink(missing_ok=True)


async def cmd_falar_async(texto, interruptivel=False):
    import threading
    evento = threading.Event()
    await _falar_async(texto, parar_evento=evento, stop_flag=STOP_FLAG)
    print(f"[Falado {len(texto)} chars]" + (" (interruptivel)" if interruptivel else ""))


def cmd_falar(texto, interruptivel=False):
    import threading
    evento = threading.Event()
    _falar(texto, parar_evento=evento, stop_flag=STOP_FLAG)
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
