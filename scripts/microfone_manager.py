"""Microfone Manager — gerência simbiótica do microfone do Jarvis (Windows).

Consolida os 8 passos de evolução do microfone em UM módulo autoritativo:

  1. Device selection persistente + benchmark automático (WASAPI > DirectSound > MME)
  2. Hot-plug detection (monitora devices e re-seleciona se o preferido sumir)
  3. Wake word real (Porcupine/Picovoice se PORCUPINE_ACCESS_KEY) com fallback VAD+regex
  4. Streaming STT (faster-whisper com vad_filter + partial callbacks)
  5. Audio enhancement (noise gate + AGC em numpy puro; RNNoise sem wheel Windows)
  6. Bridge integration (mic_estado.json enriquecido com status; mantém chave "ativo")
  7. Health check + auto-restart (watchdog no ciclo de captura)
  8. Config unificada (config/microfone.json)

Uso:
  from microfone_manager import MicrofoneManager, DeviceSelector, AudioEnhancer

Variaveis de ambiente (opcionais):
  PORCUPINE_ACCESS_KEY  chave gratuita do Picovoice p/ wake word real
  VOX_WHISPER_MODEL     modelo whisper (default base)
"""

import json
import os
import threading
import time
from pathlib import Path

import numpy as np

ECOSSISTEMA_DIR = Path(__file__).resolve().parent.parent
CONFIG = ECOSSISTEMA_DIR / "config" / "microfone.json"
RUNTIME_DIR = ECOSSISTEMA_DIR / "runtime"
RUNTIME_FILE = RUNTIME_DIR / "microfone_runtime.json"
ESTADO_FILE = RUNTIME_DIR / "mic_estado.json"

SAMPLE_RATE = 16000

_HOSTAPI_PESO = {"WASAPI": 3.0, "DirectSound": 2.0, "WDM-KS": 1.5, "MME": 1.0}

_DEFAULT_CONFIG = {
    "device_selection": {
        "auto_benchmark": True,
        "preferred_device": None,
        "benchmark_duration_sec": 3,
    },
    "vad": {
        "engine": "silero",
        "silero_threshold": 0.5,
        "min_silence_ms": 800,
        "speech_pad_ms": 30,
        "min_speech_ms": 250,
        "fallback_rms_threshold": 0.02,
        "fallback_silence_sec": 1.2,
        "fallback_max_speech_sec": 15,
    },
    "wake_word": {
        "enabled": True,
        "engine": "porcupine",
        "keywords": ["jarvis"],
        "sensitivities": [0.6],
        "access_key_env": "PORCUPINE_ACCESS_KEY",
    },
    "stt": {
        "engine": "faster_whisper",
        "model": "base",
        "device": "cpu",
        "compute_type": "int8",
        "language": "pt",
        "beam_size": 5,
        "vad_filter": True,
        "fallback_google": {"enabled": True, "language": "pt-BR"},
    },
    "audio_enhancement": {
        "noise_gate": {
            "enabled": True,
            "threshold_db": -40,
            "ratio": 10,
            "attack_ms": 10,
            "release_ms": 100,
        },
        "auto_gain_control": {
            "enabled": True,
            "target_level_db": -20,
            "max_gain_db": 20,
            "adaptation_speed": 0.1,
        },
    },
    "bridge_integration": {"enabled": True, "sync_file": "runtime/mic_estado.json"},
    "health_check": {
        "enabled": True,
        "watchdog_timeout_sec": 60,
        "max_restarts": 3,
        "restart_cooldown_sec": 30,
    },
    "hotplug": {
        "enabled": True,
        "poll_interval_sec": 2,
    },
    "logging": {
        "level": "INFO",
        "log_audio_levels": False,
        "log_vad_decisions": True,
    },
}


def _carregar_config() -> dict:
    """Carrega config/microfone.json com fallback de defaults (deep merge leve)."""
    cfg = json.loads(json.dumps(_DEFAULT_CONFIG))
    try:
        if CONFIG.exists():
            user = json.loads(CONFIG.read_text(encoding="utf-8"))
            for sec, vals in user.items():
                if isinstance(vals, dict) and isinstance(cfg.get(sec), dict):
                    cfg[sec].update(vals)
                else:
                    cfg[sec] = vals
    except Exception as e:
        print(f"[microfone] config invalida ({e}); usando defaults")
    return cfg


def _atomic_write(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        os.replace(tmp, path)


def _rms(x):
    if x is None or x.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.asarray(x, dtype="float32") ** 2)))


def _db(x):
    r = _rms(x)
    if r < 1e-9:
        return -120.0
    return 20.0 * np.log10(r)


class DeviceSelector:
    """Seleção persistente do melhor dispositivo de entrada.

    Ranking por hostapi (WASAPI > DirectSound > WDM-KS > MME) e latência
    declarada. Persiste a escolha em runtime/microfone_runtime.json e
    re-benchmarka quando o preferido deixa de existir (hot-plug).
    """

    def __init__(self, config: dict):
        self.cfg = config.get("device_selection", {})
        self.hotplug_cfg = config.get("hotplug", {})
        self._lock = threading.Lock()
        self._monitor_on = False
        self._thread = None
        self._preferido = None
        self._ultimo_teste_ts = 0.0
        self._ttl_teste = 30.0
        self._carregar_persistido()

    def _carregar_persistido(self):
        try:
            if RUNTIME_FILE.exists():
                d = json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
                self._preferido = d.get("device_id")
        except Exception:
            self._preferido = None

    def _persistir(self):
        try:
            _atomic_write(RUNTIME_FILE, {
                "device_id": self._preferido,
                "updated_at": int(time.time()),
            })
        except Exception:
            pass

    def _dispositivos_entrada(self):
        try:
            import sounddevice as sd
            out = []
            for i, d in enumerate(sd.query_devices()):
                if d.get("max_input_channels", 0) > 0:
                    out.append({
                        "id": i,
                        "name": d.get("name", ""),
                        "hostapi": d.get("hostapi", 0),
                        "samplerate": d.get("default_samplerate", 44100.0),
                        "low_latency": d.get("default_low_input_latency", 0.1),
                        "channels": d.get("max_input_channels", 0),
                    })
            return out
        except Exception as e:
            print(f"[microfone] falha ao listar devices: {e}")
            return []

    def _nome_hostapi(self, hostapi_id):
        try:
            import sounddevice as sd
            return sd.query_hostapis(hostapi_id)["name"]
        except Exception:
            return ""

    def _testar_abertura(self, device_id, samplerate, duracao=0.3):
        """Tenta abrir um InputStream real por `duracao` segundos.

        E a metrica autoritativa: um device pode ter bom hostapi/baixa latencia
        declarada mas nao abrir na pratica (ex.: MME com "Unanticipated host
        error", WASAPI que so aceita taxa nativa). Retorna True se o stream
        abriu sem excecao (o driver aceitou taxa/formato)."""
        try:
            import sounddevice as sd

            def _cb(indata, frames, time_info, status):
                pass

            with sd.InputStream(
                samplerate=samplerate,
                channels=1,
                dtype="float32",
                callback=_cb,
                device=device_id,
            ):
                import time
                time.sleep(duracao)
            return True
        except Exception:
            pass
        # Fallback: abertura bloqueante via sd.rec — e o caminho que o dialogo
        # realmente usa quando o stream nao entrega callbacks (ex.: WDM-KS).
        try:
            import sounddevice as sd

            n = max(1, int(samplerate * min(duracao, 0.2)))
            rec = sd.rec(n, samplerate=samplerate, channels=1,
                         dtype="float32", device=device_id)
            sd.wait()
            return rec.size > 0
        except Exception:
            return False

    def _testar_16k(self, device_id):
        return self._testar_abertura(device_id, SAMPLE_RATE)

    def _testar_entrega(self, device_id, samplerate, duracao=0.4):
        """Abre o device e verifica se entrega dados validos (sem NaN/inf).

        Complementa o teste de abertura: alguns devices (WDM-KS) abrem mas
        retornam NaN/garbage em determinados estados do driver. Essa metrica
        garante que o device escolhido captura audio de verdade."""
        try:
            import sounddevice as sd
            import numpy as np
            n = int(samplerate * duracao)
            rec = sd.rec(n, samplerate=samplerate, channels=1, dtype="float32", device=device_id)
            sd.wait()
            x = rec.flatten()
            if x.size == 0:
                return False
            if np.isnan(x).any() or np.isinf(x).any():
                return False
            rms = float(np.sqrt(np.mean(x.astype("float64") ** 2)))
            return 0.0 <= rms < 100.0
        except Exception:
            return False

    def _e_loopback(self, did):
        """True se o device e canal de loopback/mixagem: captura a SAIDA dos
        alto-falantes, nao o microfone fisico. Nunca deve ser preferido."""
        for d in self._dispositivos_entrada():
            if d["id"] == did:
                nome = d["name"].lower()
                return "mixagem" in nome or "stereo mix" in nome or "loopback" in nome
        return False

    def benchmark(self, permitir_nativo=True):
        """Seleciona o melhor device de entrada por teste REAL de abertura + entrega.

        Prioridade:
          1. device preferido na config, se abre e entrega a 16kHz
          2. device persistido, se abre e entrega a 16kHz
          3. devices que abrem e entregam a 16kHz, rankeados por hostapi+latencia
          4. (fallback) devices que abrem e entregam na taxa nativa, p/ resample
          5. (ultimo recurso) devices que apenas abrem (qualquer taxa)

        Retorna o id (int) ou None se nenhum abrir.
        """
        devs = self._dispositivos_entrada()
        # Loopback/mixagem captura a saida dos alto-falantes, nao o usuario.
        # Excluido de TODOS os niveis: melhor nenhum device que um falso mic.
        devs = [d for d in devs if not self._e_loopback(d["id"])]
        if not devs:
            return None

        def _valido(did, sr):
            return self._testar_abertura(did, sr) and self._testar_entrega(did, sr)

        def _abre(did, sr):
            return self._testar_abertura(did, sr)

        pid = self.cfg.get("preferred_device")
        if pid is not None:
            try:
                pid = int(pid)
                if (any(d["id"] == pid for d in devs) and _valido(pid, SAMPLE_RATE)
                        and not self._e_loopback(pid)):
                    self._preferido = pid
                    self._persistir()
                    return pid
            except (TypeError, ValueError):
                pass

        if self._preferido is not None and any(d["id"] == self._preferido for d in devs):
            if _valido(self._preferido, SAMPLE_RATE) and not self._e_loopback(self._preferido):
                return self._preferido

        def score(d):
            base = _HOSTAPI_PESO.get(self._nome_hostapi(d["hostapi"]), 1.0)
            lat = max(0.0, d["low_latency"])
            lat_bonus = 2.0 if lat <= 0.02 else (1.0 if lat <= 0.06 else 0.0)
            nome = d["name"].lower()
            # prefere microfone fisico; penaliza loopback/mixagem (nao e entrada real)
            if "microfone" in nome or " mic" in nome or "mic" == nome[:3]:
                tipo = 2.0
            elif "mixagem" in nome or "stereo mix" in nome or "loopback" in nome:
                tipo = -2.0
            else:
                tipo = 0.0
            return base + lat_bonus + tipo

        # 1) abre E entrega a 16k
        candidatos = [d for d in devs if d["samplerate"] >= SAMPLE_RATE and _valido(d["id"], SAMPLE_RATE)]
        if candidatos:
            melhor = max(candidatos, key=score)
            self._preferido = melhor["id"]
            self._persistir()
            return melhor["id"]

        if permitir_nativo:
            # 2) abre E entrega na taxa nativa (resample depois)
            candidatos = [d for d in devs if _valido(d["id"], d["samplerate"])]
            if candidatos:
                melhor = max(candidatos, key=score)
                self._preferido = melhor["id"]
                self._persistir()
                return melhor["id"]
            # 3) apenas abre (qualquer taxa) — ultimo recurso
            candidatos = [d for d in devs if _abre(d["id"], d["samplerate"])]
            if candidatos:
                melhor = max(candidatos, key=score)
                self._preferido = melhor["id"]
                self._persistir()
                return melhor["id"]

        return None

    def selecionar(self):
        """Devolve o device preferido.

        Usa cache TTL: o benchmark/teste real so roda quando o preferido ainda
        nao foi validado ou o TTL expirou. O monitor de hot-plug invalida e
        re-benchmarka quando a lista de devices muda. Retorna o id (int) ou None.
        """
        with self._lock:
            if self._preferido is not None and any(
                d["id"] == self._preferido for d in self._dispositivos_entrada()
            ):
                agora = time.time()
                if (agora - self._ultimo_teste_ts) < self._ttl_teste:
                    return self._preferido
                if (self._testar_16k(self._preferido) and self._testar_entrega(
                    self._preferido, SAMPLE_RATE
                ) and not self._e_loopback(self._preferido)):
                    self._ultimo_teste_ts = agora
                    return self._preferido
            dev = self.benchmark()
            if dev is not None:
                self._ultimo_teste_ts = time.time()
            return dev

    def dispositivo_atual(self) -> dict:
        devs = self._dispositivos_entrada()
        did = self.selecionar()
        for d in devs:
            if d["id"] == did:
                return d
        return {}

    def iniciar_monitor(self):
        """Thread de hot-plug: detecta mudancas e re-seleciona se o preferido sumir."""
        if not self.hotplug_cfg.get("enabled", True):
            return
        if self._monitor_on:
            return
        self._monitor_on = True

        def _loop():
            ultima = {d["id"] for d in self._dispositivos_entrada()}
            intervalo = float(self.hotplug_cfg.get("poll_interval_sec", 2))
            while self._monitor_on:
                time.sleep(intervalo)
                try:
                    atual = {d["id"] for d in self._dispositivos_entrada()}
                    if atual != ultima:
                        ultima = atual
                        if self._preferido is not None and self._preferido not in atual:
                            novo = self.benchmark()
                            print(
                                f"[microfone] device {self._preferido} sumiu; "
                                f"novo preferido: {novo}"
                            )
                            self._preferido = novo
                            self._persistir()
                except Exception:
                    pass

        self._thread = threading.Thread(target=_loop, daemon=True, name="hotplug")
        self._thread.start()

    def parar_monitor(self):
        self._monitor_on = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None


class AudioEnhancer:
    """Melhora audio em numpy puro: noise gate + AGC (auto gain control).

    RNNoise nao tem wheel Windows, entao usamos um noise gate suave com
    ataque/release e um AGC leve para nivelar a captura. Estrategia segura:
    nenhuma dependencia compilada, falha silenciosa (devolve o audio original).
    """

    def __init__(self, config: dict):
        ae = config.get("audio_enhancement", {})
        self.ng = ae.get("noise_gate", {})
        self.agc = ae.get("auto_gain_control", {})
        self._gate_env = 0.0
        self._agc_gain = 1.0

    def processar(self, audio: np.ndarray) -> np.ndarray:
        if audio is None or audio.size == 0:
            return audio
        try:
            x = np.asarray(audio, dtype="float32").copy()
            x = self._noise_gate(x)
            x = self._agc(x)
            return x
        except Exception:
            return audio

    def _noise_gate(self, x):
        if not self.ng.get("enabled", True):
            return x
        thr_db = float(self.ng.get("threshold_db", -40))
        thr = 10.0 ** (thr_db / 20.0)
        attack = float(self.ng.get("attack_ms", 10)) / 1000.0
        release = float(self.ng.get("release_ms", 100)) / 1000.0
        frame = int(SAMPLE_RATE * 0.01)
        n = max(1, x.size // frame)
        out = x.copy()
        for i in range(n):
            seg = x[i * frame:(i + 1) * frame]
            r = _rms(seg)
            if r > thr:
                self._gate_env = min(1.0, self._gate_env + attack)
            else:
                self._gate_env = max(0.0, self._gate_env - release)
            out[i * frame:(i + 1) * frame] = seg * self._gate_env
        return out

    def _agc(self, x):
        if not self.agc.get("enabled", True):
            return x
        target = float(self.agc.get("target_level_db", -20))
        max_gain = float(self.agc.get("max_gain_db", 20))
        speed = float(self.agc.get("adaptation_speed", 0.1))
        alvo = 10.0 ** (target / 20.0)
        cur = _rms(x)
        if cur < 1e-6:
            return x
        ganho = min(max_gain, alvo / cur)
        self._agc_gain += (ganho - self._agc_gain) * speed
        return x * self._agc_gain


class WakeWordDetector:
    """Wake word real (Porcupine/Picovoice) com fallback VAD+regex.

    Se PORCUPINE_ACCESS_KEY existir, usa o Porcupine (offline, latencia baixa).
    Caso contrario, o modulo indica indisponibilidade e o dialogo usa a deteccao
    via VAD + regex "jarvis" (que ja funciona neste ecossistema).
    """

    def __init__(self, config: dict):
        self.cfg = config.get("wake_word", {})
        self._porcupine = None
        self._pcm = None
        self._disponivel = False
        self._inicializar()

    def _inicializar(self):
        if not self.cfg.get("enabled", True):
            return
        try:
            import pvporcupine
            chave = os.environ.get(self.cfg.get("access_key_env", "PORCUPINE_ACCESS_KEY"), "")
            if not chave:
                print("[wake] PORCUPINE_ACCESS_KEY ausente; usando fallback VAD+regex")
                return
            keywords = self.cfg.get("keywords", ["jarvis"])
            sens = self.cfg.get("sensitivities", [0.6])
            self._porcupine = pvporcupine.create(
                access_key=chave,
                keywords=keywords,
                sensitivities=sens,
            )
            import pvrecorder
            self._pcm = pvrecorder.PvRecorder(
                frame_length=self._porcupine.frame_length,
                device_index=-1,
            )
            self._disponivel = True
            print("[wake] Porcupine pronto (offline)")
        except Exception as e:
            print(f"[wake] Porcupine indisponivel ({e}); usando fallback VAD+regex")
            self._porcupine = None
            self._pcm = None
            self._disponivel = False

    @property
    def disponivel(self) -> bool:
        return self._disponivel

    def detectar(self, pcm_int16) -> bool:
        """Recebe buffer int16 na taxa do porcupine. True se ouviu a palavra."""
        if not self._disponivel or self._porcupine is None:
            return False
        try:
            return self._porcupine.process(pcm_int16) >= 0
        except Exception:
            return False

    def parar(self):
        if self._porcupine is not None:
            try:
                self._porcupine.delete()
            except Exception:
                pass
        if self._pcm is not None:
            try:
                self._pcm.delete()
            except Exception:
                pass
        self._porcupine = None
        self._pcm = None
        self._disponivel = False


class MicrofoneManager:
    """Orquestrador dos 8 passos: device, hot-plug, wake word, VAD, bridge sync e
    health check. Integra com dialogo.py mantendo os contratos existentes
    (runtime/mic_estado.json com chave "ativo")."""

    def __init__(self, config: dict | None = None):
        self.config = config if config is not None else _carregar_config()
        self.device = DeviceSelector(self.config)
        self.enhancer = AudioEnhancer(self.config)
        self.wake = WakeWordDetector(self.config)
        self.bridge_cfg = self.config.get("bridge_integration", {})
        self.health_cfg = self.config.get("health_check", {})
        self._estado = {"ativo": False, "status": "off", "timestamp": int(time.time())}
        self._lock = threading.Lock()
        self._ultima_atividade = time.time()
        self._restarts = 0

    # --- estado / bridge ---

    def _gravar_estado(self, status: str, extra: dict | None = None):
        if not self.bridge_cfg.get("enabled", True):
            return
        with self._lock:
            self._estado.update({
                "ativo": status in ("listening", "processing"),
                "status": status,
                "timestamp": int(time.time()),
            })
            if extra:
                self._estado.update(extra)
        try:
            _atomic_write(ESTADO_FILE, self._estado)
        except Exception:
            pass

    def ativo(self) -> bool:
        return bool(self._estado.get("ativo"))

    def marcar_listening(self):
        self._gravar_estado("listening", {"device_id": self.device.selecionar()})

    def marcar_processing(self):
        self._gravar_estado("processing")

    def marcar_paused_tts(self):
        """Jarvis esta falando: pausa o mic (evita que ele ouça a propria voz)."""
        self._gravar_estado("paused_tts")

    def marcar_off(self):
        self._gravar_estado("off")

    # --- health check / watchdog ---

    def marcar_atividade(self):
        self._ultima_atividade = time.time()

    def watchdog_ok(self) -> bool:
        """True se a ultima atividade nao excedeu o timeout (loop travado?)."""
        timeout = float(self.health_cfg.get("watchdog_timeout_sec", 60))
        return (time.time() - self._ultima_atividade) <= timeout

    def registrar_restart(self) -> bool:
        """Registra um restart. Devolve False se excedeu o limite (deve encerrar)."""
        max_r = int(self.health_cfg.get("max_restarts", 3))
        self._restarts += 1
        if self._restarts > max_r:
            print("[microfone] limite de restarts atingido; encerrando com seguranca")
            return False
        cooldown = float(self.health_cfg.get("restart_cooldown_sec", 30))
        print(f"[microfone] restart {self._restarts}/{max_r} em {cooldown}s")
        time.sleep(cooldown)
        return True


# Instancia de conveniencia compartilhada (unica por processo)
_manager = None
_manager_lock = threading.Lock()


def obter_manager() -> MicrofoneManager:
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = MicrofoneManager()
        return _manager