"""Captura de turno de fala com VAD — Silero streaming + fallback RMS.

Fonte unica da captura VAD do ecossistema (consolidada em 2026-09-06 a partir
do dialogo.py). Usado por:
  - dialogo.py         (modo voz contínuo: loop_vad / ativacao)
  - vox_audio.py       (STT / "ouvir" — encerra a gravação ao silenciar)

Uso:
  from vad_captura import capturar_turno
  audio = capturar_turno()   # ndarray float32 mono 16kHz, turno de fala

Variaveis de ambiente (iguais ao dialogo.py):
  VOX_THRESHOLD            threshold do Silero / RMS (default 0.5)
  VOX_SILENCIO             segundos de silencio p/ encerrar (default 0.8)
  VOX_MAX_FALA             segundos maximo de fala (default 15)
  VOX_VAD_MIN_SILENCE_MS   silencio min p/ VADIterator (default int(SILENCIO*1000))
"""

import os

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
THRESHOLD = float(os.environ.get("VOX_THRESHOLD", "0.5"))
SILENCIO = float(os.environ.get("VOX_SILENCIO", "0.8"))
MAX_FALA = float(os.environ.get("VOX_MAX_FALA", "15"))
VAD_MIN_SILENCE_MS = int(os.environ.get(
    "VOX_VAD_MIN_SILENCE_MS", str(int(SILENCIO * 1000))
))

# Instancia autoritativa do MicrofoneManager (device persistente + hot-plug).
# Múltiplas instancias coexistem (dialogo/vox_audio/módulo) sem duplicar o
# device escolhido: o gerenciador persiste a seleção em disco.
_mm = None


def _manager():
    global _mm
    if _mm is None:
        from microfone_manager import MicrofoneManager

        _mm = MicrofoneManager()
    return _mm


def rms(x):
    return float(np.sqrt(np.mean(x * x)))


def device_entrada():
    """Devolve o device de entrada escolhido pelo MicrofoneManager (benchmark
    real de abertura + persistência + hot-plug). Fallback: 1 (legado)."""
    try:
        dev = _manager().device.selecionar()
        if dev is not None:
            return dev
    except Exception:
        pass
    return 1


def taxa_nativa(device_id):
    """Taxa nativa do device (o WDM-KS só aceita a taxa nativa; o VAD faz
    resample para 16kHz depois)."""
    try:
        return int(sd.query_devices(device_id)["default_samplerate"])
    except Exception:
        return SAMPLE_RATE


def resample_para_16k(x, sr):
    """Downsample de `sr` para 16kHz via decimação linear (barata, suficiente
    para VAD/STT). Se já for 16k, devolve intacto."""
    if sr == SAMPLE_RATE or x.size == 0:
        return x
    step = sr / SAMPLE_RATE
    idx = np.arange(0, len(x), step).astype(int)
    idx = idx[idx < len(x)]
    return x[idx]


def rec_bloco_f32(dev, taxa, bloco):
    """Captura um bloco via sd.rec e devolve float32 mono 16kHz.

    Usa int16 (formato nativo estável do WDM-KS) e converte para float32,
    evitando corrupção observada com float32 no driver Realtek."""
    try:
        rec = sd.rec(bloco, samplerate=taxa, channels=1, dtype="int16", device=dev)
        sd.wait()
        x = rec.flatten().astype("float32") / 32768.0
        return resample_para_16k(x, taxa)
    except Exception:
        try:
            rec = sd.rec(bloco, samplerate=taxa, channels=1, dtype="float32", device=dev)
            sd.wait()
            return resample_para_16k(rec.flatten(), taxa)
        except Exception:
            return np.zeros(0, dtype="float32")


# --- Silero VAD streaming (oficial: silero-vad + VADIterator) ---

_silero = None


def carregar_silero():
    """Carrega o Silero VAD oficial (ONNX, CPU) e mantém instância global."""
    global _silero
    if _silero is not None:
        return _silero, True
    try:
        from silero_vad import load_silero_vad

        _silero = load_silero_vad(onnx=True)
        return _silero, True
    except Exception as e:
        print(f"[silero indisponivel: {e}]")
        _silero = False
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


# --- Feedback opcional (retrato/prints do chamador) ---

class Feedback:
    """Pontos de injeção para o chamador acompanhar a captura (RMS/prob e
    mensagens de estado). Callables vazios = silencioso."""

    def __init__(self, on_rms=None, on_mensagem=None):
        self.on_rms = on_rms or (lambda valor: None)
        self.on_mensagem = on_mensagem or (lambda texto: None)


def _alimentar_vad_bloqueante(vad, taxa, dev, estado, fb):
    """Captura por blocos bloqueantes (sd.rec int16) e alimenta o Silero VAD.

    Usado quando o device (ex.: WDM-KS) abre mas nao dispara callbacks de
    streaming. Captura blocos grandes (~1s) para amortizar o overhead de
    inicializacao do driver WDM-KS e processa em chunks de 512 (32ms).
    Retorna o turno de fala completo quando detectado."""
    CHUNK = 512
    bloco = max(int(taxa * 1.0), 44100)  # ~1s de áudio por captura
    buf = np.zeros(0, dtype="float32")
    while True:
        x = rec_bloco_f32(dev, taxa, bloco)
        if x.size == 0:
            continue
        buf = np.concatenate([buf, x])
        while len(buf) >= CHUNK:
            chunk = buf[:CHUNK]
            buf = buf[CHUNK:]
            turno = vad.push(chunk)
            prob = vad.ultima_prob
            fb.on_rms(prob)
            if prob >= 0.5 and not estado["mostrando"]:
                estado["mostrando"] = True
                fb.on_mensagem("[ouvindo...]")
            elif prob < 0.5 and estado["mostrando"]:
                estado["mostrando"] = False
                fb.on_mensagem("")
            if turno is not None:
                return turno


def capturar_turno(threshold=THRESHOLD, min_silence_ms=VAD_MIN_SILENCE_MS, feedback=None):
    """Escuta o microfone e devolve um turno de fala completo (float32 mono
    16kHz). Tenta o Silero VAD streaming; se o device nao entregar callbacks
    (ex.: WDM-KS), cai para captura bloqueante; sem Silero, cai para RMS.

    feedback (Feedback opcional): on_rms(valor) recebe prob/rms normalizado;
    on_mensagem(texto) recebe "[ouvindo...]" ao iniciar fala e "" ao silenciar.
    """
    fb = feedback or Feedback()
    model, ok = carregar_silero()
    if not ok:
        fb.on_mensagem("[vad fallback rms] fale (Ctrl+C p/ sair)")
        return capturar_turno_rms_fallback(threshold=threshold, feedback=fb)
    dev = device_entrada()
    taxa = taxa_nativa(dev)
    CHUNK = 512  # amostras a 16kHz exigidas pelo Silero
    result = {"turno": None, "n_callbacks": 0, "buf": np.zeros(0, dtype="float32")}
    estado = {"mostrando": False}

    def callback(indata, frames, time_info, status):
        nonlocal result, estado
        if result["turno"] is not None:
            return
        result["n_callbacks"] += 1
        x = indata[:, 0]
        if x.dtype == np.int16:
            x = x.astype("float32") / 32768.0
        if taxa != SAMPLE_RATE:
            x = resample_para_16k(x, taxa)
        result["buf"] = np.concatenate([result["buf"], x])
        while len(result["buf"]) >= CHUNK:
            chunk = result["buf"][:CHUNK]
            result["buf"] = result["buf"][CHUNK:]
            turno = result["vad"].push(chunk)
            prob = result["vad"].ultima_prob
            fb.on_rms(prob)
            if prob >= 0.5 and not estado["mostrando"]:
                estado["mostrando"] = True
                fb.on_mensagem("[ouvindo...]")
            elif prob < 0.5 and estado["mostrando"]:
                estado["mostrando"] = False
                fb.on_mensagem("")
            if turno is not None:
                result["turno"] = turno
                return

    vad = VadSileroStream(model, threshold=threshold, min_silence_ms=min_silence_ms)
    result["vad"] = vad

    import time

    try:
        # Modo 1: streaming com callback (rápido, baixa latência).
        # Se o device nao disparar callbacks em ~1s, cai para o modo bloqueante.
        stream = sd.InputStream(
            samplerate=taxa, channels=1, dtype="int16", callback=callback, device=dev
        )
        with stream:
            inicio = time.time()
            while result["turno"] is None:
                time.sleep(0.05)
                # sem nenhum callback em 1.2s => WDM-KS/streaming sem dados
                if result["n_callbacks"] == 0 and (time.time() - inicio) > 1.2:
                    break
        if result["turno"] is not None:
            return result["turno"]
        # streaming nao entregou dados -> modo bloqueante
        return _alimentar_vad_bloqueante(vad, taxa, dev, estado, fb)
    except KeyboardInterrupt:
        return np.zeros(0, dtype="float32")
    except Exception:
        # Modo 2: bloqueante por blocos (resiliente p/ WDM-KS sem callback)
        try:
            return _alimentar_vad_bloqueante(vad, taxa, dev, estado, fb)
        except KeyboardInterrupt:
            return np.zeros(0, dtype="float32")


def capturar_turno_rms_fallback(threshold=THRESHOLD, silencio=SILENCIO,
                                max_fala=MAX_FALA, feedback=None):
    """Fallback por RMS caso o Silero nao carregue. Encerra quando a voz para
    por `silencio` segundos ou atinge `max_fala` segundos."""
    fb = feedback or Feedback()
    limiar = max(threshold * 0.02, 0.02)
    consec = 0
    falando = False
    silencio_atual = 0.0
    frames = []
    total = 0.0
    dev = device_entrada()
    taxa = taxa_nativa(dev)
    bloco = int(taxa * 0.1)
    while True:
        x = rec_bloco_f32(dev, taxa, bloco)
        if x.size == 0:
            continue
        rms_atual = rms(x)
        fb.on_rms(rms_atual / 0.08)
        voz = rms_atual > limiar
        if not falando:
            if voz:
                consec += 1
                if consec >= 3:
                    falando = True
                    silencio_atual = 0.0
                    frames = [x]
                    total = 0.1
            else:
                consec = 0
        else:
            frames.append(x)
            total += 0.1
            if not voz:
                silencio_atual += 0.1
                if silencio_atual >= silencio:
                    break
            else:
                silencio_atual = 0.0
            if total >= max_fala:
                break
    return np.concatenate(frames) if frames else np.zeros(0, dtype="float32")