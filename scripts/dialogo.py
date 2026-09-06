"""Dialogo por voz no PC — fale naturalmente, Jarvis ouve, responde e executa.

Modos de ativacao:
  vad      -> maos-livres: detecta fala pelo volume, processa quando silencia
  push     -> segure CTRL para falar, solte para enviar
  ativacao -> diga "Jarvis" para acordar, depois fale o comando
              ("valeu"/"tchau"/"pode dormir" para dormir de novo)

Uso:
  python scripts/dialogo.py [--modo vad|push|ativacao] [--model base]
  python scripts/dialogo.py --texto "fale uma frase direto (sem microfone)"

Variaveis de ambiente (opcionais):
  VOX_THRESHOLD   RMS p/ considerar voz (default 0.02)
  VOX_SILENCIO    segundos de silencio p/ encerrar fala (default 1.2)
  VOX_MAX_FALA    segundos maximo de fala (default 15; aplicado em vad_captura)
  VOX_VAD_MIN_SILENCE_MS  silencio min p/ VADIterator (default int(SILENCIO*1000))
  VOX_WHISPER_MODEL  modelo whisper (default base)
"""

import argparse
import asyncio
import base64
import ctypes
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from vox_audio import SAMPLE_RATE, _stt_whisper, _stt_google, _tocar_mci, _novo_mp3_temp  # noqa: E402
from jarvis_bridge import (  # noqa: E402
    Cliente,
    briefing_espontaneo,
    caminho_rapido,
    gerar_audio,
    gerar_status_natural,
    normalizar_hora_display,
)
from microfone_manager import MicrofoneManager  # noqa: E402

# Captura VAD compartilhada (fonte única): streaming Silero + fallback RMS.
# Consolidada aqui a partir das funções locais (vad_captura.py, 2026-09-06).
# O vox_audio (STT) usa o MESMO módulo — sem caminhos paralelos.
from vad_captura import Feedback, capturar_turno  # noqa: E402
from vad_captura import rms as _rms  # noqa: E402
from vad_captura import device_entrada as _device_entrada  # noqa: E402
from vad_captura import taxa_nativa as _taxa_nativa  # noqa: E402
from vad_captura import resample_para_16k as _resample_para_16k  # noqa: E402
from vad_captura import rec_bloco_f32 as _rec_bloco_f32  # noqa: E402

# Gestor simbiótico de microfone (device persistente, hot-plug, enhancement,
# wake word, bridge sync e health check) — módulo autoritativo do ecossistema.
manager = MicrofoneManager()

# Autopsia: falhas nativas (access violation em PortAudio/torch) matam o
# processo sem traceback Python; o faulthandler registra pilha crua.
try:
    import faulthandler as _faulthandler

    _crash_log = open(SCRIPTS.parent / "runtime" / "dialogo_crash.log", "a",
                      buffering=1, encoding="utf-8")
    _faulthandler.enable(file=_crash_log)
except Exception:
    pass

THRESHOLD = float(os.environ.get("VOX_THRESHOLD", "0.5"))
SILENCIO = float(os.environ.get("VOX_SILENCIO", "0.8"))
MAX_FALA = float(os.environ.get("VOX_MAX_FALA", "15"))
VAD_MIN_SILENCE_MS = int(os.environ.get("VOX_VAD_MIN_SILENCE_MS", str(int(SILENCIO * 1000))))

FALAR_COLOR = "\033[92m"
VOZ_COLOR = "\033[96m"
RESET = "\033[0m"

SLEEP_FRASES = re.compile(
    r"^(valeu|tchau|adeus|ate mais|pode dormir|va dormir|dorme|encerra|pode ir|chega por hoje|obrigado|obrigada|flw)\b",
    re.IGNORECASE,
)

# Flag global de parada (mesmo arquivo do widget/servicos)
STOP_FLAG = SCRIPTS.parent / "runtime" / "parar_fala.flag"

# --- Detecção de eco do TTS (padrão isair/jarvis) -------------------------
# Guarda a última fala do Jarvis (texto exibido). Se o microfone capturar a
# própria fala vazando dos alto-falantes ao retomar a escuta, a transcrição
# casa com esta referência e é descartada como eco (não vira novo comando).
_ULTIMA_FALA_JARVIS = [""]
_ECO_SIMILARIDADE = float(os.environ.get("VOX_ECO_SIMILARIDADE", "0.8"))
_ULTIMO_FALADO_TS = [0.0]
_ECO_JANELA_S = float(os.environ.get("VOX_ECO_JANELA_S", "8.0"))


def _normalizar_eco(texto):
    """Normaliza texto p/ comparação de eco: minúsculas, sem pontuação, sem espaços repetidos."""
    t = re.sub(r"[^\w\sáéíóúâêôãõçàü]", " ", texto, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip().lower()


def _registrar_fala_jarvis(texto):
    """Registra a fala do Jarvis como referência anti-eco."""
    if not texto:
        return
    norm = _normalizar_eco(texto)
    if norm:
        _ULTIMA_FALA_JARVIS[0] = norm
        _ULTIMO_FALADO_TS[0] = time.time()


def _parece_eco(texto):
    """True se a transcrição ouvida é (quase) a fala que o Jarvis acabou de emitir."""
    if not texto:
        return False
    norm = _normalizar_eco(texto)
    if not norm or not _ULTIMA_FALA_JARVIS[0]:
        return False
    if time.time() - _ULTIMO_FALADO_TS[0] > _ECO_JANELA_S:
        return False
    try:
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, norm, _ULTIMA_FALA_JARVIS[0]).ratio()
    except Exception:
        return False
    return ratio >= _ECO_SIMILARIDADE


# --- Juiz de intenção (padrão isair/jarvis) -------------------------------
# Um juiz (LLM pequeno opcional, fallback determinístico sempre ativo) decide
# o que o usuário quis dizer: comando, pergunta, saudação, interrupção ou eco.
# Interrupções ("para", "chega") não viram pergunta; saudações recebem resposta
# curta; o resto segue para o responder normal.
_INTENT_LLM_ENABLED = os.environ.get("VOX_INTENT_LLM", "0") == "1"
_INTERRUPCAO = re.compile(
    r"^(?:para|pare|pára|chega|cala a boca|cala-se|cala\s+boca|já chega|sil[eê]ncio|basta|deixa pra l[áa]|deixa para l[áa])\b",
    re.IGNORECASE,
)
_SAUDACAO = re.compile(
    r"^(?:oi|ola|olá|e a[ií]|eai|bom dia|boa tarde|boa noite|hey|ei|opa|fala a[ií]|falai|bom dia jarvis)\b",
    re.IGNORECASE,
)


def _juiz_intencao(texto):
    """Classifica a intenção da fala ouvida. Retorna {"intencao", "query"}.

    intencao: comando|pergunta|saudacao|interrupcao|eco|vazio|conversa
    query: texto limpo (sem "jarvis", sem saudações) p/ processamento.
    """
    if not texto or not texto.strip():
        return {"intencao": "vazio", "query": ""}
    t = texto.strip()
    tl = t.lower().strip()

    # 1) Juiz via LLM pequeno (opcional; não bloqueia se indisponível)
    if _INTENT_LLM_ENABLED:
        try:
            from llm_caller import call_llm_json
            r = call_llm_json(
                prompt=(
                    "Classifique a intenção desta fala ouvida por um assistente de voz.\n"
                    f"Fala: \"{t}\"\n"
                    "Responda JSON: "
                    '{"intencao": "comando|pergunta|saudacao|interrupcao|eco|conversa", '
                    '"query": "texto limpo sem a palavra jarvis e sem saudações"}'
                ),
                system="Assistente de voz. Responda APENAS JSON.",
                max_tokens=80,
                temperature=0.0,
                timeout=6,
            )
            if isinstance(r, dict) and "intencao" in r:
                q = (r.get("query") or t).strip()
                return {"intencao": r["intencao"], "query": q}
        except Exception:
            pass

    # 2) Fallback determinístico (nunca falha, custo zero)
    if _INTERRUPCAO.match(tl):
        return {"intencao": "interrupcao", "query": ""}
    if _parece_eco(t):
        return {"intencao": "eco", "query": ""}
    if _SAUDACAO.match(tl) and len(t.split()) <= 6:
        return {"intencao": "saudacao", "query": _separar_jarvis(t)}
    if re.match(
        r"^(abra|abre|execute|executa|rode|roda|inicie|inicia|ligue|liga|desligue|desliga|"
        r"toque|toca|envie|envia|busque|busca|procure|procura)\b",
        tl,
    ):
        return {"intencao": "comando", "query": t}
    return {"intencao": "pergunta", "query": _separar_jarvis(t)}


def _ctrl_pressionado():
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000)
    except Exception:
        return False


def _beep():
    try:
        print("\a", end="", flush=True)
    except Exception:
        pass


# --- Retrato vivo: estado do diálogo p/ o widget Edge ler em tempo real ---

RETRATO = SCRIPTS.parent / "runtime" / "dialogo_vivo.json"
VIVO = {"estado": "iniciando", "voce": "", "erro": "", "quando": 0.0}
RMS_ATUAL = [0.0]


def _retrato_gravar():
    d = dict(VIVO)
    d["rms"] = round(RMS_ATUAL[0], 3)
    try:
        tmp = RETRATO.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, RETRATO)
    except Exception:
        pass


def _retrato_estado(estado=None, voce=None, erro=None):
    """Transição de estado: atualiza e grava na hora (eventos raros)."""
    if estado is not None:
        VIVO["estado"] = estado
    if voce is not None:
        VIVO["voce"] = str(voce)[:200]
    if erro is not None:
        VIVO["erro"] = str(erro)[:300]
    VIVO["quando"] = time.time()
    _retrato_gravar()
    try:
        from atividade_emit import emitir
        emitir("fala", 0.95 if VIVO["estado"] == "falando" else 0.0)
    except Exception:
        pass


def _retrato_rms(valor):
    """Nível do mic em 0..1 (só memória; o I/O fica no loop de fundo)."""
    RMS_ATUAL[0] = max(0.0, min(1.0, float(valor)))


def _retrato_loop():
    while True:
        _retrato_gravar()
        time.sleep(0.4)


# --- Captura VAD delegada ao módulo compartilhado (vad_captura.py, fonte única).
# O dialogo e o vox_audio (STT) usam o MESMO motor de turno de fala: streaming
# Silero -> captura bloqueante -> fallback RMS. Nada de caminhos paralelos.

def capturar_vad():
    """Escuta o microfone e devolve um turno de fala completo (float32 mono
    16kHz). Delega ao módulo vad_captura (mesmo motor do vox_audio STT):
    streaming com callback (rápido); falhando, captura bloqueante por blocos
    (WDM-KS); Silero ausente, fallback RMS. Feedback visual/local preservado."""
    print(f"{VOZ_COLOR}[escutando] fale naturalmente (Ctrl+C p/ sair){RESET}", flush=True)
    _beep()

    def on_mensagem(texto):
        if texto:
            print(f"{VOZ_COLOR}{texto}{RESET}", flush=True)

    return capturar_turno(
        threshold=THRESHOLD,
        min_silence_ms=VAD_MIN_SILENCE_MS,
        feedback=Feedback(on_rms=_retrato_rms, on_mensagem=on_mensagem),
    )


def capturar_push():
    """Segure CTRL para falar; solte para enviar."""
    print(f"{VOZ_COLOR}[push] segure CTRL para falar (ESC/Ctrl+C para sair){RESET}", flush=True)
    while not _ctrl_pressionado():
        import time
        time.sleep(0.05)
    _beep()
    dev = _device_entrada()
    taxa = _taxa_nativa(dev)
    bloco = int(taxa * 0.1)
    frames = []
    while _ctrl_pressionado():
        x = _rec_bloco_f32(dev, taxa, bloco)
        if x.size == 0:
            continue
        _retrato_rms(_rms(x) / 0.08)
        frames.append(x)
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
    # Audio enhancement (noise gate + AGC) antes do STT
    try:
        audio = manager.enhancer.processar(audio)
    except Exception:
        pass
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
    # Anti-eco: se o microfone capturou a própria fala do Jarvis (vazando dos
    # alto-falantes ao retomar a escuta), descarta como eco — não vira comando.
    if _parece_eco(texto):
        print(f"{VOZ_COLOR}[eco do jarvis detectado, ignorado]{RESET} '{texto[:40]}'", flush=True)
        return ""
    print(f"{VOZ_COLOR}[voce ({fonte})]{RESET} {texto}", flush=True)
    return texto


def _pausa_total_ativa():
    """True quando o botão Pausar do widget está ativo: todo áudio de saída do
    diálogo (gerar_audio/tocar_base64) é silenciado; Jarvis continua ouvindo e
    responde apenas em texto até o usuário retomar."""
    try:
        controle = SCRIPTS.parent / "runtime" / "narracao_estado.json"
        if controle.exists():
            data = json.loads(controle.read_text(encoding="utf-8"))
            return bool(data.get("pausa_total", False))
    except Exception:
        pass
    return False


def tocar_base64(b64, parar_evento=None):
    if not b64:
        return
    if _pausa_total_ativa():
        print(f"{FALAR_COLOR}[pausa total — áudio suprimido]{RESET}", flush=True)
        return
    mp3 = _novo_mp3_temp("vox_dialogo")
    try:
        mp3.write_bytes(base64.b64decode(b64))
        _tocar_mci(str(mp3), parar_evento=parar_evento, stop_flag=STOP_FLAG)
    except Exception as e:
        print(f"[erro play] {e}")
    finally:
        try:
            mp3.unlink(missing_ok=True)
        except Exception:
            pass


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
    a fala do Jarvis, dispara a parada (barge-in por voz).

    Anti-eco: os ~0.8s iniciais calibram o nivel do proprio audio dos
    alto-falantes vazando no microfone; o limiar efetivo passa a ser esse
    eco ampliado, ou a voz ficaria sempre abaixo do corte."""
    if limiar_rms is None:
        limiar_rms = float(os.environ.get("VOX_BARGEIN_RMS", "0.07"))
    dev = _device_entrada()
    taxa = _taxa_nativa(dev)
    bloco = int(taxa * 0.1)
    amostras_eco = []
    for _ in range(8):  # calibracao ~0.8s (tambem funciona como carencia inicial)
        if parar_evento.is_set():
            return
        try:
            x = _rec_bloco_f32(dev, taxa, bloco)
            if x.size:
                amostras_eco.append(_rms(x))
        except Exception:
            pass
    eco = min(amostras_eco) if amostras_eco else 0.0
    limiar = max(limiar_rms, eco * 2.5 + 0.01)
    consec = 0
    while not parar_evento.is_set():
        try:
            x = _rec_bloco_f32(dev, taxa, bloco)
            if x.size == 0:
                continue
            rms = _rms(x)
            if rms > limiar:
                consec += 1
                if consec >= 3:  # ~300ms de fala continua = barge-in
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
    if _pausa_total_ativa():
        print(f"{FALAR_COLOR}[pausa total — fala suprimida]{RESET}", flush=True)
        return False
    _retrato_estado("falando")
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
    _retrato_estado("ouvindo", erro="")
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
            _retrato_estado(erro=f"processamento: {e}")
            r = f"Erro no processamento: {e}"
    if not r:
        r = "Não consegui gerar uma resposta."
    r_tela = normalizar_hora_display(r)
    _registrar_fala_jarvis(r_tela)
    print(f"{FALAR_COLOR}[jarvis]{RESET} {r_tela}", flush=True)
    # Pausa total: responde apenas em texto (sem gerar nem tocar áudio)
    if _pausa_total_ativa():
        _retrato_estado("ouvindo", erro="")
        return
    try:
        audio = await gerar_audio(r_tela)
    except Exception as e:
        print(f"[tts: {e}]")
        _retrato_estado(erro=f"tts: {e}")
        audio = ""
    _retrato_estado("falando")
    if interrompivel:
        falar_com_bargein(audio)
    else:
        tocar_base64(audio)
    _retrato_estado("ouvindo", erro="")


def _separar_jarvis(texto):
    m = re.match(
        r"^\s*(?:hey|ei|opa|ok|tudo bem)?\s*jarvis\s*[,:.]?\s*(.*)$",
        texto,
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else texto


async def loop_vad(cliente):
    while True:
        manager.marcar_listening()
        _retrato_estado("ouvindo")
        try:
            audio = capturar_vad()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            # mic ausente/morto: mostra o motivo no Edge em vez de morrer calado
            _retrato_estado("erro", erro=f"{type(e).__name__}: {e}")
            await asyncio.sleep(3)
            continue
        if audio.size == 0:
            continue
        manager.marcar_processing()
        manager.marcar_atividade()
        _retrato_estado("pensando")
        texto = transcrever(audio)
        if not texto:
            continue
        _retrato_estado(voce=texto)
        # Juiz de intenção: interrupção não vira pergunta
        intencao = _juiz_intencao(texto).get("intencao")
        if intencao == "interrupcao":
            print(f"{FALAR_COLOR}[jarvis]{RESET} Entendido, parando.", flush=True)
            falar_com_bargein(await gerar_audio("Entendido, parando."))
            continue
        if intencao == "eco":
            continue
        # pausa o mic enquanto o Jarvis responde (evita eco)
        try:
            manager.marcar_paused_tts()
        except Exception:
            pass
        await responder(cliente, texto)
        manager.marcar_atividade()
        try:
            manager.marcar_listening()
        except Exception:
            pass


async def loop_push(cliente):
    while True:
        manager.marcar_listening()
        audio = capturar_push()
        if audio.size == 0:
            continue
        manager.marcar_processing()
        manager.marcar_atividade()
        texto = transcrever(audio)
        if not texto:
            continue
        try:
            manager.marcar_paused_tts()
        except Exception:
            pass
        await responder(cliente, texto)
        manager.marcar_atividade()
        try:
            manager.marcar_listening()
        except Exception:
            pass


def _capturar_com_wake_word():
    """Escuta continuamente por wake word real (Porcupine). Quando detecta,
    beep e retorna True. Fallback interno: se o Porcupine nao estiver
    disponivel, retorna False (o loop usa VAD+regex)."""
    if not manager.wake.disponivel:
        return False
    try:
        import sounddevice as sd
        import numpy as np
        dev = _device_entrada()
        taxa = _taxa_nativa(dev)
        frame_len = manager.wake._porcupine.frame_length
        detectado = {"v": False}
        buf_holder = [np.zeros(0, dtype="float32")]

        def callback(indata, frames, time_info, status):
            if detectado["v"]:
                return
            x = indata[:, 0]
            if taxa != SAMPLE_RATE:
                x = _resample_para_16k(x, taxa)
            acc = buf_holder[0]
            acc = np.concatenate([acc, x])
            while len(acc) >= frame_len:
                chunk = acc[:frame_len]
                acc = acc[frame_len:]
                pcm = (chunk * 32767).astype(np.int16)
                if manager.wake.detectar(pcm):
                    detectado["v"] = True
                    return
            buf_holder[0] = acc

        with sd.InputStream(
            samplerate=taxa, channels=1, dtype="float32",
            callback=callback, device=dev,
        ):
            while not detectado["v"]:
                time.sleep(0.05)
        _beep()
        return True
    except Exception as e:
        print(f"[wake] captura falhou ({e}); usando VAD+regex")
        return False


async def loop_ativacao(cliente):
    acordado = False
    while True:
        manager.marcar_listening()
        # Se houver wake word real (Porcupine), acorda direto pela palavra
        if not acordado and manager.wake.disponivel:
            if _capturar_com_wake_word():
                acordado = True
                print(f"{FALAR_COLOR}[jarvis]{RESET} Sim, senhor?", flush=True)
                falar_com_bargein(await gerar_audio("Sim, senhor?"))
                continue
        audio = capturar_vad()
        if audio.size == 0:
            continue
        manager.marcar_processing()
        manager.marcar_atividade()
        texto = transcrever(audio)
        if not texto:
            continue
        t = texto.strip().lower()
        if not acordado:
            if re.search(r"\bjarvis\b", texto, re.IGNORECASE):
                comando = _separar_jarvis(texto)
                if comando:
                    acordado = True
                    try:
                        manager.marcar_paused_tts()
                    except Exception:
                        pass
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
        try:
            manager.marcar_paused_tts()
        except Exception:
            pass
        await responder(cliente, texto)


async def saudar_inicio(cliente):
    """Saudação criativa via LLM — mesmo núcleo do app de celular (jarvis_bridge.saudar)."""
    _retrato_estado("pensando")
    status = gerar_status_natural()
    try:
        extra = briefing_espontaneo()
    except Exception:
        extra = ""
    # Catch me up: o que aconteceu enquanto o usuário esteve fora (heardlabs/heard)
    try:
        from runtime_state import gerar_catch_up, load_state
        catch = gerar_catch_up(load_state())
        if catch:
            extra = (extra + " " + catch).strip()
    except Exception:
        pass
    saudacao = ""
    try:
        saudacao = await cliente.saudar(extra, status)
    except Exception as e:
        print(f"[saudar: {e}]")
    if not saudacao:
        import random
        import datetime
        hora = datetime.datetime.now().hour
        if 5 <= hora < 12:
            abridores = ["Bom dia", "Bom dia, senhor", "Bons dias"]
        elif 12 <= hora < 18:
            abridores = ["Boa tarde", "Boa tarde, senhor", "Boa tarde por aqui"]
        elif 18 <= hora < 24:
            abridores = ["Boa noite", "Boa noite, senhor", "Noite agradável, não é?"]
        else:
            abridores = ["Que dia é hoje a esta hora", "Madrugada firme por aqui", "Boa madrugada"]
        fechos = [
            "O que vamos fazer?", "O que precisa?", "Diga o que você precisa.",
            "Pronto para começar?", "Estou aqui. Só chamar."
        ]
        saudacao = f"{random.choice(abridores)}! {extra}{status}{random.choice(fechos)}"
    saudacao_tela = normalizar_hora_display(saudacao)
    _registrar_fala_jarvis(saudacao_tela)
    print(f"{FALAR_COLOR}[jarvis]{RESET} {saudacao_tela}", flush=True)
    if _pausa_total_ativa():
        _retrato_estado("ouvindo", erro="")
        return
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

    # Inicia monitor de hot-plug do MicrofoneManager (device robusto)
    try:
        manager.device.iniciar_monitor()
    except Exception as e:
        print(f"[microfone] monitor hot-plug falhou: {e}")

    print(f"Modo dialogo ativo ({args.modo}). Ctrl+C para encerrar.", flush=True)
    threading.Thread(target=_retrato_loop, daemon=True).start()
    _retrato_estado("iniciando", voce="", erro="")
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
    finally:
        try:
            manager.device.parar_monitor()
        except Exception:
            pass
        try:
            manager.marcar_off()
        except Exception:
            pass
        _retrato_estado("parado")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado.")
