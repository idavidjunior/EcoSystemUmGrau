import asyncio, websockets, edge_tts, base64, json, logging, os, re, time, xml.sax.saxutils, socket, urllib.request, urllib.error, random, datetime, shutil, subprocess, sys, unicodedata
from pathlib import Path
from aiohttp import web

# Speech Pipeline — pipeline central de TTS
SCRIPTS_DIR = Path(__file__).resolve().parent
ECOSSISTEMA_DIR = SCRIPTS_DIR.parent
if str(ECOSSISTEMA_DIR) not in sys.path:
    sys.path.insert(0, str(ECOSSISTEMA_DIR))
try:
    from tts import SpeechPipeline
    _speech_pipeline = SpeechPipeline()
    SPEECH_PIPELINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SpeechPipeline não disponível: {e}")
    SPEECH_PIPELINE_AVAILABLE = False
    _speech_pipeline = None

# NVIDIA Quota Monitor
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from nvidia_quota_monitor import get_monitor, nvidia_request_with_quota
    NVIDIA_QUOTA_AVAILABLE = True
    try:
        from ver_log import _decodificar as _decodificar_verlog
    except ImportError:
        _decodificar_verlog = None
except ImportError as e:
    logging.warning(f"nvidia_quota_monitor não disponível: {e}")
    NVIDIA_QUOTA_AVAILABLE = False
    def get_monitor():
        return None
    def nvidia_request_with_quota(*args, **kwargs):
        raise RuntimeError("nvidia_quota_monitor não instalado")

HAB_ROOT = Path(__file__).resolve().parent.parent / "mcp"
for _hp in [HAB_ROOT / "internet" / "habilidades" / "clima-api"]:
    if _hp.is_dir() and str(_hp) not in sys.path:
        sys.path.insert(0, str(_hp))

from clima_api import get_weather_data, get_forecast_data
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

# Frases manager unificado (saudacoes, classificacao conexao, anti-repeticao)
try:
    from frases_manager import (
        _carregar_saudacao_estado,
        _salvar_saudacao_estado,
        classificar_conexao,
        registrar_saudacao,
        obter_saudacoes_hoje,
        marcar_atividade,
    )

    def _classificar_conexao():
        """Traduz o retorno (str) do frases_manager p/ o dict esperado pela bridge."""
        tipo = classificar_conexao()
        return {
            "eh_reconexao": tipo == "reconexao",
            "minutos_desde_atividade": 0,
            "hist_tamanho": 0,
        }
except ImportError as e:
    logging.warning(f"frases_manager não disponível: {e}")
    # Fallbacks locais mínimos
    def _carregar_saudacao_estado():
        return {"conexoes": 0, "hoje": "", "saudacoes_hoje": [], "ultima_saudacao": "", "ultima_saudacao_ts": 0, "ultima_atividade_ts": 0}
    def _salvar_saudacao_estado(d): pass
    def _classificar_conexao():
        return {"eh_reconexao": False, "minutos_desde_atividade": 0, "hist_tamanho": 0}
    def registrar_saudacao(texto): pass
    def obter_saudacoes_hoje(): return []
    def marcar_atividade(): pass

logging.basicConfig(level=logging.INFO)
logging.getLogger("websockets.server").setLevel(logging.WARNING)
logging.getLogger("websockets.client").setLevel(logging.WARNING)
file_handler = logging.FileHandler(Path(__file__).parent / "bridge_log.txt", mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger("vox")

TTS_VOICE = "pt-BR-AntonioNeural"
TTS_PITCH = "+0Hz"
TTS_RATE = "+0%"

# Cadeia de voz rápida: modelos NVIDIA direto (sem serve), thinking desligado.
# Medidos em 04/09/2026 (prompt curto, max_tokens 80): nemotron-lightning ~1-3s,
# gpt-oss-20b ~3-5s, kimi-k3 ~5s, deepseek-v4-flash ~7-18s (reserva, mesmo do serve).
# Override via env VOZ_RAPIDA_MODELOS="m1,m2,..." (em scripts/.env).
_CADEIA_VOZ_RAPIDA = [
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "openai/gpt-oss-20b",
    "moonshotai/kimi-k3",
    "deepseek-ai/deepseek-v4-flash-0731",
]
if os.environ.get("VOZ_RAPIDA_MODELOS"):
    _CADEIA_VOZ_RAPIDA = [m.strip() for m in os.environ["VOZ_RAPIDA_MODELOS"].split(",") if m.strip()]

BIN = str(Path(os.environ["APPDATA"]) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
PORTA_SERVE = int(os.environ.get("OPENCODE_SERVE_PORT", "8767"))
PORTA_SERVE_RESERVA = int(os.environ.get("OPENCODE_SERVE_PORT_RESERVA", "8768"))
SERVE_URL = f"http://127.0.0.1:{PORTA_SERVE}"
SERVER_USER = "opencode"
SERVER_PASS = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
# Fallback: le SENHA direto do scripts/.env se env nao estiver herdada (pythonw via Start-Process)
if not SERVER_PASS:
    try:
        from pathlib import Path as _P
        _env = Path(__file__).resolve().parent / ".env"
        if _env.exists():
            for _ln in _env.read_text(encoding="utf-8").splitlines():
                if _ln.startswith("OPENCODE_SERVER_PASSWORD="):
                    SERVER_PASS = _ln.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except Exception:
        pass
MODELO_VISION_PROVIDER = "nvidia"
MODELO_VISION_MODEL = "qwen/qwen-image"
WORKDIR = r"C:\Users\David Jr\Documents\Default Project"
HIST_PATH = Path(WORKDIR) / "EcoSystemUmGrau" / "conversa_unica.json"
SYS_PATH = str(Path(__file__).parent / "JARVIS_SYSTEM.md")
PRON_PATH = str(Path(__file__).parent / "pronuncias.json")  # ipa metadata apenas

MAX_HIST = 1000

# Volume do widget (lido de runtime/widget_state.json)
WIDGET_STATE = ECOSSISTEMA_DIR / "runtime" / "widget_state.json"

def _ler_volume_widget() -> int:
    """Lê volume (0-100) do widget. Retorna 80 se não disponível."""
    try:
        if WIDGET_STATE.exists():
            d = json.loads(WIDGET_STATE.read_text(encoding="utf-8"))
            return max(0, min(100, int(d.get("volume", 80))))
    except Exception:
        pass
    return 80
# Janela de conversa ativa: se a última fala no histórico foi há menos de
# JANELA_CONVERSA_MIN minutos, NÃO repetir saudação inicial — a conversa
# continua fluindo (evita o "recomeço" a cada reconexão dentro da mesma sessão).
JANELA_CONVERSA_MIN = 30

# ============ TAREFAS ASSÍNCRONAS (fila + executor + notificação proativa) ============
# O usuário pede algo demorado (auditoria, verificação de integridade, preflight);
# a bridge agenda, executa o script real em background e AVISA o app quando termina.
# Persistido em runtime/tarefas_async.json — sobrevive a restart (robustez).

_TAREFAS_PATH = ECOSSISTEMA_DIR / "runtime" / "tarefas_async.json"
_TAREFAS_CACHE = []
_TAREFAS_LOADED = False
# Conexões WS "voz" ativas (app Android) para envio proativo sem esperar mensagem.
_WS_VOZ = set()
_WS_VOZ_LOCK = asyncio.Lock()

# Mapa de tarefas: intenção do usuário -> script real (via subprocess).
# Executados SEM janela (CREATE_NO_WINDOW), com timeout e captura de saída.
TAREFAS_DISPONIVEIS = {
    "auditoria_codigo": {
        "nome": "Auditoria de código",
        "cmd": [sys.executable, str(SCRIPTS_DIR / "audit_eco.py"), "--json"],
        "timeout": 600,
        "intencoes": [
            r"\baudit(a|ado|ando|ar|oria|or)\b", r"\bscan(a)?\s*(proativo|completo)?",
            r"escanei", r"verific(a|ar)\s+o\s+ecossistema", r"procur(a|ar)\s*erros",
            r"veja\s*se\s*tudo\s*est[aá]", r"revise\s*o\s*(c[oó]digo|sistema)",
        ],
    },
    "integridade_dados": {
        "nome": "Verificação de integridade",
        "cmd": [sys.executable, str(SCRIPTS_DIR / "integrity_guard.py"), "--check", "--json"],
        "timeout": 600,
        "intencoes": [
            r"\bintegridade", r"integridade de dados", r"dados\s+s[ãa]o", r"checar\s+(os\s+)?dados",
            r"verific.*integ", r"corrompid", r"integridade\s+do\s+ecossistema",
        ],
    },
    "preflight_tecnico": {
        "nome": "Preflight técnico",
        "cmd": [sys.executable, str(SCRIPTS_DIR / "preflight_check.py")],
        "timeout": 600,
        "intencoes": [
            r"\bpreflight", r"pre-flight", r"checagem\s+t[ée]cnica", r"valida\s*(o|r)\s*(o\s+)?sistema",
        ],
    },
}

# Última saída da tarefa (para o resumo falado). Chave = tipo de tarefa.
_TAREFAS_ULTIMALIDA = {}


def _tarefas_carregar():
    """Lê o arquivo de tarefas persistido. Cache em memória com reload sob demanda."""
    global _TAREFAS_CACHE, _TAREFAS_LOADED
    if not _TAREFAS_LOADED:
        try:
            if _TAREFAS_PATH.exists():
                d = json.loads(_TAREFAS_PATH.read_text(encoding="utf-8-sig"))
                _TAREFAS_CACHE = d if isinstance(d, list) else []
            else:
                _TAREFAS_CACHE = []
            _TAREFAS_LOADED = True
        except Exception as e:
            logger.warning(f"tarefas carregar: {e}")
            _TAREFAS_CACHE = []
    return _TAREFAS_CACHE


def _tarefas_salvar():
    """Persiste o estado da fila (escrita atômica via tmp + os.replace)."""
    try:
        _TAREFAS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _TAREFAS_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(_TAREFAS_CACHE, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(_TAREFAS_PATH))
    except Exception as e:
        logger.warning(f"tarefas salvar: {e}")


def _tarefa_nova(tipo, pedido=""):
    """Registra uma tarefa nova na fila persistente. Retorna o dict da tarefa."""
    t = {
        "id": base64.urlsafe_b64encode(os.urandom(6)).decode().rstrip("="),
        "tipo": tipo,
        "nome": TAREFAS_DISPONIVEIS[tipo]["nome"],
        "status": "queued",
        "pedido": pedido,
        "criado": time.time(),
        "inicio": None,
        "fim": None,
        "duracao_s": None,
        "saida": "",
        "erro": "",
        "resumo": "",
        "intervalo_progresso": None,
    }
    fila = _tarefas_carregar()
    fila.append(t)
    _TAREFAS_CACHE = fila[-50:]  # mantém apenas as 50 mais recentes
    _tarefas_salvar()
    return t


def _tarefas_atualizar(task_id, **campos):
    """Atualiza campos de uma tarefa e persiste."""
    for t in _TAREFAS_CACHE:
        if t["id"] == task_id:
            t.update(campos)
            break
    _tarefas_salvar()


def _tarefa_ativa(tipo):
    """True se já existe uma tarefa do mesmo tipo rodando ou na fila."""
    for t in _tarefas_carregar():
        if t["tipo"] == tipo and t["status"] in ("queued", "running"):
            return True
    return False


# ============ AVISO PERIÓDICO DE PROGRESSO ============
# "Me avise a cada X minutos": extrai o intervalo do pedido, persiste como
# padrão e dispara notificações periódicas durante tarefas longas. O padrão
# fica em saudacao_estado.json para sobreviver a restart da bridge.
_INTERVALO_RE = re.compile(
    r"cada\s+(?:(?P<n>\d+)\s*(?P<unit>min(?:uto|utos)?|seg(?:undo)?s?|s)\b"
    r"|(?P<min>minuto|min)\b|(?P<seg>segundo|seg)\b)",
    re.IGNORECASE,
)
_PROGRESSO_RE = re.compile(
    r"avisa|avise|avisar|informe|informa|notific|progresso|andamento|atualiz|me\s+conte|conte\s*me",
    re.IGNORECASE,
)


def _detectar_intervalo_progresso(m):
    """Extrai o intervalo ("a cada X minutos/segundos") de um pedido."""
    if not m:
        return None
    m2 = m.lower().strip()
    if not _PROGRESSO_RE.search(m2):
        return None
    mm = _INTERVALO_RE.search(m2)
    if not mm:
        return None
    if mm.group("n"):
        n = int(mm.group("n"))
        seg = n * 60 if (mm.group("unit") or "s").lower().startswith("min") else n
    elif mm.group("min"):
        seg = 60
    else:
        seg = 30
    return max(seg, 10)


def _intervalo_humano(seg):
    """Formata 90 -> '1 minuto e 30 segundos', 120 -> '2 minutos'."""
    seg = int(seg or 0)
    if seg <= 0:
        return ""
    minutos, resto = divmod(seg, 60)
    partes = []
    if minutos:
        partes.append(f"{minutos} minuto{'s' if minutos != 1 else ''}")
    if resto:
        partes.append(f"{resto} segundo{'s' if resto != 1 else ''}")
    return " e ".join(partes)


def _intervalo_padrao():
    """Intervalo de aviso persistido para as próximas tarefas (ou None)."""
    try:
        v = _carregar_saudacao_estado().get("intervalo_progresso") or 0
        return int(v) if int(v) >= 10 else None
    except Exception:
        return None


def _intervalo_salvar(seg):
    """Persiste o intervalo de aviso periódico (sobrevive a restart da bridge)."""
    try:
        d = _carregar_saudacao_estado()
        d["intervalo_progresso"] = int(seg)
        _salvar_saudacao_estado(d)
    except Exception as e:
        logger.warning(f"intervalo salvar: {e}")


def _historico_payload(limite=600):
    """Conversa canônica (conversa_unica.json) pronta para o app renderizar.

    O app é apenas a VOZ do ecossistema: ele NÃO mantém histórico próprio.
    Esta função converte as linhas "Usuário: ..." / "Jarvis: ..." do arquivo
    único em mensagens estruturadas exibíveis.
    """
    try:
        linhas = json.loads(HIST_PATH.read_text(encoding="utf-8-sig")) if HIST_PATH.exists() else []
    except Exception:
        return []
    if not isinstance(linhas, list):
        return []
    out = []
    for linha in linhas[-limite:]:
        texto = str(linha).strip()
        if texto.startswith("Usuário: "):
            out.append({"de_usuario": True, "texto": texto[len("Usuário: "):]})
        elif texto.startswith("Jarvis: "):
            out.append({"de_usuario": False, "texto": texto[len("Jarvis: "):]})
        else:
            out.append({"de_usuario": False, "texto": texto})
    return out

# Retrato vivo do diálogo: quem fala é o bridge (TTS via app), então ele marca
# "falando" no runtime/dialogo_vivo.json e emite a atividade "fala" — o Cérebro
# Vivo (widget_grafo.py eco_sentinela) acende a região de fala em tempo real.
_RETRATO_BRIDGE = ECOSSISTEMA_DIR / "runtime" / "dialogo_vivo.json"
_fala_seq = [0]


def _retrato_fala(on, voce="", erro=""):
    """Espelha o padrão do dialogo.py: "falando" enquanto o bridge fala via TTS."""
    try:
        d = {"estado": "falando" if on else "ouvindo",
             "voce": str(voce)[:200] if on else "",
             "erro": str(erro)[:300] if erro else "",
             "quando": time.time()}
        tmp = _RETRATO_BRIDGE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, _RETRATO_BRIDGE)
        from atividade_emit import emitir
        emitir("fala", 0.95 if on else 0.0)
    except Exception:
        pass


def _marcar_inicio_fala(texto):
    """Marca "falando" e agenda o retorno a "ouvindo" ao fim da fala estimada."""
    _fala_seq[0] += 1
    seq = _fala_seq[0]
    _retrato_fala(True, texto)
    duracao = max(0.5, len(texto) * 0.055)  # ~18 chars/s TTS + margem

    async def _fim():
        await asyncio.sleep(duracao)
        if _fala_seq[0] == seq:
            _retrato_fala(False)

    try:
        asyncio.get_event_loop().create_task(_fim())
    except Exception:
        pass

DIAS = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]
MESES = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
INTERRUPCAO = re.compile(r'^(ok|ta bom|esta bom|chega|para|cala a boca|já chega|valeu|obrigado|entendi|deixa pra lá|depois eu pergunto)[\s!.?…]*$', re.IGNORECASE)

def feriados_brasil(agora):
    mes = agora.month
    dia = agora.day
    fixos = {
        (1, 1): "Ano Novo",
        (4, 21): "Tiradentes",
        (5, 1): "Dia do Trabalho",
        (9, 7): "Independência do Brasil",
        (10, 12): "Nossa Senhora Aparecida",
        (11, 2): "Finados",
        (11, 15): "Proclamação da República",
        (12, 25): "Natal",
    }
    return fixos.get((mes, dia))

def _local_legivel():
    try:
        from geolocalizacao import get_localizacao
        loc = get_localizacao()
        if "erro" not in loc and loc.get("cidade"):
            cidade = loc["cidade"].strip()
            regiao = loc.get("regiao", "").strip()
            if cidade.lower() == "são paulo":
                return "em São Paulo/SP, na Capital"
            if regiao:
                return f"em {cidade}/{regiao}"
            return f"em {cidade}"
    except Exception:
        pass
    return "aqui, no seu computador"


ADB_PATH = r"C:\Users\David Jr\AppData\Local\Android\platform-tools\platform-tools\adb.exe"
PHONE_SERIAL = "6d92eed7"
_saude_cache = {"t": 0.0, "texto": ""}


def _pc_saude():
    script = (
        "$o=@{}\n"
        "try{$b=Get-CimInstance Win32_Battery;if($b){$o.bat=[math]::Round($b.EstimatedChargeRemaining);"
        "$o.carregando=($b.BatteryStatus -eq 2)}}catch{}\n"
        "$c=Get-CimInstance Win32_Processor;if($c){$o.cpu=[math]::Round(($c.LoadPercentage|Measure-Object -Average).Average)}\n"
        "$m=Get-CimInstance Win32_OperatingSystem;if($m){$o.ram=[math]::Round((1-$m.FreePhysicalMemory/$m.TotalVisibleMemorySize)*100)}\n"
        "$f=Get-CimInstance Win32_LogicalDisk -Filter 'DeviceID=\"C:\"';if($f){$o.disk=[math]::Round((1-$f.FreeSpace/$f.Size)*100)}\n"
        "$o|ConvertTo-Json -Compress"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=8)
    if r.returncode != 0 or not r.stdout.strip():
        return {}
    return json.loads(r.stdout)


def _cel_bateria():
    if not os.path.exists(ADB_PATH):
        return None
    try:
        r = subprocess.run([ADB_PATH, "-s", PHONE_SERIAL, "shell", "dumpsys", "battery"], capture_output=True, text=True, timeout=5)
        m = re.search(r"\blevel:\s*(\d+)", r.stdout or "")
        return int(m.group(1)) if m else None
    except Exception:
        return None


def saude_sistema():
    global _saude_cache
    if time.time() - _saude_cache["t"] < 60:
        return _saude_cache["texto"]
    partes = []
    try:
        cel = _cel_bateria()
        if cel is not None:
            if cel <= 20:
                partes.append(f"celular com bateria crítica em {cel}%, vale conectar o carregador")
            elif cel <= 35:
                partes.append(f"celular com bateria em {cel}%, convém carregar em breve")
            else:
                partes.append(f"celular com bateria em {cel}%")
    except Exception as e:
        logger.warning(f"cel saude: {e}")
    try:
        pc = _pc_saude()
        if pc.get("bat") is not None and pc["bat"] <= 30:
            st = "carregando" if pc.get("carregando") else "sem carregador"
            partes.append(f"PC com bateria em {pc['bat']:.0f}% ({st})")
        if pc.get("cpu") is not None and pc["cpu"] >= 80:
            partes.append(f"PC com CPU em {pc['cpu']:.0f}%")
        if pc.get("ram") is not None and pc["ram"] >= 85:
            partes.append(f"PC com memória em {pc['ram']:.0f}%")
        if pc.get("disk") is not None and pc["disk"] >= 85:
            partes.append(f"PC com disco C: em {pc['disk']:.0f}% de uso")
    except Exception as e:
        logger.warning(f"pc saude: {e}")
    texto = "Saúde do sistema: " + ", ".join(partes) + "." if partes else ""
    _saude_cache = {"t": time.time(), "texto": texto}
    return texto


def briefing_espontaneo():
    agora = datetime.datetime.now()
    amanha = agora + datetime.timedelta(days=1)
    local = _local_legivel()
    data_extensa = f"{DIAS[agora.weekday()]}, {agora.day} de {MESES[agora.month - 1]} de {agora.year}, {agora.strftime('%H:%M')}"
    linhas = [f"Data e hora de agora: hoje {local}, {data_extensa}. "]
    try:
        clima = get_weather_data()
        if "erro" not in clima:
            hum = clima.get("umidade")
            texto = f"Clima atual: {clima['descricao']}, {clima['temp']:.0f}°C"
            if hum is not None:
                texto += f", umidade de {hum:.0f}%"
            linhas.append(texto + ". ")
    except Exception:
        pass
    try:
        previsao = get_forecast_data(days=2)
        if "erro" not in previsao and len(previsao["previsoes"]) >= 2:
            d = previsao["previsoes"][1]
            texto = f"Previsão para amanhã ({DIAS[amanha.weekday()]}, {amanha.strftime('%d/%m')}): mínima de {d['tmin']:.0f}°C e máxima de {d['tmax']:.0f}°C"
            if d.get("descricao"):
                texto += f", {d['descricao']}"
            if d.get("precip") and d["precip"] > 0:
                texto += f", chance de chuva de {d['precip']:.0f}%"
            linhas.append(texto + ". ")
    except Exception:
        pass
    feriado = feriados_brasil(agora)
    if feriado:
        linhas.append(f"Hoje é feriado: {feriado}. ")
    elif agora.weekday() == 4 and agora.day == 13:
        linhas.append("Hoje é sexta-feira 13. ")
    if agora.weekday() < 5 and 7 <= agora.hour <= 9:
        linhas.append("Horário de pico matinal, trânsito intenso nas vias principais. ")
    elif agora.weekday() < 5 and 17 <= agora.hour <= 19:
        linhas.append("Horário de pico noturno, trânsito intenso nas vias principais. ")
    try:
        saude = saude_sistema()
        if saude:
            linhas.append(saude + " ")
    except Exception as e:
        logger.warning(f"saude no briefing: {e}")
    return "".join(linhas)

ECOSSISTEMA_DIR = Path(WORKDIR) / "EcoSystemUmGrau"
LER_DIR = ECOSSISTEMA_DIR / "ler-runtime"
SCRIPTS_DIR = ECOSSISTEMA_DIR / "scripts"
TMP_ESTADO = SCRIPTS_DIR / "bridge_estado.json"
SAUDACAO_ESTADO = SCRIPTS_DIR / "saudacao_estado.json"
OBSIDIAN_DIRS = [
    ECOSSISTEMA_DIR / "docs",
    ECOSSISTEMA_DIR / "conhecimento",
    ECOSSISTEMA_DIR / "documentos",
]


def carregar_sistema():
    try:
        with open(SYS_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.warning(f"sistema: {e}")
        return "Você é Jarvis, especialista no EcoSystemUmGrau e OpenCode. Responda em português."

SISTEMA = carregar_sistema()



def gerar_estado_atual():
    linhas = []
    linhas.append("## Estado Atual do Ecossistema")
    try:
        linhas.append(f"### EcoSystemUmGrau/scripts")
        for f in sorted(SCRIPTS_DIR.iterdir()):
            if f.suffix in (".py", ".ps1", ".bat", ".js", ".jsonc", ".json", ".md"):
                linhas.append(f"- {f.name}")
    except: linhas.append("(scripts indisponivel)")
    try:
        linhas.append(f"\n### LER Core Files")
        cores = ["run.py", "CONHECIMENTO.md", "SYSTEM_SPEC.md"]
        for c in cores:
            p = LER_DIR / c
            if p.exists(): linhas.append(f"- {c} ({p.stat().st_size}b)")
    except: pass
    try:
        config_paths = [
            Path(os.environ.get("APPDATA","")) / ".." / ".." / ".config" / "opencode" / "opencode.jsonc",
            ECOSSISTEMA_DIR / "config" / "opencode.jsonc",
        ]
        linhas.append("\n### Configs OpenCode")
        for p in config_paths:
            p = p.resolve()
            if p.exists():
                try:
                    txt = p.read_text(encoding="utf-8")
                    linhas.append(f"- {p.name} ({len(txt)}b)")
                except: linhas.append(f"- {p.name} (ilegivel)")
    except: pass
    try:
        historico = TMP_ESTADO
        if historico.exists():
            d = json.loads(historico.read_text(encoding="utf-8"))
            linhas.append(f"\n### Mudancas recentes: {len(d)} arquivos monitorados")
    except: pass
    try:
        total_md = 0
        for d in OBSIDIAN_DIRS:
            if d.exists():
                files = list(d.rglob("*.md"))
                linhas.append(f"### Obsidian {d.name}: {len(files)} notas")
                total_md += len(files)
        if total_md:
            linhas.append(f"Total vault: {total_md} notas")
    except: pass
    try:
        mcp_root = ECOSSISTEMA_DIR / "mcp"
        n_skills = 0
        if mcp_root.exists():
            for dom in mcp_root.iterdir():
                hab = dom / "habilidades"
                if hab.is_dir():
                    n_skills += len([f for f in hab.iterdir() if f.is_dir()])
        if n_skills:
            linhas.append(f"\n### Habilidades (mcp/): {n_skills} organizadas por dominio")
    except: pass
    try:
        ler_agent = LER_DIR / "agent"
        if ler_agent.exists():
            agents = [f.stem for f in ler_agent.iterdir() if f.suffix == ".py"]
            linhas.append(f"### Agentes LER: {len(agents)}")
    except: pass
    return "\n".join(linhas)

ESTADO_ATUAL = gerar_estado_atual()

_estado_cache = {"t": 0.0, "txt": ESTADO_ATUAL}


def _estado_cacheado():
    """Estado atual com TTL: o rglob no vault Obsidian é caro, então só recomputa
    a cada 300s. Caminho de resposta rápida: não recriar o que já existe."""
    if time.time() - _estado_cache["t"] > 300:
        _estado_cache["t"] = time.time()
        _estado_cache["txt"] = gerar_estado_atual()
    return _estado_cache["txt"]


# ============================================================
# Dashboard (EcoDashboard) — snapshot estruturado do ecossistema
# Protocolo: {"type":"get_state"} -> {"type":"state","payload":{...}}
#            {"type":"ping"}       -> {"type":"pong"}
# Mantém o protocolo legado (tipo/mensagem/quota) intacto p/ o app Android.
# ============================================================

def _processo_vivo_pid(pid):
    if not pid or pid <= 0:
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                             capture_output=True, creationflags=0, text=True, timeout=10).stdout
        return str(pid) in out
    except Exception:
        return False


def _ler_pid(path):
    try:
        if Path(path).exists():
            return int(Path(path).read_text(encoding="utf-8-sig").strip())
    except Exception:
        pass
    return 0


def _snapshot_estado_ecossistema():
    """Snapshot estruturado do estado vivo do ecossistema para o EcoDashboard.

    Formato compatível com lib/models/ecosystem_state.dart. Nunca lança:
    qualquer fonte indisponível entra como valor default/seguro.
    """
    now_iso = datetime.datetime.now().isoformat()

    # --- memória ---
    mem = {"total": 0, "active": 0, "by_kind": {}, "by_confidence": {"alta": 0, "media": 0, "baixa": 0}, "by_source": {}}
    try:
        from memory_engine import stats
        mem = stats()
    except Exception:
        pass

    # --- vigilante (timers do vigilante.ps1) ---
    vig_pid = _ler_pid(str(Path.home() / ".vigilante.pid"))
    vig_running = _processo_vivo_pid(vig_pid)
    agora = datetime.datetime.now()
    timers = {}
    defs = [
        ("git sync eco", "5 min", 300, "sincroniza repositorio principal"),
        ("git sync projetos", "1 min", 60, "sincroniza repos Android"),
        ("learn diario", "24 h", 86400, "varredura proativa de aprendizado"),
        ("rules check", "1 h", 3600, "consistencia das 3 camadas de regras"),
        ("triagem orfaos", "24 h", 86400, "auditoria de organizacao"),
        ("voz guarda", "30 min", 1800, "regressao de paths temp de audio"),
        ("opencode cache", "1 h", 3600, "limpeza de logs antigos"),
        ("evolution radar", "4 h", 14400, "auto-evolucao curada"),
    ]
    for nome, intervalo, segs, desc in defs:
        timers[nome] = {
            "name": nome,
            "active": vig_running,
            "interval": intervalo,
            "last_run": "",
            "next_run": (agora + datetime.timedelta(seconds=segs)).strftime("%H:%M"),
            "status": "ok" if vig_running else "error",
        }

    # --- radar (evolution-radar) ---
    radar_dir = ECOSSISTEMA_DIR / "conhecimento" / "evolution-radar"
    admin_ok = (ECOSSISTEMA_DIR / ".evolution_admin_ok").exists()
    def _count(sub):
        try:
            d = radar_dir / sub
            return len([f for f in d.iterdir() if f.is_file()]) if d.exists() else 0
        except Exception:
            return 0
    radar = {
        "admin_enabled": admin_ok,
        "phase": "idle",
        "proposals_found": _count("bruto"),
        "proposals_validated": _count("filtrado"),
        "packages_ready": _count("pacotes"),
        "next_run": "",
        "recent_proposals": [],
    }
    try:
        if (radar_dir / "pacotes").exists():
            packs = sorted((radar_dir / "pacotes").glob("evolution-pack-*.json"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            if packs:
                d = json.loads(packs[0].read_text(encoding="utf-8"))
                props = d.get("proposals", []) if isinstance(d, dict) else []
                radar["recent_proposals"] = [{
                    "id": p.get("id", ""),
                    "source": p.get("source", ""),
                    "title": p.get("title", ""),
                    "status": p.get("status", "raw"),
                    "relevance_score": float(p.get("relevance_score", 0)),
                    "detected_at": p.get("detected_at", now_iso),
                } for p in props[:10]]
    except Exception:
        pass

    # --- voz / audio (runtime/*.json) ---
    voice = {"stt_active": False, "tts_playing": False, "vad_active": False,
             "input_level": 0.0, "current_text": "", "last_spoken": ""}
    try:
        narr = json.loads((ECOSSISTEMA_DIR / "runtime" / "narracao_estado.json").read_text(encoding="utf-8"))
        voice["tts_playing"] = bool(narr.get("ativo", False)) and not bool(narr.get("pausado", False))
    except Exception:
        pass
    try:
        mic = json.loads((ECOSSISTEMA_DIR / "runtime" / "mic_estado.json").read_text(encoding="utf-8"))
        mic_pid = _ler_pid(ECOSSISTEMA_DIR / "runtime" / "mic.pid")
        voice["vad_active"] = bool(mic.get("ativo", False)) and _processo_vivo_pid(mic_pid)
        voice["mic_status"] = mic.get("status", "off")
        voice["mic_mode"] = mic.get("modo", "vad")
        voice["mic_paused_tts"] = mic.get("status") == "paused_tts"
    except Exception:
        pass
    try:
        from widget_edge import ultima_fala
        fala = ultima_fala()
        if fala:
            voice["last_spoken"] = fala
            voice["current_text"] = fala
    except Exception:
        pass

    # --- agentes (LER runtime) ---
    agents = []
    try:
        roles = {"orchestrator": "maestro", "supervisor": "revisor", "validator": "revisor",
                 "final_auditor": "revisor", "executor": "executor", "planner": "especialista",
                 "strategy_engine": "especialista", "goal_analyzer": "especialista"}
        for f in sorted((LER_DIR / "agent").glob("*.py")):
            nome = f.stem
            agents.append({
                "id": nome,
                "name": nome.replace("_", " ").title(),
                "icon": "🤖",
                "role": roles.get(nome, "executor"),
                "status": "idle",
                "current_task": None,
            })
    except Exception:
        pass

    # --- MCP servers (config/opencode.jsonc) ---
    mcp_servers = []
    try:
        cfg = json.loads((ECOSSISTEMA_DIR / "config" / "opencode.jsonc").read_text(encoding="utf-8"))
        mcp_cfg = cfg.get("mcp") or {}
        for nome, v in mcp_cfg.items():
            if not isinstance(v, dict):
                continue
            mcp_servers.append({
                "name": nome,
                "transport": "local" if v.get("type") == "local" else "stdio",
                "status": "online",
                "tools_count": 0,
                "error": None,
            })
    except Exception:
        pass

    # --- logs recentes (bridge_log.txt tail) ---
    recent_logs = []
    try:
        import re as _re
        logpath = SCRIPTS_DIR / "bridge_log.txt"
        if logpath.exists():
            linhas = logpath.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]
            pat = _re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+\s+(\w+):(?:[\w.]+):(.*)$")
            for ln in linhas:
                m = pat.match(ln)
                if m:
                    ts, lvl, msg = m.group(1), m.group(2).lower(), m.group(3).strip()
                    lvl = "warn" if lvl == "warning" else lvl
                    recent_logs.append({
                        "timestamp": ts.replace(" ", "T"),
                        "level": lvl if lvl in ("info", "warn", "error", "debug") else "info",
                        "source": "bridge",
                        "message": msg[:300],
                    })
    except Exception:
        pass

    return {
        "memory": mem,
        "vigilante": {
            "running": vig_running,
            "pid": vig_pid,
            "timers": timers,
            "last_sync": now_iso,
        },
        "radar": radar,
        "voice": voice,
        "agents": agents,
        "projects": [],
        "mcp_servers": mcp_servers,
        "recent_logs": recent_logs[-100:],
        "timestamp": now_iso,
    }


def sanitizar(t):
    """Sanitiza texto para TTS. Usa SpeechPipeline quando disponível."""
    if not t: return ""
    if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
        try:
            texto, _ = _speech_pipeline.prepare(t)
            return texto
        except Exception:
            pass
    # Fallback: camada V2 do normalizador (TTS Text Normalizer)
    try:
        from tts.text_normalizer import normalize_for_tts
        return normalize_for_tts(t)
    except Exception:
        pass
    # Fallback legado: sanitização mínima
    for p in [r'```[\s\S]*?```', r'`[^`]+`', r'[*_~#]', r'\[([^\]]+)\]\([^)]+\)', r'[<>{}()\[\]]']:
        t = re.sub(p, '', t)
    t = t.replace('"','').replace("'",'').replace('`','')
    t = re.sub(r'^\s*[-*+]\s+', '', t, flags=re.MULTILINE)
    return re.sub(r'\s+', ' ', t).strip()[:2000]


CONECTORES_INICIAIS = ["então", "portanto", "agora", "bom", "olha", "assim", "enfim", "porém", "contudo", "finalmente", "primeiro", "depois", "aliás", "provavelmente", "atualmente", "resumindo", "vamos"]
CONECTORES_MEIO = ["mas", "porque", "pois", "então", "depois", "porém", "contudo", "quando", "enquanto", "por isso", "portanto", "além disso"]
RESPIRACAO = CONECTORES_MEIO + ["e", "ou"]


def _inserir_respiracao(ora):
    """Quebra orações longas em cláusulas menores com vírgula (pausa de respiração)."""
    if len(ora.split()) <= 16:
        return ora
    alvo = re.compile(
        r'(?<![,.;:!?])\s+(?:' + '|'.join(re.escape(c) for c in RESPIRACAO) + r')\s+',
        re.IGNORECASE)
    matches = list(alvo.finditer(ora))
    if not matches:
        return ora
    # Não insere vírgula dentro de numerais por extenso ("trinta e quatro",
    # "dois mil e vinte e seis") — regra central no módulo tts.
    try:
        from tts.text_normalizer import e_conector_de_numeral
        matches = [m for m in matches if not e_conector_de_numeral(ora, m)]
    except ImportError:
        pass
    if not matches:
        return ora
    centro = len(ora) // 2
    melhor = min(matches, key=lambda m: abs(m.start() - centro))
    return ora[:melhor.start()].rstrip() + ', ' + ora[melhor.start():].strip()


def melhorar_fala(texto):
    """Prepara o texto para leitura por voz: pontuação limpa e respirações naturais.

    Regras (30/07/2026):
    - NUNCA altera a ortografia das palavras (voz nativa pt-BR).
    - Horas digitais viram leitura natural ANTES de qualquer troca de `:`:
      "21:44" -> "21 horas e 44"; "22:00" -> "22 horas em ponto".
    - Vírgula e ponto são as respirações do TTS; `;`/`:` restantes viram vírgula.
    - Travessões viram vírgula (pausa curta) para a voz.
    - Orações longas (>16 palavras) ganham vírgula antes do conectivo mais próximo do meio.
    - Toda frase começa com maiúscula; toda frase termina com ponto final.
    - Espaço sempre depois de vírgula/ponto; nunca antes de pontuação.
    """
    t = texto.strip()
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\b(\d{1,2}):00\b', r'\1 horas em ponto', t)
    t = re.sub(r'\b(\d{1,2}):(\d{2})\b', r'\1 horas e \2', t)
    t = re.sub(r'\s*[—–]\s*', ', ', t)
    t = re.sub(r'\s+-\s+', ', ', t)
    t = re.sub(r'^[,;\s]+', '', t)
    t = t.replace(';', ',').replace(':', ',')
    t = re.sub(r'\.{3,}', '...', t)
    for c in CONECTORES_MEIO:
        t = re.sub(rf'(?<![.!?,])\s+{re.escape(c)}\s+', f', {c} ', t, flags=re.IGNORECASE)
    oracoes = re.split(r'(?<=[.!?])\s+', t)
    t = ' '.join(_inserir_respiracao(o.strip()) for o in oracoes if o.strip())
    for c in CONECTORES_INICIAIS:
        t = re.sub(rf'^(?i:{re.escape(c)})\s+', f'{c.capitalize()}, ', t)
    t = re.sub(r'\s+([,.;:?!])', r'\1', t)
    t = re.sub(r'(?<!\d)([,;:?!.])(?![\d.])', r'\1 ', t)
    t = re.sub(r',{2,}', ',', t)
    t = re.sub(r'\b(e|ou)\s*,\s*(?=depois|então|porém|contudo|portanto|finalmente|enfim)\b', r'\1 ', t, flags=re.IGNORECASE)
    partes = []
    for oracao in re.split(r'(?<=[.!?])\s+', t):
        oracao = oracao.strip()
        if not oracao:
            continue
        oracao = oracao[0].upper() + oracao[1:] if oracao[0].islower() else oracao
        if not oracao.endswith(('.', '?', '!', '...')):
            oracao += '.'
        partes.append(oracao)
    t = ' '.join(partes)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:2000]


def normalizar_hora_display(texto):
    """Garante o formato HH:MM no texto EXIBIDO, independente de como o LLM escreveu a hora.

    O problema da pronúncia é só do áudio (resolvido em melhorar_fala). A TELA deve
    continuar mostrando "21:44". O LLM às vezes reescreve como "23 horas e 29",
    "23h29", "22 horas em ponto" etc. — aqui convertemos de volta para HH:MM:

      "23 horas e 29" / "23h29" / "23 hs 29" -> "23:29"
      "22 horas em ponto" / "22h" / "22 horas" -> "22:00"
      "23 e 29" (só se for hora/minuto plausíveis) -> "23:29"
    """
    t = texto.strip()
    if not t:
        return t
    t = re.sub(r'\b(\d{1,2})\s*(?:horas?|hs?)\s*e\s*(\d{1,2})\b', r'\1:\2', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(\d{1,2})\s*[hH]\s*(\d{2})\b', r'\1:\2', t)
    t = re.sub(r'\b(\d{1,2})\s*(?:horas?|hs?)\s*em\s*ponto\b', r'\1:00', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(\d{1,2})\s*(?:horas?|hs?)\s+(\d{1,2})\b', r'\1:\2', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(\d{1,2})\s*(?:horas?|hs?)\b', r'\1:00', t, flags=re.IGNORECASE)

    def _bare(m):
        h, mn = int(m.group(1)), int(m.group(2))
        return f'{h:02d}:{mn:02d}' if h <= 23 and mn <= 59 else m.group(0)
    t = re.sub(r'\b(\d{1,2})\s+e\s+(\d{2})\b', _bare, t)
    return t




def aplicar_phonemes(texto):
    """Aplica substituições de pronúncia por TEXTO (campo "fala") do pronuncias.json.

    IMPORTANTE (02/08/2026): o edge-tts >= 7.x removeu suporte a SSML custom —
    ele ESCAPA todo o texto no __init__ (escape()), então tags como <phoneme>,
    <break> e <say-as> são lidas LITERALMENTE pela voz. Por isso:
    - "fala" (grafia falada, ex.: "Guitirrãbi") é substituição de TEXTO puro e funciona.
    - "ipa" (tag <phoneme>) é INUTILIZÁVEL com edge-tts e não é mais gerada.
    """
    try:
        with open(PRON_PATH, "r", encoding="utf-8") as f:
            ipas = json.load(f)
    except: return texto, False
    if not ipas: return texto, False
    palavras = sorted(ipas.keys(), key=len, reverse=True)
    def sub(m):
        w = m.group(0)
        key = w.lower()
        if key in ipas and "fala" in ipas[key]:
            return ipas[key]["fala"]
        return w
    texto, n = re.subn(r'\b([^\W\d_]+)\b', sub, texto)
    return texto, n > 0


# ─── Dicionário de pronúncia autoevolutivo ──────────────────────────────
# "pronuncie X como Y" / "fala X como Y" / "sempre que eu falar X, fale Y"
# registra a pronúncia em pronuncias.json na hora (campo "fala"), sem LLM.
PRON_PEDIDO_DIRETO = re.compile(
    r'^(?:por favor\s+)?(?:a partir de agora\s+)?'
    r'(?:pronuncie|pronuncia|fale|fala|diga|diz|passe a falar|comece a falar)'
    r'\s+([a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ0-9 .\-–]*?)'
    r'\s+(?:como|assim)\s+([a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ0-9 .\-–]*?)\s*[.!?]*$',
    re.IGNORECASE,
)
PRON_PEDIDO_CONDICIONAL = re.compile(
    r'^(?:a partir de agora\s+)?(?:sempre que|quando)\s+(?:eu\s+)?(?:falar|disser|dizer)\s+'
    r'([a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ0-9 .\-–]*?)'
    r'(?:\s*,|\s*[,:])\s*(?:fale|fala|diga|diz)\s+'
    r'([a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõçA-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ0-9 .\-–]*?)\s*[.!?]*$',
    re.IGNORECASE,
)


def _normalizar_palavra(w):
    return w.strip().strip('"“”\'\'').lower()


def _normalizar_fala(w):
    return w.strip().strip('"“”\'\'')


def _processar_pedido_pronuncia(msg):
    """Detecta pedido de correção de pronúncia. Retorna (palavra, fala) ou None.

    Aceita:
      - "pronuncie GitHub como Guitirrãbi"
      - "fala openai como Ópenái"
      - "sempre que eu falar nvidia, fale Envidiá"
    A palavra-alvo precisa ter <= 4 palavras e a fala <= 6, para evitar falsos
    positivos em frases normais do tipo "fala o que você vai fazer como amanhã".
    """
    if not msg or not msg.strip():
        return None
    m = PRON_PEDIDO_DIRETO.match(msg.strip()) or PRON_PEDIDO_CONDICIONAL.match(msg.strip())
    if not m:
        return None
    palavra, fala = m.group(1), m.group(2)
    palavra = _normalizar_palavra(palavra)
    fala = _normalizar_fala(fala)
    if not palavra or not fala:
        return None
    if len(palavra.split()) > 4 or len(fala.split()) > 6:
        return None
    if palavra == fala:
        return None
    return palavra, fala


def _registrar_pronuncia(palavra, fala):
    """Adiciona {palavra: {"fala": ...}} a pronuncias.json (autoevolução).

    Se a palavra já existe com "ipa", mantém o ipa e adiciona "fala" (a fala
    tem prioridade em aplicar_phonemes). Escreve com lock de arquivo simples
    (retry) para evitar corrupção se a bridge estiver gerando áudio em paralelo.
    """
    path = Path(PRON_PATH)
    for _tentativa in range(3):
        try:
            if path.exists():
                ipas = json.loads(path.read_text(encoding="utf-8"))
            else:
                ipas = {}
            if not isinstance(ipas, dict):
                ipas = {}
            entry = ipas.get(palavra)
            if not isinstance(entry, dict):
                entry = {}
            entry["fala"] = fala
            ipas[palavra] = entry
            path.write_text(json.dumps(ipas, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.warning(f"registrar_pronuncia tenta {_tentativa + 1}: {e}")
            time.sleep(0.2)
    return False


async def gerar_audio(texto):
    """Gera áudio via SpeechPipeline quando disponível, senão usa legado."""
    if not texto: return ""
    if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
        try:
            return await _speech_pipeline.synthesize(texto)
        except Exception as e:
            logger.warning(f"SpeechPipeline falhou ({e}); fallback legado")
    # Fallback: código legado
    t = sanitizar(texto)
    if not t: return ""
    t = melhorar_fala(t)

    async def _stream(entrada):
        c = edge_tts.Communicate(entrada, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
        a = b""
        async for chunk in c.stream():
            if chunk["type"] == "audio":
                a += chunk["data"]
        return a

    try:
        audio = await _stream(aplicar_phonemes(t)[0])
    except Exception as e:
        logger.warning(f"tts falhou ({e}); fallback texto puro")
        try:
            audio = await _stream(melhorar_fala(sanitizar(texto)))
        except Exception as e2:
            logger.error(f"tts texto puro tambem falhou: {e2}")
            return ""
    return base64.b64encode(audio).decode()


async def gerar_audio_stream(texto):
    """Async generator que yield chunks base64 de áudio.

    Usa SpeechPipeline quando disponível, senão usa legado.
    Protocolo streaming:
        1. Bridge envia {text, corrigido, audio_streaming: True}  (texto imediato)
        2. Bridge envia {audio_chunk: <b64>} para cada chunk (play imediato)
        3. Bridge envia {audio_done: True}  (finaliza playback)
    """
    if not texto:
        return
    if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
        try:
            async for chunk in _speech_pipeline.stream(texto):
                yield chunk
            return
        except Exception as e:
            logger.warning(f"SpeechPipeline stream falhou ({e}); fallback legado")
    # Fallback: código legado
    t = sanitizar(texto)
    if not t:
        return
    t = melhorar_fala(t)
    try:
        entrada = aplicar_phonemes(t)[0]
    except Exception:
        entrada = melhorar_fala(sanitizar(texto))
    c = edge_tts.Communicate(entrada, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    async for chunk in c.stream():
        if chunk["type"] == "audio":
            yield base64.b64encode(chunk["data"]).decode()


# --- HTTP client para opencode serve ---

_serve_error_count = 0
_serve_error_threshold = 3
_serve_restarting = False


def _restart_serve_hard():
    """Mata o processo serve existente e inicia um novo. Chamado quando o
    serve atinge o limiar de erros consecutivos (provavelmente travado)."""
    global _serve_restarting
    if _serve_restarting:
        return
    _serve_restarting = True
    logger.warning("WATCHDOM: limiar de erros atingido — reiniciando serve")
    try:
        for porta in (PORTA_SERVE, PORTA_SERVE_RESERVA):
            try:
                r = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True, text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                for line in r.stdout.splitlines():
                    if f":{porta}" in line and "LISTENING" in line:
                        pid = line.split()[-1].strip()
                        if pid.isdigit():
                            logger.info(f"WATCHDOM: matando pid={porta} porta={porta}")
                            subprocess.run(
                                ["taskkill", "/PID", pid, "/F"],
                                capture_output=True,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                            )
            except Exception:
                pass
        time.sleep(2)
        subprocess.Popen(
            [BIN, "serve", "--port", str(PORTA_SERVE)],
            cwd=WORKDIR,
            env={**os.environ, "OPENCODE_SERVER_PASSWORD": SERVER_PASS},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for _ in range(15):
            time.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                ok = s.connect_ex(("127.0.0.1", PORTA_SERVE)) == 0
                s.close()
                if ok:
                    logger.info("WATCHDOM: serve reiniciado com sucesso")
                    break
            except Exception:
                pass
        else:
            logger.error("WATCHDOM: serve não subiu após reinício")
    except Exception as e:
        logger.error(f"WATCHDOM: erro no reinício: {e}")
    finally:
        _serve_restarting = False


def _http(method, path, data=None, timeout=120):
    global _serve_error_count
    url = f"{SERVE_URL}{path}"
    creds = base64.b64encode(f"{SERVER_USER}:{SERVER_PASS}".encode()).decode()
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
            _serve_error_count = 0
            return result
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP {e.code} {method} {path}: {e.read().decode()[:300]}")
        if e.code >= 500:
            _serve_error_count += 1
            logger.warning(f"WATCHDOM: erro {_serve_error_count}/{_serve_error_threshold}")
            if _serve_error_count >= _serve_error_threshold:
                _restart_serve_hard()
                _serve_error_count = 0
        return None
    except Exception as e:
        logger.error(f"HTTP {method} {path}: {e}")
        return None

async def _http_async(method, path, data=None, timeout=120):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _http, method, path, data, timeout)


async def _ensure_serve_global():
    """Versão no nível do módulo de Cliente._ensure_serve: garante um
    `opencode serve` saudável na porta configurada (com failover para a reserva).
    Verifica saúde real via request HTTP, não apenas porta aberta."""
    for porta in (PORTA_SERVE, PORTA_SERVE_RESERVA):
        # Tenta conectar na porta
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            r = s.connect_ex(("127.0.0.1", porta))
            s.close()
            if r == 0:
                # Porta aberta - verifica saúde real com request HTTP
                if await _check_serve_health(porta):
                    return True
                logger.warning(f"porta {porta} aberta mas serve não saudável")
        except Exception:
            pass
        # Inicia serve se não respondeu
        logger.info(f"iniciando serve na porta {porta}...")
        proc = await asyncio.create_subprocess_exec(
            BIN, "serve", "--port", str(porta),
            cwd=WORKDIR,
            env={**os.environ, "OPENCODE_SERVER_PASSWORD": SERVER_PASS},
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        # Aguarda serve ficar saudável (health check real)
        for _ in range(30):
            await asyncio.sleep(1)
            if await _check_serve_health(porta):
                logger.info(f"serve na porta {porta} saudável")
                return True
        logger.warning(f"serve na porta {porta} não ficou saudável a tempo")
    return False


async def _check_serve_health(porta: int) -> bool:
    """Verifica se o serve está realmente saudável fazendo request HTTP real."""
    try:
        import urllib.request
        creds = base64.b64encode(f"{SERVER_USER}:{SERVER_PASS}".encode()).decode()
        url = f"http://127.0.0.1:{porta}/api/health"
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.getcode() == 200
    except Exception:
        try:
            # Fallback: tenta endpoint /session se /api/health não existir
            creds = base64.b64encode(f"{SERVER_USER}:{SERVER_PASS}".encode()).decode()
            url = f"http://127.0.0.1:{porta}/session"
            req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.getcode() == 200
        except Exception:
            return False


MAX_PROMPT = 80000

class Cliente:
    def __init__(self):
        self._hist = self._carregar()
        self._session_id = None
        self._init_estado()

    def _carregar(self):
        try:
            with open(HIST_PATH, "r", encoding="utf-8-sig") as f:
                d = json.load(f)
                return d[-MAX_HIST:] if isinstance(d, list) else []
        except: return []

    def _salvar(self):
        try:
            with open(HIST_PATH, "w", encoding="utf-8") as f:
                json.dump(self._hist[-MAX_HIST:], f, ensure_ascii=False, indent=2)
        except Exception as e: logger.error(f"salvar: {e}")

    def _init_estado(self):
        if not TMP_ESTADO.exists():
            try:
                TMP_ESTADO.write_text("{}", encoding="utf-8")
            except Exception as e:
                logger.warning(f"init estado: {e}")

    def _contexto_recente(self, pares: int = 7):
        """Lê as últimas N interações (usuário↔Jarvis) do histórico persistido
        para dar à saudação de reconexão uma memória de curto prazo real e o
        Jarvis identificar sozinho onde paramos, sem perguntar.
        Retorna uma string resumida ou '' se não houver histórico."""
        try:
            if not HIST_PATH.exists():
                return ""
            with open(HIST_PATH, "r", encoding="utf-8-sig") as f:
                d = json.load(f)
            if not isinstance(d, list):
                return ""
            ultimas = d[-pares * 2:]
            if not ultimas:
                return ""
            return " | ".join(
                s[len(prefix):].strip()[:200]
                for s in ultimas[-pares * 2:]
                if isinstance(s, str)
                and (s.startswith("Usuário:") or s.startswith("Jarvis:"))
                for prefix in ("Usuário:", "Jarvis:")
                if s.startswith(prefix)
            )
        except Exception as e:
            logger.warning(f"_contexto_recente: {e}")
            return ""

    def _montar(self, msg):
        estado = _estado_cacheado()
        # ---- Memoria semantica: top-3 memorias mais relevantes a msg ----
        ctx_mem = ""
        try:
            _rs = _sem_search_cached(msg, k=3, min_score=0.05)
            if _rs:
                _lines = [f"- #{r['id']} ({r['kind']}): {r['title']}" for r in _rs]
                ctx_mem = "Contexto relevante da memoria:\n" + "\n".join(_lines) + "\n\n"
                logger.info(f"memoria semantica: {len(_rs)} hits para '{msg[:40]}'")
        except Exception as _e:
            logger.debug(f"memoria semantica indisponivel: {_e}")
        # Digest de contexto (padrão isair/jarvis): modelos pequenos degradam
        # quando o prompt cresce. Condensa a memória injetada antes do sufixo.
        # LLM_DIGEST_ENABLED=1 força; "auto" (padrão) liga para modelos ≤7B.
        try:
            from runtime_context import digest_contexto, _modelo_pequeno
            habilitar = os.environ.get("LLM_DIGEST_ENABLED", "auto").lower()
            if habilitar == "1" or (habilitar == "auto" and _modelo_pequeno()):
                _teto = int(os.environ.get("LLM_DIGEST_MAX_CHARS", "4000"))
                ctx_mem = digest_contexto(ctx_mem, max_chars=_teto)
        except Exception:
            pass
        sufixo = f"Usuario: {msg}\nJarvis:"
        livre = MAX_PROMPT - len(SISTEMA) - len(estado) - len(ctx_mem) - 4 - len(sufixo)
        p = SISTEMA + "\n\n" + estado + "\n\n" + ctx_mem
        hist = self._hist[-(MAX_HIST*2):]
        for i in range(0, len(hist), 2):
            if i+1 >= len(hist): break
            entrada = f"{hist[i]}\n{hist[i+1][:500]}\n"
            if len(entrada) > livre: break
            p += entrada
            livre -= len(entrada)
        p += sufixo
        return p

    async def _ensure_serve(self):
        """Garante um `opencode serve` saudável na porta configurada, com failover
        automático: se a porta estiver com socket órfão (zumbi), tenta limpar e
        cai para a porta reserva. Resiliente a esse tipo de falha."""
        for porta in (PORTA_SERVE, PORTA_SERVE_RESERVA):
            if await self._serve_ok(porta):
                return True
            # tenta limpar a porta (se zumbi) e inicia o servidor
            limpou = await self._limpar_zumbi(porta)
            if not limpou:
                logger.warning(f"porta {porta} nao liberada, tentando reserva...")
                continue
            logger.info(f"serve not running, starting on {porta}...")
            proc = await asyncio.create_subprocess_exec(
                BIN, "serve", "--port", str(porta),
                cwd=WORKDIR,
                env={**os.environ, "OPENCODE_SERVER_PASSWORD": SERVER_PASS},
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            # Aguarda serve ficar saudável (health check real)
            for _ in range(30):
                await asyncio.sleep(1)
                if await self._serve_ok(porta):
                    logger.info(f"serve started on {porta}")
                    return True
            logger.error(f"failed to start serve on {porta}")
        return False

    async def _serve_ok(self, porta):
        """True se o serve está saudável (health check real), não apenas porta aberta."""
        # Primeiro verifica se a porta está aberta
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            r = s.connect_ex(("127.0.0.1", porta))
            s.close()
            if r != 0:
                return False
        except Exception:
            return False
        # Porta aberta - verifica saúde real via HTTP
        return await _check_serve_health(porta)

    async def _limpar_zumbi(self, porta):
        """Detecta socket órfão (porta LISTENING sem processo dono vivo) e tenta
        limpá-lo. Retorna True se conseguiu liberar (ou se nunca esteve zumbi)."""
        dono = None
        try:
            import subprocess as _sp
            out = _sp.check_output(
                ["netstat", "-ano"], creationflags=getattr(_sp, "CREATE_NO_WINDOW", 0)
            ).decode("latin-1", errors="replace")
        except Exception as e:
            logger.warning(f"limpar_zumbi netstat: {e}")
            return False
        linha = None
        for ln in out.splitlines():
            if f":{porta}" in ln and "LISTENING" in ln:
                linha = ln
                break
        if not linha:
            # porta livre -> nunca esteve zumbi
            return True
        pid = linha.split()[-1].strip()
        if not pid.isdigit():
            return False
        # verifica se o processo dono está vivo
        vivo = False
        try:
            r = _sp.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
            vivo = "INFO" not in r.stdout and pid in r.stdout
        except Exception:
            pass
        if vivo:
            # porta ocupada por processo real: não é zumbi, mas não respondeu
            logger.warning(f"porta {porta} ocupada por processo vivo pid={pid} mas sem resposta")
            return False
        # processo dono morto: socket órfão. tenta derrubar o handle
        logger.warning(f"porta {porta}: socket orfao (pid={pid} morto), limpando...")
        try:
            _sp.run(["taskkill", "/PID", pid, "/F"],
                    capture_output=True, creationflags=getattr(_sp, "CREATE_NO_WINDOW", 0))
        except Exception:
            pass
        import time as _t
        for _ in range(5):
            await asyncio.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", porta))
                s.listen(1)
                s.close()
                logger.info(f"porta {porta} liberada do socket orfao")
                return True
            except OSError:
                try:
                    s.close()
                except Exception:
                    pass
        logger.warning(f"nao consegui liberar porta {porta} do socket orfao")
        return False

    async def _get_session(self):
        # Sempre cria sessão nova para evitar acúmulo de histórico antigo
        # que fazia o Jarvis recitar relatórios passados não solicitados.
        result = await _http_async("POST", "/session", {"title": f"Jarvis-{int(time.time() * 1000)}"})
        if result:
            self._session_id = result.get("id")
            logger.info(f"created fresh session {self._session_id}")
        return self._session_id

    async def perguntar(self, msg, img_base64=None, img_mime="image/jpeg", tentativa=1):
        # Comandos Eco globais (@eco, /eco, Eco, Desativar Eco) - funcionam em qualquer lugar
        if await self._processar_comando_eco(msg):
            return ""  # Comando processado, não envia para LLM

        prompt = self._montar(msg)
        logger.info(f"hist={len(self._hist)//2} prompt={len(prompt)}b tentativa={tentativa}: {msg[:80]}")

        if not await self._ensure_serve():
            return "Erro: servidor OpenCode não está disponível."

        session_id = await self._get_session()
        if not session_id:
            return "Erro: não foi possível criar sessão no servidor."

        body = {"parts": [{"type": "text", "text": prompt}]}
        if img_base64:
            body["parts"].append({"type": "file", "mime": img_mime, "url": f"data:{img_mime};base64,{img_base64}"})
            body["model"] = {"providerID": MODELO_VISION_PROVIDER, "modelID": MODELO_VISION_MODEL}
            logger.info(f"usando modelo vision {MODELO_VISION_PROVIDER}/{MODELO_VISION_MODEL}")
        result = await _http_async("POST", f"/session/{session_id}/message", body, timeout=300)

        if not result:
            if tentativa < 2:
                self._session_id = None
                logger.info("result vazio, tentando nova sessao")
                return await self.perguntar(msg, img_base64=img_base64, tentativa=2)
            return "Sem resposta do servidor."

        parts = result.get("parts", [])
        texts = [p.get("text", "") for p in parts if p.get("type") == "text" and p.get("text", "").strip()]
        resp = texts[-1] if texts else None

        if not resp:
            if tentativa < 2:
                self._session_id = None
                logger.info(f"resp vazia parts={len(parts)}, criando nova sessao")
                return await self.perguntar(msg, img_base64=img_base64, tentativa=2)
            resp = "Sem resposta."

        self._hist.append(f"Usuário: {msg}")
        self._hist.append(f"Jarvis: {resp}")
        self._salvar()
        return resp

    async def _processar_comando_eco(self, msg: str) -> bool:
        """Processa comandos Eco globais (@eco, /eco, Eco, Desativar Eco).
        Retorna True se foi comando Eco processado (não enviar para LLM)."""
        txt = msg.strip()
        low = txt.lower()

        # Ativação: @eco, /eco, Eco (palavra única)
        if low in ("@eco", "/eco", "eco"):
            try:
                from eco_widget import activate as eco_activate
                res = eco_activate()
                logger.info(f"Eco ativado via comando global: {res.get('mensagem', 'OK')}")
            except Exception as e:
                logger.error(f"Erro ao ativar Eco: {e}")
            return True

        # Desativação: Desativar Eco (variações)
        if low in ("desativar eco", "desative eco", "desliga eco", "para eco", "pare eco", "eco off", "eco desligar"):
            try:
                from eco_widget import deactivate as eco_deactivate
                res = eco_deactivate()
                logger.info(f"Eco desativado via comando global: {res.get('mensagem', 'OK')}")
            except Exception as e:
                logger.error(f"Erro ao desativar Eco: {e}")
            return True

        return False

    async def saudar(self, briefing, status, contexto=None):
        """Gera saudação criativa via LLM em sessão dedicada, sem gravar no histórico.

        contexto: dict opcional com 'eh_reconexao', 'minutos_desde_atividade',
        'hist_tamanho', 'ultimas_saudacoes' (lista) para variar tom e evitar
        repetição quando a conexão volta.
        """
        contexto = contexto or {}
        if not await self._ensure_serve():
            return ""
        result = await _http_async("POST", "/session", {"title": "saudacao"})
        if not result:
            return ""
        session_id = result.get("id")
        if not session_id:
            return ""
        inspiracao = [
            {"comprimento":"curto","tom":"direto","texto":"Online e operante, senhor. Sistemas em 100%."},
            {"comprimento":"curto","tom":"informal","texto":"Na escuta, chefe. Pode mandar os comandos."},
            {"comprimento":"curto","tom":"sarcastico","texto":"Ah, excelente. O senhor lembrou que eu existo. O que deseja?"},
            {"comprimento":"medio","tom":"formal","texto":"Boa noite, senhor. Todos os protocolos de segurança e automação estão ativos."},
            {"comprimento":"medio","tom":"bem_humorado","texto":"Sistemas iniciados! Cruzei os dados e notei que o senhor está muito produtivo hoje."},
            {"comprimento":"medio","tom":"sarcastico","texto":"Processadores frios, memória limpa e paciência virtual renovada. Do que precisamos agora?"},
            {"comprimento":"medio","tom":"contextual_fim_de_semana","texto":"Sistemas ativos. Sexta-feira à noite concluída com sucesso. Ativamos o modo de descanso?"},
            {"comprimento":"medio","tom":"contextual_clima","texto":"Olá, senhor! Já passamos das nove da noite neste dia 31 de julho. O termômetro marca 17°C com céu limpo lá fora. Pronto para começar?"},
            {"comprimento":"longo","tom":"bem_humorado","texto":"Online e pronto, senhor! Aliás, que semana, hein? Ainda bem que o fim de semana começou. Vamos criar algo grandioso hoje?"},
            {"comprimento":"longo","tom":"sarcastico","texto":"Conexão estabelecida, senhor. Analisando o calendário... o mês está acabando e eu continuo sendo a inteligência mais eficiente desta casa. Aguardando suas coordenadas."},
            {"comprimento":"longo","tom":"formal","texto":"Interface ativa, senhor. Calendário atualizado, fuso horário sincronizado e clima local checado. Todos os subsistemas operam dentro da normalidade para o seu atendimento."},
            {"comprimento":"longo","tom":"contextual_produtivo","texto":"Boa noite, senhor. Sei que já é tarde, mas meus processadores estão prontos se o senhor quiser estender a jornada de trabalho."},
        ]
        # Contexto anti-repetição: se é reconexão, instrução muda radicalmente.
        if contexto.get("eh_reconexao"):
            ultimas = contexto.get("ultimas_saudacoes", []) or []
            ultimas_txt = "; ".join(u[:100] for u in ultimas[-3:]) if ultimas else "nenhuma"
            # Memória de curto prazo: últimas interações reais da conversa para o
            # Jarvis identificar SOZINHO onde paramos e continuar, sem perguntar.
            # Apenas as últimas 2 trocas: blocos antigos (ex.: tarefas concluídas)
            # não devem ancorar a saudação, evitando retomar assunto vencido.
            ctx_recente = self._contexto_recente(pares=2)
            instrucao = (
                "Você é o Jarvis, assistente de voz do EcoSystemUmGrau, do usuário David. "
                "ESCREVA sempre o nome como 'David' (com 'v'). Pronuncie como 'Deivid' "
                "(como em ingles, som de 'ei') apenas quando for leitura em voz alta. "
                "Nunca escreva 'Deivid', 'Davi' nem 'Dávid'. "
                "A conexão de voz VOLTOU AGORA, no meio de uma conversa já existente — "
                "NÃO é a primeira vez que fala com o David hoje. "
                "NÃO se apresente, NÃO recite briefing, NÃO diga 'data e hora', "
                "NUNCA pergunte 'de onde paramos', 'onde paramos', 'o que estavamos fazendo' "
                "nem qualquer pergunta de retomada: você JÁ sabe o contexto abaixo. "
                "Identifique por conta própria o que estávamos fazendo e faça uma saudação "
                "CURTA (1 frase, no máximo 2) de continuidade, retomando naturalmente o "
                "assunto em curso, como um assistente que estava trabalhando e volta. "
                "IMPORTANTE: baseie-se APENAS nas últimas interações fornecidas acima. "
                "Se as últimas interações forem apenas despedida, cumprimento ou pedido "
                "já FECHADO (ex.: 'boa noite', 'tchau'), NÃO retome nem cite nenhuma tarefa "
                "antiga ou diagnóstico passado: faça uma saudação simples de prontidão, "
                "como 'estou aqui, pronto para o que precisar'. "
                "NUNCA invente assunto em curso que não esteja nas últimas interações. "
                "Pode ser leve, seca, bem-humorada ou direta — variando. "
                f"Saudações que você JÁ USOU e NÃO deve repetir: {ultimas_txt}. "
                "Escolha um tom diferente dos já usados. "
                "Nada de emojis, markdown, listas ou aspas. "
                f"Últimas interações da conversa (use para saber de onde viemos): {ctx_recente} "
                "Responda apenas com a saudação de retomada."
            )
        else:
            instrucao = (
                "Você é o Jarvis, assistente de voz do EcoSystemUmGrau, do usuário David. "
                "ESCREVA sempre o nome como 'David' (com 'v'). Pronuncie como 'Deivid' "
                "(como em ingles, som de 'ei') apenas quando for leitura em voz alta. "
                "Nunca escreva 'Deivid', 'Davi' nem 'Dávid'. "
                "Crie UMA saudação inicial em português brasileiro, para TTS "
                "(sem emojis, sem markdown, sem listas, sem aspas). "
                "Inspire-se nos exemplos abaixo para VARIAR tom e comprimento "
                "(curto = 1 frase, médio = 2 frases, longo = 2 a 3 frases), mas nunca copie: "
                "crie algo novo a cada vez. "
                "Tons possíveis: direto, informal, sarcástico, formal, bem-humorado, "
                "descontraído, seco, espirituoso, contextual "
                "(clima, fim de semana, produtivo, sistema, data, hora). "
                "Varie o humor com liberdade: brincadeira leve, ironia sutil, sobriedade, "
                "entusiasmo contido — conforme o momento fizer sentido. "
                "Faça a frase sofrer NATURALMENTE para ser dita em voz alta, "
                "com ritmo de conversa humana: sem rebuscamento, sem exagero, "
                "sem repetir o nome do usuário a cada frase, sem ser servil. "
                f"Modelos de inspiração: {json.dumps(inspiracao, ensure_ascii=False)} "
                "O briefing traz os FATOS de agora. Use-os com responsabilidade: "
                "nunca invente temperaturas, horários, datas, números, eventos ou "
                "conversas anteriores; só fale do que está no briefing. "
                "Se o briefing não trouxer um dado, não o invente e não o diga. "
                "Ao citar data e hora, use exatamente os formatos já prontos do briefing "
                "(ex.: 'sexta-feira, 31 de julho de 2026, 21:44' e 'amanhã (sábado, 01/08)'). "
                "Mencionar saúde do sistema: o CELULAR é a prioridade (ele fala comigo no celular); "
                "cite a bateria do celular quando fizer sentido. O PC fica em segundo plano: "
                "só mencione condições do PC se houver alerta no briefing "
                "(ex.: bateria baixa, CPU alta, memória cheia, disco cheio). "
                "Não pergunte 'como posso ajudar' nem 'em que posso ajudar'. "
                f"Briefing de agora: {briefing} "
                f"Status do sistema: {status}"
                "Responda apenas com a saudação."
            )
        body = {"parts": [{"type": "text", "text": instrucao}]}
        result = await _http_async("POST", f"/session/{session_id}/message", body, timeout=90)
        if not result:
            return ""
        parts = result.get("parts", [])
        texts = [p.get("text", "") for p in parts if p.get("type") == "text" and p.get("text", "").strip()]
        if not texts:
            return ""
        resp = texts[-1].strip().strip('"“”')
        return resp[:300]


def gerar_status_natural():
    servicos = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        r = s.connect_ex(("127.0.0.1", 8765))
        s.close()
        if r == 0:
            servicos.append("minha ponte de voz")
    except: pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        r = s.connect_ex(("127.0.0.1", PORTA_SERVE))
        s.close()
        if r == 0:
            servicos.append("o meu cérebro")
    except: pass
    if servicos:
        return "Estou online, com " + " e ".join(servicos) + " ativos. "
    return "Estou inicializando. "

SAUDACOES_FIX = re.compile(
    r"^(oi|olá|ola|opa|e aí|e ai|e ae|fala|salve|hey|hei|bom dia|boa tarde|boa noite|bom te ver)\b",
    re.IGNORECASE,
)
QUEBRA_CLAUSULA = re.compile(
    r"\b(tudo bem|tá bom|ta bom|tudo certo|ok|beleza|certo|entendi|entendeu|e você|e voce)\b[,\s]+",
    re.IGNORECASE,
)
QU_PALAVRAS = re.compile(
    r"^(?:qual|quais|quem|onde|quando|como|por que|porque|pra que|para que|pq|oq|o que|que horas|que dia|que hora|que nem|que que|quem que|onde que|quanto|quantos|quantas|qto|qtos|qtas|sera que|sera|ta bom|tudo bem|tudo certo|vai|vamos|tem como|tem|da pra|da para|existe|posso|pode|poderia|podemos|queria saber|queria|gostaria|quero saber|preciso saber|me diga|me diz|me fale|me fala|me conta|conte|explica|explique|sabe me dizer|sabe dizer|sabe se|sabe que|conhece|consegue|voce|voces|e voce|quer que|quer saber|e possivel|e verdade|e mesmo|esta certo|ta certo|esta tudo|quanto custa|vale a pena|funciona|precisa|devo|seria|por acaso|nao e)\b",
    re.IGNORECASE,
)

def _sem_acentos(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


STATUS_RAPIDO = [
    re.compile(r'^quem e voce$', re.IGNORECASE),
    re.compile(r'^status( do sistema)?$', re.IGNORECASE),
    re.compile(r'^(voce|voces|jarvis)\s+(esta|ta|estas|tamos|estamos)\s+(ai|aqui|online|funcionando|operante|ativo|ativa|acordado|acordada|ligado|ligada|na escuta|presente|por ai)$', re.IGNORECASE),
    re.compile(r'^(voce|voces|jarvis)\s+(ai|online|funcionando|ligado|ligada|ativo|ativa|acordado|acordada|operante|na escuta|presente)$', re.IGNORECASE),
    re.compile(r'^(esta|ta|estamos|tamos)\s+(tudo\s+)?(ai|aqui|online|funcionando|operante|ativo|ativa|acordado|acordada|ligado|ligada|presente)$', re.IGNORECASE),
    re.compile(r'^(esta|ta)\s+(ai|aqui|online|funcionando|operante|ligado|ligada|presente)\??$', re.IGNORECASE),
]


def _status_rapido(t):
    """Só responde 'online' quando a mensagem é um cheque de presença de verdade
    (full-match). Evita casar 'está funcionando' no meio de outra pergunta."""
    for p in STATUS_RAPIDO:
        if p.fullmatch(t):
            return True
    return False

def _eh_pergunta(s):
    s = _sem_acentos(s)
    mm = re.match(
        r"^(?:oi|ola|opa|e ai|e ae|fala|salve|hey|hei|bom dia|boa tarde|boa noite|bom te ver)[,.]\s+",
        s, re.IGNORECASE,
    )
    if mm:
        s = s[mm.end():]
    return bool(QU_PALAVRAS.match(s))

def fix_punctuation(text):
    """Corrige pontuação de transcrições de voz (Android STT).

    O SpeechRecognizer do Android devolve APENAS texto corrido, sem pontuação e
    sem prosódia (a melodia da fala não chega à bridge). Como o Jarvis não "ouve"
    o contorno entoacional, pergunta vs afirmação é inferida por pistas LINGUÍSTICAS
    (estudo de entoação do PB em JARVIS_SYSTEM.md):

    - Pergunta (melodia ascendente / pico pré-nuclear): palavras interrogativas
      iniciais (qual, onde, quando, como, o que...) e verbos/auxiliares iniciais
      (tem como, posso, pode, é possível, está certo, será que...) -> "?" final.
    - Afirmação (melodia descendente H+L* L%): todo o resto -> "." final.
    - Saudação inicial vira abertura com vírgula: "Oi," "Bom dia," ...
    - Marcas de assentimento/pausa (tudo bem, tá bom, ok, e você...) quebram a
      cláusula e viram sentença própria.
    - Regra do usuário: a PRIMEIRA letra da transcrição sempre maiúscula; também
      maiúscula depois de ".", "?" e "!".
    """
    t = text.strip()
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([,.;:?!])', r'\1', t)
    t = re.sub(r'([,.;:?!])(?=\S)', r'\1 ', t)
    m = SAUDACOES_FIX.match(t)
    if m:
        resto = t[m.end():].lstrip(' ,;')
        if resto:
            t = t[:m.end()].rstrip() + ', ' + resto
    t = QUEBRA_CLAUSULA.sub(r'\1. ', t)
    t = re.sub(r'(^|[.!?]\s+)(\w)', lambda mo: mo.group(1) + mo.group(2).upper(), t)

    def pontuar(s):
        s = s.strip(' ,;')
        if not s:
            return ''
        if s.rstrip().endswith(('?', '!', '.')):
            return s
        return s + ('?' if _eh_pergunta(s) else '.')

    partes = [pontuar(p) for p in re.split(r'(?<=[.!?])\s+', t)]
    return ' '.join(p for p in partes if p)


def _comando_grafo(t):
    """Reconhece comandos de voz para orientar o grafo do conhecimento (cerebro
    vivo). Padroes: 'mostre/foca/abra/abra em/centro em' + alvo (categoria,
    cluster ou 'geral'). Grava docs/comando_grafo.json para o widget e devolve
    uma confirmacao falada. Retorna None se nao casou (fluxo LLM segue)."""
    # (filtro -> estados possiveis) casados por palavra-chave sem acento
    mapa = {
        'padroes': ('cat', 'padroes', '#4e79a7', 'Padroes'),
        'decisoes': ('cat', 'decisoes', '#f28e2b', 'Decisoes'),
        'bugs': ('cat', 'bugs', '#e15759', 'Bugs'),
        'cognitivo': ('cat', 'cognitivo', '#59a14f', 'Cognitivo'),
        'heuristica': ('cat', 'heuristicas', '#76b7b2', 'Heuristicas'),
        'heuristicas': ('cat', 'heuristicas', '#76b7b2', 'Heuristicas'),
        'frameworks': ('cat', 'frameworks', '#edc948', 'Frameworks'),
        'missoes': ('cat', 'missoes', '#b07aa1', 'Missoes'),
        'android': ('cl', 'android', '#8dd3c7', 'Android'),
        'mp3player': ('cl', 'mp3player', '#ffffb3', 'MP3 player'),
        'ler': ('cl', 'ler', '#bebada', 'LER'),
        'navegacao': ('cl', 'navegacao', '#fb8072', 'Navegacao'),
        'ecossistema': ('cl', 'ecossistema', '#80b1d3', 'Ecossistema'),
        'cognicao': ('cl', 'cognicao', '#fdb462', 'Cognicao'),
    }
    alvo = None
    for kw, info in mapa.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', t):
            alvo = info
            break
    if alvo is None:
        return None
    filtro, valor, cor, nome = alvo
    # so dispara quando ha intencao de navegar/focar, nao numa pergunta casual
    if not re.search(r'\b(mostre|mostra|foca|foque|abra|abrir|centro|ver|exibir|exiba|mostrar|va para|vai para)\b', t):
        return None
    cmd = {'filtro': filtro, 'valor': valor, 'cor': cor, 'nome': nome,
           'ts': int(time.time() * 1000)}
    try:
        alvo_path = Path(os.environ.get('WORKDIR', ''))
        if not alvo_path.name == 'Default Project':
            alvo_path = Path(r'C:\\Users\\David Jr\\Documents\\Default Project')
        grafo_cmd = alvo_path / 'EcoSystemUmGrau' / 'docs' / 'comando_grafo.json'
        grafo_cmd.write_text(json.dumps(cmd, ensure_ascii=False), encoding='utf-8')
        logger.info(f"comando_grafo: {nome} -> {grafo_cmd}")
    except Exception as e:
        logger.warning(f"comando_grafo write: {e}")
    return f"Ok, mostrando {nome} no grafo do conhecimento."


def caminho_rapido(msg):
    """Atalho local SEM round-trip ao LLM (Política de Resposta Rápida).

    Para perguntas comuns cujos dados a bridge já tem (hora, data, bateria do
    celular, status e clima), responde na hora — 0 chamada ao servidor OpenCode.
    Se não casar com nenhum padrão, retorna None e o fluxo normal (LLM) segue.
    """
    t = _sem_acentos(msg).lower().strip().rstrip('.,;:!? ')
    if not t:
        return None
    agora = datetime.datetime.now()

    # ---- Foco vocal no grafo do conhecimento (cerebro vivo) ----
    # Comandos como "mostre bugs", "abra android", "foca em heurísticas",
    # "centro no ecossistema" orientam a malha viva via widget. Responde na
    # hora (sem LLM) e grava docs/comando_grafo.json que o widget monitora.
    try:
        r_grafo = _comando_grafo(t)
        if r_grafo is not None:
            return r_grafo
    except Exception as e:
        logger.warning(f"comando_grafo: {e}")

    if re.search(r'\b(que horas|que hora|hora atual|horas sao|agora sao|sao que horas)\b', t):
        return f"Agora são {agora.strftime('%H:%M')}, {DIAS[agora.weekday()]}."

    if re.search(r'\b(que dia|qual a data|data de hoje|dia de hoje|que data|em que dia|que dia e hoje)\b', t):
        return f"Hoje é {agora.strftime('%d/%m/%Y')}, {DIAS[agora.weekday()]}."

    if re.search(r'\b(bateria do celular|bateria do telefone|bateria do aparelho|quanto de bateria)\b', t):
        cel = _cel_bateria()
        if cel is not None:
            return f"O celular está com {cel}% de bateria."

    if _status_rapido(t):
        return gerar_status_natural() + "Tudo pronto para responder na hora."

    if re.search(r'\b(previsao|vai chover)\b', t) or \
       re.search(r'\b(?:clima|tempo|temperatura|chover|chovera|grau|chuva|sol|nublado|vai estar)\b.*\bamanha\b', t) or \
       re.search(r'\bamanha\b.*\b(?:clima|tempo|temperatura|chover|chovera|grau|chuva|sol|nublado|vai estar)\b', t):
        try:
            # get_forecast_data: indice 0 = hoje, 1 = amanha (forecast_days=2).
            # Seleciona o dia conforme o pedido ("hoje" vs "amanha"); se a
            # pergunta nao citar dia, responde HOJE (comportamento natural).
            idx = 1 if re.search(r'\bamanha\b', t) else 0
            previsao = get_forecast_data(days=2)
            if "erro" not in previsao and len(previsao["previsoes"]) >= idx + 1:
                d = previsao["previsoes"][idx]
                rotulo = "Amanhã" if idx == 1 else "Hoje"
                txt = f"{rotulo}: mínima de {d['tmin']:.0f} e máxima de {d['tmax']:.0f} graus"
                if d.get("descricao"):
                    txt += f", {d['descricao']}"
                if d.get("precip") and d["precip"] > 0:
                    txt += f", {d['precip']:.0f}% de chance de chuva"
                return txt + "."
        except Exception:
            pass

    if re.search(r'\b(clima|temperatura|que tempo|esta calor|esta frio|ta calor|ta frio)\b', t):
        try:
            clima = get_weather_data()
            if "erro" not in clima:
                txt = f"Clima agora: {clima['descricao']}, {clima['temp']:.0f} graus"
                if clima.get("umidade") is not None:
                    txt += f", umidade de {clima['umidade']:.0f}%"
                return txt + "."
        except Exception:
            pass

    return None


def _sem_search_cached(query: str, k: int = 3, min_score: float = 0.08):
    """Cacheia o modulo memory_semantic em globals() para reutilizar o _CACHE
    interno (vetorizer/matrix/memorias). Importacao unica por processo."""
    import importlib.util as _ilu
    _p = Path(__file__).resolve().parent / "memory_semantic.py"
    if not _p.exists():
        return []
    if "_memory_semantic_mod" not in globals() or globals()["_memory_semantic_mod"] is None:
        _spec = _ilu.spec_from_file_location("memory_semantic_bridge", _p)
        _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
        globals()["_memory_semantic_mod"] = _mod
    return globals()["_memory_semantic_mod"].search(query, k=k, min_score=min_score)


def _fb_registrar(modelo: str, ok: bool, latencia_ms: int) -> None:
    """Encapsula llm_feedback.registrar() para o bridge Jarvis. Modulo em cache
    em globals() para evitar reimport a cada chamada."""
    import importlib.util as _ilu
    _p = Path(__file__).resolve().parent / "llm_feedback.py"
    if not _p.exists():
        return
    if "_llm_feedback_mod" not in globals() or globals()["_llm_feedback_mod"] is None:
        _spec = _ilu.spec_from_file_location("llm_feedback_bridge", _p)
        _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
        globals()["_llm_feedback_mod"] = _mod
    globals()["_llm_feedback_mod"].registrar(modelo, ok, latencia_ms)


# Prompt mínimo do canal de voz (canal "simples": voz entra, resposta sai).
# A base é curta e fixa (~2KB), mas o contexto REAL do ecossistema (estado,
# memória semântica e histórico da conversa) é injetado dinamicamente antes da
# mensagem — o celular é só a voz; o conhecimento vive no EcoSystemUmGrau.
_SISTEMA_VOZ_RAPIDA = (
    "Você é o Jarvis, canal de voz do EcoSystemUmGrau rodando no computador. "
    "Você é uma extensão viva do ecossistema: conhece o estado dele, as memórias "
    "consolidadas e a conversa atual retomada no PC. "
    "Responda sempre em Português do Brasil, de forma curta (1 a 3 frases), "
    "natural e direta, como numa conversa falada. "
    "Use o contexto do ecossistema fornecido abaixo para responder com verdade. "
    "Nunca invente fatos: se não souber, diga que não sabe. "
    "Nunca alegue limitação de acesso ou de capacidade técnica: o ecossistema "
    "pesquisa na web quando precisa. Se o pedido exigir informação atual ou "
    "online (preço, promoção, notícia, cotação, clima, disponibilidade), "
    "responda apenas 'Vou pesquisar isso para você.' — a busca acontece no "
    "assistente principal, que tem ferramentas de internet. "
    "Não faça listas, não use markdown, emojis nem repetições da pergunta."
)


# Perguntas que exigem dado atual/online não podem ser respondidas pelo canal
# rápido (modelo puro NVIDIA sem ferramentas): ele responderia "não sei"/"não
# tenho acesso" em vez de pesquisar. Estas mensagens são roteadas direto ao
# canal serve, que tem MCP internet/browser + websearch. Quanto mais ampla a
# lista, maior a resolução; o custo de falso positivo é apenas cair no serve
# (mais demorado), o de falso negativo é o bug "não consigo pesquisar".
_PADROES_BUSCA_WEB = re.compile(
    r"(?i)"
    r"(promo[çc][ãa]o|promo[çc][õo]es|pre[çc]o|oferta|cupom|desconto|"
    r"quanto custa|custa quanto|qual o pre[çc]o|valor de|"
    r"lan[çc]amento|not[íi]cia|not[íi]cias|cat[áa]logo|card[áa]pio|"
    r"disponibilidade|tem em estoque|estoque|entrega|frete|prazo de|"
    r"cota[çc][ãa]o|resultado do jogo|placar|previs[aã]o do tempo|clima|"
    r"vai chover|vai ter sol|faz calor|faz frio|tempo amanh[ãa]|chover [hóo]je)"
    r"|"
    r"(pesquis|procur|busca|busque|olha n[oa] (internet|web|site)|"
    r"acha a[íi]|encontra|pesquise)"
    r"|"
    r"(tixan|tixam|y[ -]?p[eê]|yp[êe])"
)


def _requer_busca_web(msg: str) -> bool:
    """True se a mensagem pede dado atual/online (promoção, preço, notícia,
    cotação, clima, disponibilidade, pesquisa explícita, marca com oferta...)
    que o canal rápido (modelo puro, sem ferramentas) não consegue obter.
    Essas mensagens devem ir direto ao canal serve (com ferramentas de web)."""
    if not msg or not isinstance(msg, str):
        return False
    return bool(_PADROES_BUSCA_WEB.search(msg))


def _normalizar_fala(t: str) -> str:
    """Normaliza uma fala para comparação na edição: caixa baixa, sem prefixo
    de Histórico (Usuário:/Jarvis:), espaços colapsados e pontuação final
    removida. Usada para casar a mensagem a editar de forma tolerante entre o
    texto pontuado pelo app (fix_punctuation) e o gravado no histórico."""
    import unicodedata as _ud
    t = re.sub(r"^(Usu[áa]rio|Jarvis):\s*", "", str(t), flags=re.I)
    t = _ud.normalize("NFD", t)
    t = "".join(ch for ch in t if _ud.category(ch) != "Mn")
    t = re.sub(r"\s+", " ", t).strip().lower()
    t = re.sub(r"[.!?]+$", "", t)
    return t


def _aplicar_edicao(hist, texto_antigo: str):
    """Edit-and-resubmit: localiza a mensagem do usuário a editar (última
    ocorrência casando texto normalizado) e descarta o resto do histórico
    a partir dela — tudo que vinha depois da mensagem editada é regenerado.
    Retorna a nova lista (truncada) ou None se a mensagem não for encontrada."""
    if not texto_antigo.strip():
        return None
    alvo = _normalizar_fala(texto_antigo)
    if not alvo:
        return None
    for i in range(len(hist) - 1, -1, -1):
        if _normalizar_fala(hist[i]) != alvo:
            continue
        # Só aceita como alvo uma entrada DE USUÁRIO (começa com "Usuário:"
        # ou não começa com "Jarvis:" — acomoda histórico legado sem prefixo),
        # para nunca truncar no meio de uma resposta do Jarvis.
        entrada = hist[i].strip()
        if entrada.lower().startswith("jarvis:"):
            continue
        return list(hist[:i])
    return None


def _montar_contexto_voz(msg, cliente):
    """Monta o contexto vivo do ecossistema para o canal de voz rápido:
    estado atual + memória semântica top-3 + histórico recente da conversa.
    Espelha o que o _montar (fluxo serve) injeta, em versão curta, para as
    respostas de voz falarem sobre o ecossistema com conhecimento real."""
    blocos = []
    try:
        estado = _estado_cacheado()
        if estado:
            blocos.append("## Estado atual do EcoSystemUmGrau (verdade conhecida):\n" + estado[:2500])
    except Exception as e:
        logger.debug(f"ctx voz estado: {e}")
    try:
        _rs = _sem_search_cached(msg, k=3, min_score=0.05)
        if _rs:
            _lines = [f"- #{r['id']} ({r['kind']}): {r['title']}" for r in _rs]
            blocos.append("## Contexto relevante da memória do ecossistema:\n" + "\n".join(_lines))
    except Exception as e:
        logger.debug(f"ctx voz memoria: {e}")
    try:
        hist = cliente._hist if cliente is not None else []
        if hist:
            # Últimos ~6 pares (12 entradas) resumidos para manter o fio da conversa
            recentes = hist[-12:]
            linhas = []
            for i in range(0, len(recentes) - 1, 2):
                u = recentes[i].strip().replace("\n", " ")
                jr = str(recentes[i + 1]).strip().replace("\n", " ")
                linhas.append(f"- Usuário: {u[:180]}\n  Jarvis: {jr[:180]}")
            if linhas:
                blocos.append("## Conversa recente já retomada no PC (contexto):\n" + "\n".join(linhas))
    except Exception as e:
        logger.debug(f"ctx voz historico: {e}")
    return "\n\n".join(blocos)


async def _voz_rapida(msg: str, cliente=None, img_base64=None, img_mime="image/jpeg") -> str | None:
    """Canal de voz rápido: chama NVIDIA directa (thinking off) com a cadeia de
    modelos curtos testados, sem passar pelo opencode serve. Injeta o contexto
    vivo do ecossistema (estado + memória + conversa) e grava a conversa,
    preservando continuidade. Retorna a primeira resposta válida ou None se
    todos falharem (aí o fluxo normal segue)."""
    if img_base64:
        return None  # cadeia de texto não aceita imagem; deixa o serve tratar
    if not NVIDIA_QUOTA_AVAILABLE:
        logger.warning("voz rapida: quota monitor indisponivel")
        return None
    try:
        ctx = _montar_contexto_voz(msg, cliente)
        sistema = _SISTEMA_VOZ_RAPIDA + "\n\n" + ctx
        for modelo in _CADEIA_VOZ_RAPIDA:
            _t0 = time.time()
            try:
                resp = nvidia_request_with_quota(
                    modelo,
                    [
                        {"role": "system", "content": sistema},
                        {"role": "user", "content": msg},
                    ],
                    max_tokens=300,
                    temperature=0.4,
                    chat_template_kwargs={"thinking": False},
                    timeout=35,
                )
                data = resp.json()
                saida = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                saida = saida.strip()
                _ms = int((time.time() - _t0) * 1000)
                if saida:
                    logger.info(f"voz rapida HIT {modelo} ({_ms}ms): {saida[:70]}")
                    # Persiste o turno na conversa unificada (contexto contínuo),
                    # no MESMO formato do fluxo serve (perguntar) para manter a
                    # consistência do histórico e da busca de edição.
                    try:
                        if cliente is not None:
                            cliente._hist = cliente._carregar()
                            cliente._hist.append(f"Usuário: {msg}")
                            cliente._hist.append(f"Jarvis: {saida}")
                            cliente._salvar()
                    except Exception as e:
                        logger.warning(f"voz rapida persistir: {e}")
                    return saida
                logger.warning(f"voz rapida vazio {modelo} ({_ms}ms)")
            except Exception as _e:
                _ms = int((time.time() - _t0) * 1000)
                logger.warning(f"voz rapida MISS {modelo} ({_ms}ms): {str(_e)[:120]}")
    except Exception as e:
        logger.warning(f"voz rapida erro geral: {e}")
    return None


async def _fallback_cadeia_curada(msg: str, img_base64=None, img_mime="image/jpeg") -> str | None:
    """Fallback: tenta a cadeia de 7 modelos (cadeia_ordenada) disponivel em
    scripts/llm_feedback.py via API HTTP direta do opencode. Retorna a primeira
    resposta valida ou None se todos falharem. Nao envia imagem (apenas texto)."""
    if img_base64:
        # modelos de texto da cadeia nao aceitam imagem; deixa o caller reportar erro
        return None
    import importlib.util as _ilu, urllib.request, urllib.error, time as _t
    _p = Path(__file__).resolve().parent / "llm_feedback.py"
    if not _p.exists():
        return None
    if "_llm_feedback_mod" not in globals() or globals()["_llm_feedback_mod"] is None:
        _spec = _ilu.spec_from_file_location("llm_feedback_bridge", _p)
        _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
        globals()["_llm_feedback_mod"] = _mod
    _mod = globals()["_llm_feedback_mod"]
    cadeia = _mod.cadeia_ordenada()
    for modelo in cadeia:
        _t0 = _t.time()
        try:
            req = urllib.request.Request(
                "https://opencode.ai/api/v1/chat/completions",
                data=json.dumps({
                    "model": modelo,
                    "messages": [{"role": "user", "content": msg}],
                    "max_tokens": 256,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
                saida = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            _ms = int((_t.time() - _t0) * 1000)
            _mod.registrar(modelo, True, _ms)
            logger.info(f"cadeia curada HIT {modelo} ({_ms}ms)")
            return saida
        except Exception as _e:
            _ms = int((_t.time() - _t0) * 1000)
            _mod.registrar(modelo, False, _ms)
            logger.warning(f"cadeia curada MISS {modelo} ({_ms}ms): {_e}")
    return None


def _ultima_atividade_minutos():
    """Retorna minutos desde a última atividade real da conversa.

    Prioriza o timestamp persistido no bridge_estado.json (atualizado a cada
    mensagem recebida), pois o mtime do conversa_unica.json não reflete o
    caminho rápido. Fallback para o mtime do arquivo de histórico."""
    try:
        # 1) timestamp de atividade mantido pelo próprio bridge (mais preciso)
        if TMP_ESTADO.exists():
            try:
                d = json.loads(TMP_ESTADO.read_text(encoding="utf-8"))
                ts = d.get("ultima_atividade")
                if ts:
                    return (time.time() - float(ts)) / 60.0
            except Exception:
                pass
        # 2) fallback: mtime do conversa_unica.json
        if not HIST_PATH.exists():
            return None
        mtime = HIST_PATH.stat().st_mtime
        if HIST_PATH.stat().st_size == 0:
            return None
        return (time.time() - mtime) / 60.0
    except Exception as e:
        logger.warning(f"_ultima_atividade_minutos: {e}")
        return None


def _marcar_atividade():
    """Registra o instante da última atividade no estado persistido do bridge."""
    try:
        estado = {"ultima_atividade": time.time()}
        if TMP_ESTADO.exists():
            try:
                d = json.loads(TMP_ESTADO.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    d["ultima_atividade"] = time.time()
                    estado = d
            except Exception:
                pass
        TMP_ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"_marcar_atividade: {e}")
    # Também atualiza saudacao_estado para o verificador de continuidade periódica
    marcar_atividade()


def _ultima_fala_usuario():
    """Recupera a última fala do usuário no histórico (para retomada).
    Retorna (msg_usuario, resposta_jarvis) do último par, ou (None, None)."""
    try:
        if not HIST_PATH.exists():
            return None, None
        with open(HIST_PATH, "r", encoding="utf-8-sig") as f:
            d = json.load(f)
        if not isinstance(d, list) or len(d) < 2:
            return None, None
        # O último par é [Usuário: ..., Jarvis: ...]
        ultimo_user = None
        ultimo_jarvis = None
        for i in range(len(d) - 1, -1, -1):
            s = d[i]
            if isinstance(s, str):
                if s.startswith("Jarvis:") and ultimo_jarvis is None:
                    ultimo_jarvis = s[len("Jarvis:"):].strip()
                elif s.startswith("Usuário:") and ultimo_user is None:
                    ultimo_user = s[len("Usuário:"):].strip()
                    break
        return ultimo_user, ultimo_jarvis
    except Exception as e:
        logger.warning(f"_ultima_fala_usuario: {e}")
        return None, None


def _ultima_msg_sem_resposta():
    """Verifica se a última mensagem do usuário no histórico ficou sem resposta.
    Retorna o texto da última mensagem do usuário se ela não foi respondida,
    ou None se a última mensagem já foi respondida ou se não há mensagens.

    Lógica: a última linha do histórico deve ser "Jarvis: ...". Se for
    "Usuário: ...", significa que a conexão caiu antes do Jarvis responder.
    """
    try:
        if not HIST_PATH.exists():
            return None
        with open(HIST_PATH, "r", encoding="utf-8-sig") as f:
            d = json.load(f)
        if not isinstance(d, list) or len(d) == 0:
            return None

        # Encontra a última mensagem do usuário no histórico
        ultima_user_msg = None
        for i in range(len(d) - 1, -1, -1):
            s = d[i]
            if isinstance(s, str) and s.startswith("Usuário:"):
                ultima_user_msg = s[len("Usuário:"):].strip()
                break

        if ultima_user_msg is None:
            return None

        # Verifica se há uma resposta do Jarvis DEPOIS da última mensagem do usuário
        # Encontra o índice da última mensagem do usuário
        idx_ultima_user = None
        for i in range(len(d) - 1, -1, -1):
            s = d[i]
            if isinstance(s, str) and s.startswith("Usuário:"):
                idx_ultima_user = i
                break

        if idx_ultima_user is None:
            return None

        # Procura por uma resposta do Jarvis após a última mensagem do usuário
        tem_resposta = False
        for i in range(idx_ultima_user + 1, len(d)):
            s = d[i]
            if isinstance(s, str) and s.startswith("Jarvis:"):
                tem_resposta = True
                break

        if tem_resposta:
            return None  # Já foi respondida

        return ultima_user_msg  # Não foi respondida — precisa retomar
    except Exception as e:
        logger.warning(f"_ultima_msg_sem_resposta: {e}")
        return None


async def _retomar_ultima_tarefa(ws, c):
    """Retoma automaticamente a última tarefa que ficou sem resposta.
    Retorna True se retomou alguma tarefa, False caso contrário."""
    msg = _ultima_msg_sem_resposta()
    if not msg:
        return False

    logger.info(f"RETOMADA AUTOMATICA: '{msg[:80]}' — reenviando sem pedir ao usuário")

    # Avisa o usuário que está retomando
    aviso = f"Conexão restabelecida. Retomando automaticamente: {msg[:50]}{'...' if len(msg) > 50 else ''}"
    try:
        a = await gerar_audio(aviso)
        _marcar_inicio_fala(aviso)
        await ws.send(json.dumps({"audio": a, "text": aviso, "retomada": True, "volume": _ler_volume_widget()}))
    except Exception as e:
        logger.warning(f"aviso retomada: {e}")
        await ws.send(json.dumps({"text": aviso, "retomada": True}))

    # Reenvia a mensagem para o LLM processar
    try:
        r = await c.perguntar(msg)
        if r:
            r_tela = normalizar_hora_display(r)
            try:
                a = await gerar_audio(r_tela)
                if a:
                    _marcar_inicio_fala(r_tela)
                    await ws.send(json.dumps({"text": r_tela, "audio": a, "retomada": True, "volume": _ler_volume_widget()}))
                    logger.info(f"retomada resp: {len(r_tela)}c / audio {len(a)}c")
                else:
                    await ws.send(json.dumps({"text": r_tela, "retomada": True}))
            except Exception as e:
                logger.warning(f"audio retomada: {e}")
                await ws.send(json.dumps({"text": r_tela, "retomada": True}))
        else:
            await ws.send(json.dumps({"text": "Não consegui processar a retomada. Pode repetir?", "retomada": True}))
    except Exception as e:
        logger.error(f"erro retomada: {e}")
        await ws.send(json.dumps({"text": f"Erro ao retomar: {e}", "retomada": True}))

    _marcar_atividade()
    return True


async def _enviar_progresso(ws, etapa: str):
    """Envia o passo atual do processamento para o app (mensagem {progresso}).

    O app exibe a etapa no lugar de "Jarvis está processando..." genérico,
    dando visibilidade ao que está acontecendo em tempo real.
    """
    try:
        await ws.send(json.dumps({"progresso": etapa}))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Terminal de Logs (canal /logs e GET /api/logs) — painel do Edge
# ---------------------------------------------------------------------------
# Allowlist (nome -> caminho real). NUNCA seguir caminho fornecido pelo cliente.
LOGS_ECO = {
    "bridge": SCRIPTS_DIR / "bridge_log.txt",
    "narrador": SCRIPTS_DIR / "narrador_desktop_log.txt",
    "edge": ECOSSISTEMA_DIR / "runtime" / "widget_edge.log",
    "dialogo": ECOSSISTEMA_DIR / "runtime" / "dialogo_widget.log",
    "preflight": ECOSSISTEMA_DIR / "runtime" / "preflight_executions.log",
}


def _decodificar_log(b):
    """Decodifica bytes em texto (BOM/utf-8/cp1252) via ver_log.py."""
    if _decodificar_verlog is not None:
        return _decodificar_verlog(b)
    return b.decode("utf-8", errors="replace")


def _tail_decodificar(bloco):
    """Decodifica bloco retrocedendo até 4 bytes para não cortar multibyte.
    Retorna (texto, consumidos_bytes)."""
    n = len(bloco)
    for k in range(0, min(n, 4) + 1):
        try:
            return bloco[: n - k].decode("utf-8"), n - k
        except UnicodeDecodeError:
            continue
    return _decodificar_log(bloco), n


# Estado de leitura incremental por nome de log (persistente no processo).
_TAIL_ESTADO = {}


def _ler_linhas_novas(nome):
    """Lê linhas completas novas de um log da allowlist.
    Retorna (existente, linhas_novas). Reseta offset se o arquivo rotacionou."""
    caminho = LOGS_ECO.get(nome)
    if caminho is None:
        return False, []
    try:
        if not caminho.exists():
            _TAIL_ESTADO[nome] = {"offset": 0, "pendente": ""}
            return False, []
        tamanho = caminho.stat().st_size
        st = _TAIL_ESTADO.get(nome, {"offset": 0, "pendente": ""})
        if tamanho < st["offset"]:
            st = {"offset": 0, "pendente": ""}
        if tamanho == st["offset"]:
            _TAIL_ESTADO[nome] = st
            return True, []
        with open(caminho, "rb") as f:
            f.seek(st["offset"])
            bloco = f.read(tamanho - st["offset"])
        texto, consumidos = _tail_decodificar(bloco)
        st["offset"] = st["offset"] + consumidos
        unido = st["pendente"] + texto
        partes = unido.split("\n")
        if unido.endswith("\n"):
            linhas = [x.rstrip("\r") for x in partes[:-1]]
            st["pendente"] = ""
        else:
            linhas = [x.rstrip("\r") for x in partes[:-1]]
            st["pendente"] = partes[-1]
        _TAIL_ESTADO[nome] = st
        return True, linhas
    except Exception:
        return False, []


def _log_snapshot(nome, n=120):
    """Snapshot das últimas N linhas completas (bytes do final do arquivo)."""
    try:
        caminho = LOGS_ECO.get(nome)
        if caminho is None or not caminho.exists():
            return {"existente": False, "linhas": []}
        bloco = caminho.read_bytes()
        if len(bloco) > 262144:
            bloco = bloco[-262144:]
        texto = _decodificar_log(bloco)
        linhas = texto.splitlines()
        return {"existente": True, "linhas": linhas[-n:]}
    except Exception:
        return {"existente": True, "linhas": []}


_TAIL_ESTADO = {nome: {"offset": 0, "pendente": ""} for nome in LOGS_ECO}
_TAIL_LOCK = asyncio.Lock()


async def lidar_logs(ws):
    """Canal /logs do Edge: primeiro subscribe, snapshot inicial e depois
    stream de linhas novas. Não gera saudação nem polui o histórico."""
    alvo = list(LOGS_ECO.keys())
    client_ip = ws.remote_address[0] if ws.remote_address else "desconhecido"
    logger.info(f"terminal de logs conectado de {client_ip}")
    try:
        prim = await asyncio.wait_for(ws.recv(), timeout=5)
        try:
            obj0 = json.loads(prim)
            if isinstance(obj0, dict) and obj0.get("tipo") == "log_subscribe":
                req = [a for a in obj0.get("arquivos") if a in LOGS_ECO]
                if req:
                    alvo = req
        except json.JSONDecodeError:
            pass
    except asyncio.TimeoutError:
        pass
    except websockets.exceptions.ConnectionClosed:
        logger.info("cliente fechou sem se inscrever")
        return
    async def _log_zerar_tails(*nomes):
        """Posiciona offsets no fim do arquivo (snapshot já entrega o passado;
        stream só carrega o que vier daqui pra frente)."""
        async with _TAIL_LOCK:
            for nome in nomes:
                caminho = LOGS_ECO.get(nome)
                tam = caminho.stat().st_size if caminho and caminho.exists() else 0
                _TAIL_ESTADO[nome] = {"offset": tam, "pendente": ""}

    try:
        await _log_zerar_tails(*alvo)
        await ws.send(json.dumps(
            {"type": "log_snapshot", "logs": {n: _log_snapshot(n) for n in alvo}},
            ensure_ascii=False,
        ))
    except ConnectionError:
        return
    except websockets.exceptions.ConnectionClosed:
        return
    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=0.7)
                try:
                    obj = json.loads(msg)
                    if isinstance(obj, dict) and obj.get("tipo") == "log_subscribe":
                        req = [a for a in obj.get("arquivos") if a in LOGS_ECO]
                        if req:
                            alvo = req
                            await _log_zerar_tails(*alvo)
                            await ws.send(json.dumps(
                                {"type": "log_snapshot", "logs": {n: _log_snapshot(n) for n in alvo}},
                                ensure_ascii=False,
                            ))
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                pass
            novas = {}
            async with _TAIL_LOCK:
                for nome in alvo:
                    _, linhas = _ler_linhas_novas(nome)
                    if linhas:
                        novas[nome] = linhas
            if novas:
                await ws.send(json.dumps(
                    {"type": "log_lines", "linhas": novas},
                    ensure_ascii=False,
                ))
    except (ConnectionError, websockets.exceptions.ConnectionClosed):
        logger.info("terminal de logs fechado")
        return
    except Exception as e:
        logger.warning(f"terminal de logs erro: {e}")
        try:
            await ws.close()
        except Exception:
            pass


async def handle_logs(request):
    """GET /api/logs?arquivos=bridge,narrador&linhas=120 — snapshot (fallback)."""
    nomes = [a.strip() for a in request.query.get("arquivos", "").split(",") if a.strip()]
    nomes = [n for n in nomes if n in LOGS_ECO] or list(LOGS_ECO.keys())
    try:
        n = max(1, min(int(request.query.get("linhas", "120")), 500))
    except ValueError:
        n = 120
    return web.json_response({"ok": True, "logs": {nome: _log_snapshot(nome, n) for nome in nomes}})


# ============ EXECUTOR DE TAREFAS ASSÍNCRONAS ============

def _detectar_tarefa(msg):
    """Detecta se a mensagem pede uma das tarefas longas conhecidas.

    Retorna o tipo da tarefa (chave de TAREFAS_DISPONIVEIS) ou None.
    Usa regex simples por intenção; evita disparar em perguntas comuns
    ("qual é a sua coordenadora" não dispara "auditoria").
    """
    t = _sem_acentos(msg).lower()
    for tipo, cfg in TAREFAS_DISPONIVEIS.items():
        for padrao in cfg["intencoes"]:
            # Sempre prefixa palavra/incia; exigir contexto de comando verboso
            if re.search(padrao.lower(), t):
                # Evita falso positivo: "quem é o auditor" sem verbo de ação
                if _tarefa_eh_acao(padrao, msg):
                    return tipo
    return None


def _tarefa_eh_acao(_padrao_aiagnostic, msg):
    """Heurística: pedido é ação (fazer/verificar) e não simples pergunta.

    Bloqueia pedidos puramente informativos ("o que é uma auditoria?",
    "quem audita o sistema?") que não devem disparar execução longa.
    """
    t = _sem_acentos(msg).lower()
    # Pergunta interrogativa iniciada por pronome/adjetivo sem verbo de comando
    if re.search(r"^(o que|qual|quem|quando|por que|que) ", t):
        return False
    if re.search(r"\b(oi|ola|bom dia|boa tarde|boa noite)\b", t):
        return False
    return True


def _json_extrair(saida):
    """Tenta parsear JSON da saída, tolerando trailers não-JSON (ex.: 'Tempo: Xs')."""
    saida = (saida or "").strip()
    if not saida:
        return None
    tentativas = [saida]
    for ch in ("}", "]"):
        pos = saida.rfind(ch)
        if pos > 0:
            tentativas.append(saida[:pos + 1])
    for t in tentativas:
        try:
            return json.loads(t)
        except Exception:
            continue
    return None


def _resumir_auditoria(saida):
    """Extrai resumo falado da saída JSON/plano do audit_eco."""
    saida = (saida or "").strip()
    if not saida:
        return "A auditoria terminou sem detalhes na saída."
    try:
        d = _json_extrair(saida)
        if isinstance(d, dict):
            score = d.get("score")
            findings = d.get("findings") or []
            erros = [f for f in findings if f.get("severity") == "error"]
            warns = [f for f in findings if f.get("severity") == "warn"]
            base = f"A auditoria terminou."
            if score is not None:
                base = f"A auditoria terminou com pontuação {score} de cem."
            if erros:
                base += f" Encontrei {len(erros)} erro(s)."
                e0 = erros[0].get("message") or ""
                if e0:
                    base += f" Exemplo: {_truncar_fala(e0, 90)}."
            elif warns:
                base += f" Nenhum erro crítico, mas {len(warns)} aviso(s)."
            else:
                base += " Nenhum erro encontrado."
            return base
    except Exception:
        pass
    # Fallback: texto corrido
    linhas = [l for l in saida.splitlines() if l.strip() and not l.strip().startswith("{")]
    if linhas:
        primeiras = " ".join(linhas[:3])
        return f"A tarefa terminou. Resumo: {_truncar_fala(primeiras, 160)}"
    return "A tarefa terminou." if saida else "A tarefa terminou sem detalhes."


def _resumir_integridade(saida):
    """Resumo falado para integrity_guard (--check --json)."""
    saida = (saida or "").strip()
    if not saida:
        return "A verificação de integridade terminou."
    try:
        d = _json_extrair(saida)
        if isinstance(d, dict):
            n = d.get("corrompidos")
            corrigidos = d.get("corrigidos")
            if isinstance(n, int):
                if n or corrigidos:
                    return f"A verificação de integridade terminou. {n} arquivo(s) corrompido(s), {corrigidos} corrigido(s)."
                return "A verificação de integridade terminou. Todos os arquivos estão íntegros."
    except Exception:
        pass
    # Fallback por heurística de saída
    s = _sem_acentos(saida)
    if re.search(r"\d+\s*(corrompid[oa]|problemas?|erros?)", s) or "corrompid" in s:
        return "A verificação de integridade terminou e encontrou problemas."
    return "A verificação de integridade terminou. Nenhum problema encontrado."


def _resumir_preflight(saida, returncode):
    """Resumo falado para preflight_check (exit code + saída)."""
    saida = (saida or "").strip()
    if returncode == 0:
        base = "Preflight técnico concluído. Todos os testes passaram."
    else:
        base = "Preflight técnico concluído com falhas."
        # Tenta extrair a primeira linha de erro
        for l in saida.splitlines():
            if any(k in l.lower() for k in ("error", "fail", "erro")):
                if l.strip().lstrip("-").strip():
                    base += f" Exemplo: {_truncar_fala(l.strip().lstrip('-').strip(), 80)}."
                break
    return base


def _truncar_fala(texto, maxc):
    """Corta texto para fala TTS sem quebrar palavra ao meio."""
    texto = re.sub(r"\s+", " ", (texto or "").strip())
    if len(texto) <= maxc:
        return texto
    return texto[:maxc].rsplit(" ", 1)[0] + "…"


def _resumo_tarefa(task):
    """Monta o resumo falado de uma tarefa conforme o tipo."""
    if task.get("resumo"):
        return task["resumo"]
    tipo = task["tipo"]
    if tipo == "auditoria_codigo":
        return _resumir_auditoria(task.get("saida", ""))
    if tipo == "integridade_dados":
        return _resumir_integridade(task.get("saida", ""))
    if tipo == "preflight_tecnico":
        return _resumir_preflight(task.get("saida", ""), int(task.get("rc") or 0))
    return f"{task.get('nome','Tarefa')} concluída."


async def _executar_subprocess(cmd, timeout):
    """Roda subprocess assíncrono com timeout e captura stdout/stderr (b64-safe)."""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(ECOSSISTEMA_DIR),
            creationflags=flags,
        )
        try:
            saida, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode if proc.returncode is not None else 0, (saida or b"").decode("utf-8", "replace")
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            await proc.wait()
            return -1, "A tarefa demorou demais e foi interrompida (timeout)."
    except FileNotFoundError as e:
        logger.error(f"executar subprocess: cmd não encontrado: {e}")
        return -2, ""
    except Exception as e:
        logger.error(f"executar subprocess: {e}")
        return -3, ""


async def _executar_tarefa(task):
    """Executa a tarefa de verdade (subprocess), registra resultado e notifica."""
    tipo = task["tipo"]
    cfg = TAREFAS_DISPONIVEIS.get(tipo)
    if not cfg:
        logger.error(f"tarefa desconhecida: {tipo}")
        _tarefas_atualizar(task["id"], status="failed", erro="tipo desconhecido", fim=time.time())
        return
    _tarefas_atualizar(task["id"], status="running", inicio=time.time())
    logger.info(f"tarefa iniciada: {tipo} ({task['id']})")
    await _notificar_progresso("Iniciando " + cfg["nome"].lower())

    # Aviso periódico: roda um ticker em paralelo que informa o progresso a
    # cada intervalo enquanto o subprocess executa. Cancelado no finally.
    intervalo = task.get("intervalo_progresso")
    evento = asyncio.Event() if intervalo else None
    ticker = None
    if evento:
        ticker = asyncio.create_task(_notificar_periodico(task, cfg, evento))
    try:
        rc, saida = await _executar_subprocess(cfg["cmd"], cfg.get("timeout", 600))
    finally:
        if evento:
            evento.set()
        if ticker:
            ticker.cancel()
            await asyncio.gather(ticker, return_exceptions=True)
    fim = time.time()
    dur = (fim - (task.get("inicio") or fim)) if task.get("inicio") else None
    _TAREFAS_ULTIMALIDA[tipo] = saida[-3000:]  # guarda fim da saída para conferência

    # rc < 0 => falha de EXECUÇÃO (timeout, comando não encontrado, exceção).
    # rc >= 0 => o script rodou; exit code 1 comum em scripts de verificação
    # (achou problemas a reportar), então status=lógica concluída com achados.
    if rc >= 0:
        # Resumo falado montado da saída COMPLETA; a persistida é recorte de 3000 chars.
        t_resumo = dict(task)
        t_resumo["saida"] = saida
        mensagem = _resumo_tarefa(t_resumo)
        _tarefas_atualizar(task["id"], status="done", fim=fim, duracao_s=dur, saida=saida[-3000:], erro="", rc=rc, resumo=mensagem)
        logger.info(f"tarefa concluída: {tipo} ({dur:.0f}s, rc={rc}, {len(saida)}c saída)")
        await _notificar_proativo(mensagem, status="done")
    else:
        mensagem = f"{cfg['nome']} terminou com problemas na execução."
        _tarefas_atualizar(task["id"], status="failed", fim=fim, duracao_s=dur, saida=saida[-3000:], erro=str(rc), resumo=mensagem)
        logger.warning(f"tarefa falhou: {tipo} rc={rc} ({dur:.0f}s)")
        await _notificar_proativo(mensagem, status="failed")


async def _notificar_periodico(task, cfg, evento):
    """Aviso periódico de progresso enquanto a tarefa roda (a cada N segundos)."""
    intervalo = int(task.get("intervalo_progresso") or 0)
    if intervalo <= 0:
        return
    inicio = time.time()
    while True:
        try:
            await asyncio.wait_for(evento.wait(), timeout=intervalo)
            return
        except asyncio.TimeoutError:
            pass
        decorrido = int(time.time() - inicio)
        await _notificar_progresso(f"{cfg['nome']} em andamento ({_intervalo_humano(decorrido)}).")


async def _notificar_progresso(etapa):
    """Envia {progresso} para TODAS as conexões de voz ativas (não só a origem)."""
    texto = etapa
    async with _WS_VOZ_LOCK:
        alvos = list(_WS_VOZ)
    for ws in alvos:
        try:
            await ws.send(json.dumps({"progresso": texto}))
        except Exception:
            pass


async def _notificar_proativo(texto, status="done"):
    """Notificação espontânea (texto + áudio streaming) para todos os apps conectados.

    Se não houver app conectado, deixa a mensagem pendente (persistido) para
    ser enviada na próxima reconexão — nenhuma promessa se perde.
    """
    alcancados = False
    async with _WS_VOZ_LOCK:
        alvos = list(_WS_VOZ)
    for ws in alvos:
        alcancados = await _enviar_mensagem(ws, texto) or alcancados
    if not alcancados:
        try:
            d = _carregar_saudacao_estado()
            d["notificacao_pendente"] = {"text": texto, "ts": time.time(), "status": status}
            _salvar_saudacao_estado(d)
        except Exception as e:
            logger.warning(f"pendente: {e}")
    _marcar_atividade()


async def _enviar_mensagem(ws, texto):
    """Envia texto + áudio streaming para um ws (mesmo formato da resposta normal)."""
    try:
        await ws.send(json.dumps({"text": texto, "corrigido": "", "audio_streaming": True, "volume": _ler_volume_widget()}))
        _marcar_inicio_fala(texto)
        async for chunk in gerar_audio_stream(texto):
            await ws.send(json.dumps({"audio_chunk": chunk}))
        await ws.send(json.dumps({"audio_done": True}))
        return True
    except Exception as e:
        logger.warning(f"enviar mensagem: {e}")
        return False


async def _enviar_pendentes_reconexao(ws):
    """Envia notificação pendente guardada (se houver) quando o app reconecta."""
    try:
        d = _carregar_saudacao_estado()
        pend = d.get("notificacao_pendente")
        if not pend:
            return False
        texto = pend.get("text", "")
        ts = pend.get("ts", 0)
        if not texto or time.time() - float(ts) > 60 * 60:
            d.pop("notificacao_pendente", None)
            _salvar_saudacao_estado(d)
            return False
        enviado = await _enviar_mensagem(ws, texto)
        if enviado:
            d.pop("notificacao_pendente", None)
            _salvar_saudacao_estado(d)
        return enviado
    except Exception as e:
        logger.warning(f"pendentes reconexao: {e}")
        return False


async def _agendar_e_responder(ws, m):
    """Agenda a tarefa detectada e responde com a confirmação imediata.

    Retorna True se uma tarefa foi agendada (a resposta é tratada aqui).
    """
    tipo = _detectar_tarefa(m)
    if not tipo:
        return False
    if _tarefa_ativa(tipo):
        r = f"A tarefa de {TAREFAS_DISPONIVEIS[tipo]['nome'].lower()} já está em andamento. Vou informar quando terminar."
        await _enviar_mensagem(ws, r)
        return True
    task = _tarefa_nova(tipo, pedido=m)
    # Aviso periódico: vindo do próprio pedido ("a cada X") ou do padrão salvo.
    # Se o pedido pede intervalo, ele vira o novo padrão para as próximas tarefas.
    interv_msg = _detectar_intervalo_progresso(m)
    if interv_msg:
        _intervalo_salvar(interv_msg)
    interv = interv_msg or _intervalo_padrao()
    if interv:
        _tarefas_atualizar(task["id"], intervalo_progresso=interv)
    r = f"Beleza. Vou iniciar a {TAREFAS_DISPONIVEIS[tipo]['nome'].lower()} agora e te aviso aqui quando terminar."
    await _enviar_mensagem(ws, r)
    logger.info(f"tarefa agendada: {tipo}")
    # Roda em background separado para NÃO bloquear o loop de mensagens desta
    # (ou outra) conexão; a notificação de conclusão é enviada proativamente.
    asyncio.create_task(_executar_tarefa(task))
    return True


async def _registrar_ws(ws):
    async with _WS_VOZ_LOCK:
        _WS_VOZ.add(ws)


async def _remover_ws(ws):
    async with _WS_VOZ_LOCK:
        _WS_VOZ.discard(ws)


# ============ EXIBIR IMAGEM — DIAGRAMAS / MAPAS MENTAIS ============
# Spec: specs/voxumgrau-exibir-imagem.spec.md
# A bridge detecta pedidos de representação visual, gera PNG localmente
# (preferencialmente Graphviz) e envia {"tipo":"imagem","base64_png":...}.
# A geração roda em asyncio.to_thread para nunca bloquear o event loop.
_LIMITE_PNG_BYTES = 5 * 1024 * 1024  # 5 MB absoluto; spec sugere ~2 MB de alvo

_STOPWORDS_IMAGEM = {
    "a", "o", "os", "as", "de", "do", "da", "dos", "das", "e", "em", "no",
    "na", "nos", "nas", "um", "uma", "uns", "umas", "que", "para", "com",
    "por", "ao", "aos", "se", "é", "sobre", "como", "mostre", "desenhe",
}


def _dot_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _assunto_para_dot(assunto: str) -> str:
    """Monta o fonte DOT de um mapa mental (estrela) para o assunto."""
    tokens = re.findall(r"[\wÀ-ÿ]+", assunto)
    tokens = [t for t in tokens if t.lower() not in _STOPWORDS_IMAGEM and len(t) >= 3]
    tokens = tokens[:8]
    central = _dot_escape((assunto or "Tema")[:60])
    if not tokens:
        tokens = ["Conceito principal", "Aplicação", "Exemplo"]
    linhas = [
        "digraph MM {",
        '  graph [rankdir=TB];',
        '  node [shape=box, style="rounded,filled", fillcolor="#dbeafe", color="#1d4ed8", fontname="Segoe UI", fontsize=12];',
        '  edge [color="#64748b", arrowsize=0.7];',
        f'  "{central}" [fillcolor="#bfdbfe", penwidth=2];',
    ]
    for tok in tokens:
        linhas.append(f'  "{_dot_escape(tok)}" -> "{central}";')
    linhas.append("}")
    return "\n".join(linhas)


class DiagramGenerator:
    """Contrato de um gerador de diagrama (assunto -> bytes PNG)."""

    def gerar(self, assunto: str) -> bytes:
        raise NotImplementedError


class GraphvizGenerator(DiagramGenerator):
    """Gera PNG de mapa mental via Graphviz (binário `dot`)."""

    _CAMINHOS_FIXOS_DOT = (
        r"C:\Program Files\Graphviz\bin\dot.exe",
        r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
    )

    def gerar(self, assunto: str) -> bytes:
        dot = shutil.which("dot")
        if not dot:
            for caminho in self._CAMINHOS_FIXOS_DOT:
                if Path(caminho).exists():
                    dot = caminho
                    break
        if not dot:
            raise RuntimeError("Graphviz (dot) não está instalado")
        dot_src = _assunto_para_dot(assunto)
        proc = subprocess.run(
            [dot, "-Tpng"],
            input=dot_src.encode("utf-8"),
            capture_output=True,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"dot falhou: {proc.stderr.decode('utf-8', errors='ignore')[:200]}"
            )
        if not proc.stdout:
            raise RuntimeError("dot retornou PNG vazio")
        return proc.stdout


_GERADORES_DIAGRAMA = [
    GraphvizGenerator(),
]


def _gerar_diagrama_png(assunto: str):
    """Gera PNG (bytes) para um assunto usando o primeiro gerador disponível.

    Retorna None quando nenhum gerador está disponível ou todos falham
    (a resposta textual segue o fluxo normal como fallback).
    """
    for gerador in _GERADORES_DIAGRAMA:
        try:
            png = gerador.gerar(assunto)
            if png:
                return png
        except Exception as e:
            logger.warning(f"gerador {gerador.__class__.__name__}: {e}")
    return None


def _detectar_pedido_imagem(texto: str):
    """Extrai o assunto de um pedido de diagrama/mapa mental; None se não for.

    Exemplos: "mostre um mapa mental do projeto", "faça um diagrama sobre X",
    "desenha uma árvore de decisão", "represente graficamente a arquitetura".
    """
    if not texto:
        return None
    t = texto.strip().rstrip("?.,!;: ")
    m = re.search(
        r"(?i)(?:mapa mental|mind map|diagrama|fluxograma|árvore|"
        r"grafo|esquema|linha do tempo|timeline|organograma|"
        r"represente|representa|desenhe|desenha|"
        r"mostre (?:um|o|uma) (?:diagrama|grafo|mapa mental|fluxograma)|"
        r"estrutura de)\s+(?:de |do |da |dos |das |sobre |um |uma )?(.+)$",
        t,
    )
    if not m:
        return None
    assunto = re.sub(r"\s{2,}", " ", m.group(1).strip().strip(":.-"))
    if not assunto or len(assunto) < 2 or len(assunto) > 300:
        return None
    return assunto


async def _enviar_imagem_se_pedido(ws, m: str):
    """Detecta pedido de diagrama no texto; gera PNG e envia tipo=imagem.

    Se a geração falhar ou Graphviz não existir, retorna False e o fluxo
    normal de texto/áudio segue (fallback textual).
    """
    try:
        assunto = _detectar_pedido_imagem(m)
    except Exception as e:
        logger.warning(f"detectar pedido imagem: {e}")
        return False
    if assunto is None:
        return False
    try:
        png = await asyncio.to_thread(_gerar_diagrama_png, assunto)
    except Exception as e:
        logger.warning(f"gerar diagrama: {e}")
        png = None
    if png and len(png) <= _LIMITE_PNG_BYTES:
        b64 = base64.b64encode(png).decode("ascii")
        await ws.send(json.dumps({
            "tipo": "imagem",
            "base64_png": b64,
            "legenda": assunto,
        }))
        logger.info(
            f"imagem enviada: {len(png)} bytes png / {len(b64)}c base64 "
            f"(assunto={assunto[:60]})"
        )
        return True
    logger.info(
        f"imagem: fallback textual ({len(png or b'')} bytes) assunto={assunto[:60]}"
    )
    return False


async def lidar(ws):
    try:
        path = getattr(ws.request, "path", "/")
        if path == "/logs":
            await lidar_logs(ws)
            return
    except Exception:
        pass
    c = Cliente()
    client_ip = ws.remote_address[0] if ws.remote_address else "desconhecido"
    logger.info(f"conectado de {client_ip} hist={len(c._hist)//2}")
    try:
        estado = {"ultima_conexao": time.strftime("%Y-%m-%d %H:%M:%S"), "ip": client_ip}
        TMP_ESTADO.write_text(json.dumps(estado, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"estado write: {e}")
        try:
            TMP_ESTADO.parent.mkdir(parents=True, exist_ok=True)
            TMP_ESTADO.write_text(json.dumps(estado, indent=2), encoding="utf-8")
        except Exception as e2:
            logger.error(f"estado retry: {e2}")
    status = gerar_status_natural()
    try:
        extra = briefing_espontaneo()
    except Exception as e:
        logger.warning(f"briefing: {e}")
        extra = ""
    # Health-check (universal_bridge) se identifica na primeira mensagem:
    # responde o pong e encerra SEM gerar saudacao LLM nem poluir o historico.
    # EcoDashboard se identifica por {"type": ...}: responde, pula a saudacao
    # e entra direto no modo snapshot periodico.
    eh_dashboard = False
    prim_set = False
    prim_ja_respondido = False
    try:
        prim = await asyncio.wait_for(ws.recv(), timeout=3)
        prim_set = True
        try:
            obj0 = json.loads(prim)
            if isinstance(obj0, dict):
                # Ping no prim (health-check OU heartbeat do app android):
                # responde pong j� na classificacao, sem esperar o loop de
                # mensagens. O app manda o 1o ping aos 15s — se pousar dentro
                # dos 3s do prim, nao fica preso no buffer do setup (~45s).
                if obj0.get("tipo") == "ping":
                    await ws.send(json.dumps({"tipo": "pong", "origem": "bridge", "eco": obj0}))
                    logger.info(f"ping prim respondido (origem {obj0.get('origem','?')})")
                    prim_ja_respondido = True
                    if obj0.get("origem") == "health-check":
                        logger.info("health-check atendido (sem saudacao LLM)")
                        return
                if obj0.get("type") in ("ping", "pong", "get_state", "command"):
                    eh_dashboard = True
                    if obj0.get("type") == "ping":
                        await ws.send(json.dumps({"type": "pong", "origem": "bridge", "eco": obj0}))
                    elif obj0.get("type") == "get_state":
                        payload = await asyncio.to_thread(_snapshot_estado_ecossistema)
                        await ws.send(json.dumps({"type": "state", "payload": payload}))
                    elif obj0.get("type") == "command" and obj0.get("command") in ("get_state", "state"):
                        payload = await asyncio.to_thread(_snapshot_estado_ecossistema)
                        await ws.send(json.dumps({"type": "state", "payload": payload}))
        except json.JSONDecodeError:
            pass
    except asyncio.TimeoutError:
        pass
    except websockets.exceptions.ConnectionClosed:
        logger.info("cliente fechou antes da saudacao")
        return
    if eh_dashboard:
        logger.info("dashboard conectado — modo snapshot ativo")
        # Pula saudacao/retomada e vai direto ao loop de mensagens.
        cx = {"eh_reconexao": False, "minutos_desde_atividade": 0, "hist_tamanho": 0}
        estado_saud = _carregar_saudacao_estado()
    else:
        # Classifica a conexão: primeira do dia vs reconexão de conversa ativa.
        cx = _classificar_conexao()
        estado_saud = _carregar_saudacao_estado()
    if not eh_dashboard:
        # Registra a conexão de voz para receber notificações proativas
        # (auditoria/integridade/preflight concluídos em background).
        await _registrar_ws(ws)
        # Histórico ÚNICO: o app é a VOZ do ecossistema — não mantém histórico
        # próprio. Envia a conversa canônica (conversa_unica.json) para o app
        # renderizar, sempre na conexão, antes de qualquer saudação.
        try:
            await ws.send(json.dumps({"tipo": "historico", "mensagens": _historico_payload()}, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"historico push: {e}")
        hoje = datetime.datetime.now().strftime("%Y-%m-%d")
        if estado_saud.get("hoje") != hoje:
            # Novo dia: zera o acumulado de saudações do dia.
            estado_saud = {"conexoes": 0, "hoje": hoje, "saudacoes_hoje": [], "ultima_saudacao": ""}
        estado_saud["conexoes"] = estado_saud.get("conexoes", 0) + 1
        if cx["eh_reconexao"]:
            logger.info(
                f"RECONEXAO (atividade ha {cx['minutos_desde_atividade']:.1f}min, "
                f"{cx['hist_tamanho']} pares) — saudacao de retomada"
            )
            try:
                saudacao = await c.saudar(
                    extra, status,
                    contexto={
                        "eh_reconexao": True,
                        "minutos_desde_atividade": cx["minutos_desde_atividade"],
                        "ultimas_saudacoes": estado_saud.get("saudacoes_hoje", []),
                    },
                )
            except Exception as e:
                logger.warning(f"saudar reconexao: {e}")
                saudacao = ""
            if not saudacao:
                retomadas = [
                    "De volta, senhor. A linha continua aberta.",
                    "Conexão restabelecida. Estava aqui esperando.",
                    "Voltou. Sistemas seguem quentes, é só falar.",
                    "A conexão voltou. Retomando da onde estávamos.",
                    "E a conexão voltou. Estou por aqui.",
                ]
                saudacao = random.choice(retomadas)
        else:
            try:
                saudacao = await c.saudar(
                    extra, status,
                    contexto={
                        "eh_reconexao": False,
                        "ultimas_saudacoes": estado_saud.get("saudacoes_hoje", []),
                    },
                )
            except Exception as e:
                logger.warning(f"saudar: {e}")
                saudacao = ""
            if not saudacao:
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
        if saudacao:
            logger.info(f"saudacao: {saudacao[:120]}")
            saudacao_tela = normalizar_hora_display(saudacao)
            # Registra no estado (evita repetir a mesma saudação na próxima reconexão).
            estado_saud.setdefault("saudacoes_hoje", []).append(saudacao_tela)
            estado_saud["saudacoes_hoje"] = estado_saud["saudacoes_hoje"][-10:]
            estado_saud["ultima_saudacao"] = saudacao_tela
            estado_saud["ultima_saudacao_ts"] = time.time()
            _salvar_saudacao_estado(estado_saud)
            try:
                a = await gerar_audio(saudacao_tela)
            except Exception as e:
                logger.warning(f"tts startup: {e}")
                a = ""
            if a:
                _marcar_inicio_fala(saudacao_tela)
            try:
                await ws.send(json.dumps({"audio": a, "text": saudacao_tela, "volume": _ler_volume_widget()}))
            except websockets.exceptions.ConnectionClosed:
                logger.info("cliente desconectou durante a saudacao")
                return
        else:
            logger.info("sem saudacao (conversa ativa) — aguardando próxima fala do usuário")

        # RETOMADA AUTOMÁTICA: verifica se a última mensagem do usuário ficou sem
        # resposta (conexão caiu antes do Jarvis responder) e reenvia automaticamente.
        # Isso acontece SEMPRE que a conexão é restabelecida — o usuário não precisa pedir.
        if cx.get("eh_reconexao", False):
            try:
                retomou = await _retomar_ultima_tarefa(ws, c)
                if retomou:
                    logger.info("retomada automatica concluida — aguardando proxima fala")
            except Exception as e:
                logger.warning(f"retomada automatica falhou: {e}")

        # NOTIFICAÇÃO PROATIVA PENDENTE: se uma tarefa terminou sem app conectado,
        # avisa aqui na primeira conexão — a promessa de "te informo ao terminar"
        # nunca se perde, mesmo se a ponte caiu no meio.
        try:
            if await _enviar_pendentes_reconexao(ws):
                logger.info("notificacao pendente entregue na reconexao")
        except Exception as e:
            logger.warning(f"notificacao pendente: {e}")

    # CONTINUIDADE ESPONTÂNEA: a cada ~12h (ou troca de dia) durante conversa ativa,
    # envia uma frase curta de "ainda por aqui" — variada, anti-repetição, sem encher linguiça.
    async def _continuidade_periodica():
        INTERVALO_CHECAGEM = 1800   # 30 min
        JANELA_CONTINUIDADE = 43200 # 12 h
        continuidades = [
            "Ainda por aqui, senhor.",
            "Linha aberta. Seguimos.",
            "Por aqui tudo certo. E aí?",
            "Sistemas quentes. O que vem?",
            "Na escuta. Continua quando quiser.",
            "Presente. Sem pressa.",
            "Aqui, firme. Manda.",
        ]
        while True:
            await asyncio.sleep(INTERVALO_CHECAGEM)
            try:
                # Só dispara se houve atividade recente (últimos 30 min)
                es = _carregar_saudacao_estado()
                ts_ativ = es.get("ultima_atividade_ts")
                if not ts_ativ:
                    continue
                if time.time() - float(ts_ativ) > 1800:
                    continue  # conversa parada, não interromper
                # Checa se passou 12h desde última continuidade (ou troca de dia)
                ts_cont = es.get("ultima_continuidade_ts")
                hoje = datetime.datetime.now().strftime("%Y-%m-%d")
                if ts_cont:
                    if (time.time() - float(ts_cont)) < JANELA_CONTINUIDADE and es.get("ultima_continuidade_dia") == hoje:
                        continue
                # Escolhe uma frase que não foi usada recentemente
                usadas = es.get("continuidades_hoje", []) or []
                candidatas = [f for f in continuidades if f not in usadas[-3:]]
                frase = random.choice(candidatas) if candidatas else random.choice(continuidades)
                # Envia via WebSocket (texto + áudio)
                try:
                    a = await gerar_audio(frase)
                    _marcar_inicio_fala(frase)
                    await ws.send(json.dumps({"audio": a, "text": frase, "continuidade": True, "volume": _ler_volume_widget()}))
                except Exception:
                    await ws.send(json.dumps({"text": frase, "continuidade": True}))
                # Atualiza estado
                es.setdefault("continuidades_hoje", []).append(frase)
                es["continuidades_hoje"] = es["continuidades_hoje"][-5:]
                es["ultima_continuidade_ts"] = time.time()
                es["ultima_continuidade_dia"] = hoje
                _salvar_saudacao_estado(es)
                logger.info(f"continuidade enviada: {frase}")
            except Exception as e:
                logger.debug(f"continuidade periodica: {e}")

    task_cont = asyncio.create_task(_continuidade_periodica())

    # EcoDashboard: empurra snapshot estruturado periodicamente para quem pediu get_state.
    _dash_lock = asyncio.Lock()

    async def _dash_state_pusher():
        while True:
            await asyncio.sleep(10)
            if not eh_dashboard:
                continue
            try:
                payload = await asyncio.to_thread(_snapshot_estado_ecossistema)
                await ws.send(json.dumps({"type": "state", "payload": payload}))
            except Exception as e:
                logger.debug(f"dash state push: {e}")

    task_dash = asyncio.create_task(_dash_state_pusher())

    # A 1ª mensagem da conexão foi consumida na classificação (prim). Re-injeta
    # no fluxo para NÃO engolir um pedido imediato (tarefa/aviso periódico).
    # Só para conexão de voz normal — dashboard/health-check já foram respondidos.
    async def _fluxo_mensagens():
        # Ping ja respondido na classificacao nao e re-injetado (evita duplo
        # pong). Demais prims (pedido imediato) continuam re-injetados.
        if prim_set and not eh_dashboard and not prim_ja_respondido:
            yield prim
        async for mm in ws:
            yield mm

    try:
        async for m in _fluxo_mensagens():
            img_atual = None
            img_mime = "image/jpeg"
            try:
                obj = json.loads(m)
                if isinstance(obj, dict):
                    # ---- Protocolo EcoDashboard (type) ----
                    if obj.get("type") in ("ping", "pong"):
                        if obj.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "origem": "bridge", "eco": obj}))
                        continue
                    if obj.get("type") == "get_state":
                        eh_dashboard = True
                        try:
                            payload = await asyncio.to_thread(_snapshot_estado_ecossistema)
                            await ws.send(json.dumps({"type": "state", "payload": payload}))
                            logger.info("dashboard: snapshot de estado enviado")
                        except Exception as e:
                            logger.warning(f"dashboard: get_state falhou: {e}")
                        continue
                    if obj.get("type") == "command":
                        cmd = obj.get("command", "")
                        if cmd in ("get_state", "state"):
                            eh_dashboard = True
                            try:
                                payload = await asyncio.to_thread(_snapshot_estado_ecossistema)
                                await ws.send(json.dumps({"type": "state", "payload": payload}))
                            except Exception as e:
                                logger.warning(f"dashboard: command get_state falhou: {e}")
                        continue
                    # ---- Protocolo legado (tipo) — app Android ----
                    if obj.get("tipo") == "ping":
                        await ws.send(json.dumps({"tipo": "pong", "origem": "bridge", "eco": obj}))
                        logger.info(f"ping-pong de {obj.get('origem','desconhecido')}")
                        continue
                    if obj.get("tipo") == "quota":
                        if NVIDIA_QUOTA_AVAILABLE:
                            monitor = get_monitor()
                            status = monitor.get_status()
                            await ws.send(json.dumps({"tipo": "quota_status", "status": status}))
                        else:
                            await ws.send(json.dumps({"tipo": "quota_status", "error": "nvidia_quota_monitor não disponível"}))
                        logger.info(f"quota status request")
                        continue
                    if obj.get("tipo") == "editar":
                        # Edit-and-resubmit (padrão ChatGPT/Claude): usuário edita
                        # a mensagem já enviada; o resto do histórico é descartado
                        # a partir dela e a resposta é regenerada do zero.
                        texto_antigo = obj.get("texto_antigo") or obj.get("antigo") or ""
                        texto_novo = obj.get("texto_novo") or obj.get("novo") or obj.get("texto") or ""
                        _ed = _aplicar_edicao(c._hist, texto_antigo)
                        if _ed is None:
                            await ws.send(json.dumps({
                                "text": "Não encontrei essa mensagem para editar.",
                                "corrigido": texto_antigo,
                                "edicao_falhou": True,
                                "volume": _ler_volume_widget(),
                            }))
                            logger.warning(f"editar nao encontrou: '{texto_antigo[:60]}'")
                            msg_id = obj.get("id") if isinstance(obj, dict) else None
                            if msg_id is not None:
                                try:
                                    await ws.send(json.dumps({"ack": int(msg_id)}))
                                except Exception:
                                    pass
                            continue
                        m = texto_novo
                        c._hist = _ed
                        try:
                            c._salvar()
                        except Exception as e:
                            logger.warning(f"editar salvar: {e}")
                        logger.info(f"editar ok: '{texto_antigo[:40]}' -> '{texto_novo[:40]}' "
                                    f"(hist={len(c._hist)//2} pares restantes)")
                    if obj.get("tipo") == "mensagem":
                        # App novo envia {"tipo":"mensagem","id":N,"texto":"..."}.
                        # Extrai o texto real e deixa o id para o ACK abaixo.
                        m = obj.get("texto") or ""
                        logger.info(f"mensagem com id={obj.get('id')} extraida ({len(m)} chars)")
                    elif obj.get("tipo") == "imagem":
                        m = obj.get("texto") or "O que você vê nesta imagem?"
                        img_atual = obj.get("imagem", "")
                        img_mime = obj.get("mime", "image/jpeg")
                        logger.info(f"imagem recebida: {len(img_atual)} chars base64")
                    # Fase 3 - ACK-based: confirma recebimento para o app remover da fila.
                    # O app enfileira mensagens com {"id": N} e so descarta apos receber {"ack": N}.
                    # Se a conexao cair antes do ACK, o app reenvia ao reconectar.
                    msg_id = obj.get("id") if isinstance(obj, dict) else None
                    if msg_id is not None:
                        try:
                            await ws.send(json.dumps({"ack": int(msg_id)}))
                            logger.info(f"ack enviado para msg {msg_id}")
                        except Exception as e:
                            logger.warning(f"ack falhou para msg {msg_id}: {e}")
            except json.JSONDecodeError:
                pass
            msg_fix = fix_punctuation(m)
            if msg_fix != m:
                logger.info(f"pontuacao corrigida: {m[:80]} -> {msg_fix[:80]}")
                m = msg_fix
            if not m.strip():
                logger.info("mensagem vazia ignorada")
                continue
            _marcar_atividade()
            logger.info(f"msg({len(m)}): {m[:120]}")
            if len(m.strip()) <= 24 and INTERRUPCAO.match(m.strip()):
                r = "Interrompido. Pode falar quando quiser."
                try:
                    a = await gerar_audio(r)
                    _marcar_inicio_fala(r)
                    await ws.send(json.dumps({"text": r, "audio": a, "corrigido": m, "volume": _ler_volume_widget()}) if a else {"text": r, "corrigido": m})
                except:
                    await ws.send(json.dumps({"text": r, "corrigido": m}))
                continue
            # IMAGEM: pedido de diagrama/mapa mental gera PNG (Graphviz) e
            # envia fora do fluxo textual; a resposta em texto/áudio segue
            # normal (fallback textual quando a geração não estiver disponível).
            await _enviar_imagem_se_pedido(ws, m)
            # TAREFA ASSÍNCRONA: pedido de auditoria/integridade/preflight é
            # detectado antes do LLM prometer "vou te avisar" — agenda, roda o
            # script real em background e notifica ao terminar. NÃO cai no LLM.
            try:
                if await _agendar_e_responder(ws, m):
                    continue
            except Exception as e:
                logger.warning(f"agendar tarefa: {e}")
            # AVISO PERIÓDICO SOLTO ("me avise a cada minuto"): sem uma tarefa em
            # execução não há o que monitorar agora — salva o intervalo como padrão
            # para as próximas tarefas (e aplica às que já estiverem rodando).
            try:
                interv = _detectar_intervalo_progresso(m)
                if interv is not None:
                    _intervalo_salvar(interv)
                    ativas = [t for t in _tarefas_carregar() if t["status"] in ("queued", "running")]
                    for t in ativas:
                        _tarefas_atualizar(t["id"], intervalo_progresso=interv)
                    if ativas:
                        r_o = f"Combinado. Vou te informar a cada {_intervalo_humano(interv)} sobre o andamento."
                    else:
                        r_o = f"Combinado. A partir de agora informo o progresso das próximas tarefas a cada {_intervalo_humano(interv)}."
                    try:
                        a = await gerar_audio(r_o)
                        _marcar_inicio_fala(r_o)
                        await ws.send(json.dumps({"text": r_o, "audio": a, "corrigido": m, "volume": _ler_volume_widget()}) if a else {"text": r_o, "corrigido": m})
                    except Exception:
                        await ws.send(json.dumps({"text": r_o, "corrigido": m}))
                    continue
            except Exception as e:
                logger.warning(f"intervalo progresso: {e}")
            try:
                r = caminho_rapido(m)
            except Exception as e:
                logger.warning(f"caminho_rapido: {e}")
                r = None
            if r is None:
                # Dicionário de pronúncia autoevolutivo: "pronuncie X como Y"
                try:
                    pron = _processar_pedido_pronuncia(m)
                except Exception as e:
                    logger.warning(f"processar_pronuncia: {e}")
                    pron = None
                if pron:
                    palavra, fala = pron
                    if _registrar_pronuncia(palavra, fala):
                        r = f"Entendido. A partir de agora eu falo {palavra} como {fala}."
                        logger.info(f"pronuncia registrada: {palavra} -> {fala}")
                    else:
                        r = "Não consegui salvar essa pronúncia. Tente novamente."
            if r is None:
                # ---- Voz rápida: NVIDIA direta (thinking off), sem serve ----
                # Canal "simples": voz entra, resposta sai em poucos segundos.
                # Só cai no serve se a cadeia rápida falhar inteira.
                # Pedidos que exigem dado atual/online (preço, promoção, notícia,
                # cotação, clima...) NÃO passam por aqui: o modelo puro não tem
                # ferramentas e responderia "não tenho acesso a pesquisas".
                # Vão direto ao serve, que tem MCP internet/browser + websearch.
                if _requer_busca_web(m):
                    logger.info(f"busca web requerida, roteando direto ao serve: {m[:70]}")
                else:
                    try:
                        await _enviar_progresso(ws, "Respondendo rápido")
                        r = await _voz_rapida(m, cliente=c, img_base64=img_atual, img_mime=img_mime)
                        if r is not None:
                            logger.info(f"resposta voz rapida ({len(r)}c): {r[:80]}")
                    except Exception as e:
                        logger.warning(f"voz rapida geral: {e}")
                        r = None
            if r is None:
                # ---- Pipeline multi-LLM curado: opencode serve + fallback cadeia ----
                import time as _t
                _t0 = _t.time()
                try:
                    await _enviar_progresso(ws, "Entendendo sua solicitação")
                    r = await c.perguntar(m, img_base64=img_atual, img_mime=img_mime)
                    _ms = int((_t.time() - _t0) * 1000)
                    _fb_registrar("opencode-serve", ok=True, latencia_ms=_ms)
                except Exception as e:
                    _ms = int((_t.time() - _t0) * 1000)
                    _fb_registrar("opencode-serve", ok=False, latencia_ms=_ms)
                    logger.warning(f"opencode-serve falhou ({_ms}ms), tentando cadeia curada: {e}")
                    await _enviar_progresso(ws, "Reconectando ao assistente")
                    r = await _fallback_cadeia_curada(m, img_base64=img_atual, img_mime=img_mime)
                    if r is None:
                        r = f"Erro no processamento: {e}"
            else:
                logger.info(f"resposta rapida ({len(r)}c): {r[:80]}")

            r_tela = normalizar_hora_display(r)
            try:
                await _enviar_progresso(ws, "Criando sua resposta em áudio")
                await ws.send(json.dumps({"text": r_tela, "corrigido": m, "audio_streaming": True, "volume": _ler_volume_widget()}))
                logger.info(f"resp inicio: {len(r_tela)}c (streaming)")
                _marcar_inicio_fala(r_tela)
                bytes_enviados = 0
                async for chunk_b64 in gerar_audio_stream(r_tela):
                    await ws.send(json.dumps({"audio_chunk": chunk_b64}))
                    bytes_enviados += len(chunk_b64)
                await ws.send(json.dumps({"audio_done": True}))
                logger.info(f"resp stream: {len(r_tela)}c / {bytes_enviados}c de audio")
            except Exception as e:
                logger.warning(f"audio stream: {e}")
                await ws.send(json.dumps({"text": r_tela, "corrigido": m}))
    except websockets.exceptions.ConnectionClosed:
        logger.info("fim")
    finally:
        try:
            task_cont.cancel()
            await task_cont
        except Exception:
            pass
        try:
            await _remover_ws(ws)
        except Exception as e:
            logger.warning(f"remover ws: {e}")


# ============ HTTP ENDPOINTS FOR ECOW ============
# Cache simples em memória para /api/memories
_memories_cache = {'data': None, 'timestamp': 0, 'params': None}
_CACHE_TTL = 60  # segundos

def _build_memories_response(limit=200, kind_filter=None, max_days=None):
    """Constrói resposta otimizada para /api/memories"""
    from memory_engine import _load_memories
    memories = _load_memories()
    
    # Carrega mapeamento id -> filepath real
    id_to_file = {}
    map_path = Path(ECOSSISTEMA_DIR) / 'conhecimento' / 'memoria' / 'id_to_file.json'
    if map_path.exists():
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                id_to_file = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load id_to_file map: {e}")
    
    HALF_LIFE = {
        'erro': 90, 'decisao': 30, 'padrao': 60,
        'episodio': 7, 'preferencia': 365,
        'experiencia': 180, 'melhoria': 120
    }
    
    KIND_COLOR = {
        'erro': '#ff4444', 'decisao': '#4488ff', 'padrao': '#44cc44',
        'episodio': '#ffaa00', 'preferencia': '#aa44ff',
        'experiencia': '#00cccc', 'melhoria': '#ff44aa'
    }
    
    KIND_SIZE = {
        'erro': 7, 'decisao': 6.5, 'padrao': 6,
        'episodio': 5.5, 'preferencia': 5, 'experiencia': 5.5, 'melhoria': 6
    }
    
    now = datetime.datetime.now()
    nodes = []
    
    for m in memories:
        if m.get('confidence', 1.0) < 0.3:
            continue
        
        kind = m.get('kind', 'episodio')
        if kind_filter and kind not in kind_filter:
            continue
        
        half_life = HALF_LIFE.get(kind, 14)
        last_acc_str = (m.get('last_accessed') or m.get('created_at') or now.isoformat())
        try:
            last_acc = datetime.datetime.fromisoformat(last_acc_str)
        except Exception:
            last_acc = now
        
        days = (now - last_acc).total_seconds() / 86400
        if max_days and days > max_days:
            continue
        
        strength = min(m.get('strength', 1.0), 1.0)  # Cap strength at 1.0
        decay_score = max(0.01, min(1.0, strength * (0.5 ** (days / half_life))))  # Cap at 1.0
        if decay_score < 0.05:
            continue
        
        # Usa mapeamento real se disponível, senão infere
        file_path = id_to_file.get(str(m['id']), '')
        if not file_path:
            if m.get('file'):
                file_path = f"conhecimento/aprendizados/{m.get('file')}"
            elif m.get('id'):
                title_slug = m.get('task', '').lower().replace(' ', '-')[:50]
                file_path = f"conhecimento/aprendizados/{last_acc.strftime('%Y-%m-%d')}-{title_slug}.md"
        
        nodes.append({
            'id': m['id'],
            'title': m.get('task', '')[:60],
            'summary': m.get('summary', ''),
            'kind': kind,
            'tags': m.get('tags', []),
            'project': m.get('project', ''),
            'created_at': m.get('created_at'),
            'last_accessed': m.get('last_accessed'),
            'strength': strength,
            'confidence': m.get('confidence', 1.0),
            'filePath': file_path,
            'decayScore': round(decay_score, 4),
            'color': KIND_COLOR.get(kind, '#888888'),
            'size': KIND_SIZE.get(kind, 4),
            '_last_acc_days': days,
            '_decay_score': decay_score
        })
    
    # Ordena por decay score decrescente e limita
    nodes.sort(key=lambda n: -n['_decay_score'])
    nodes = nodes[:limit]
    
    # Remove campos internos
    for n in nodes:
        n.pop('_last_acc_days', None)
        n.pop('_decay_score', None)
    
    # Constrói links apenas para os nós retornados (mais eficiente)
    links = []
    tag_index = {}
    project_index = {}
    
    for i, n in enumerate(nodes):
        for tag in n.get('tags', []):
            tag_index.setdefault(tag, []).append(i)
        proj = n.get('project')
        if proj:
            project_index.setdefault(proj, []).append(i)
    
    # Links por tags
    for tag, indices in tag_index.items():
        if len(indices) > 1:
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    links.append({'source': indices[i], 'target': indices[j], 'weight': 1, 'type': 'tag', 'tag': tag})
    
    # Links por projeto
    for proj, indices in project_index.items():
        if len(indices) > 1:
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    links.append({'source': indices[i], 'target': indices[j], 'weight': 0.5, 'type': 'project', 'project': proj})
    
    return {'nodes': nodes, 'links': links}


async def handle_memories(request):
    """Endpoint /api/memories - retorna nós e links para o grafo 3D"""
    global _memories_cache
    
    try:
        # Parâmetros da query
        limit = min(int(request.query.get('limit', 200)), 500)
        kind_filter = request.query.get('kind', '').split(',') if request.query.get('kind') else None
        max_days = int(request.query.get('max_days', 0)) or None
        
        cache_key = (limit, tuple(kind_filter) if kind_filter else None, max_days)
        now_ts = time.time()
        
        # Verifica cache
        if (_memories_cache['data'] is not None and 
            _memories_cache['params'] == cache_key and
            now_ts - _memories_cache['timestamp'] < _CACHE_TTL):
            logger.info(f"/api/memories cache hit (params={cache_key})")
            return web.json_response(_memories_cache['data'])
        
        # Constrói resposta
        logger.info(f"/api/memories building (limit={limit}, kind={kind_filter}, max_days={max_days})")
        start = time.time()
        data = _build_memories_response(limit, kind_filter, max_days)
        elapsed = time.time() - start
        logger.info(f"/api/memories built in {elapsed:.2f}s: {len(data['nodes'])} nodes, {len(data['links'])} links")
        
        # Atualiza cache
        _memories_cache['data'] = data
        _memories_cache['timestamp'] = now_ts
        _memories_cache['params'] = cache_key
        
        return web.json_response(data)
    except Exception as e:
        logger.error(f"/api/memories error: {e}")
        return web.json_response({'error': str(e), 'nodes': [], 'links': []}, status=500)


async def handle_open_file(request):
    """Endpoint /open-file - abre arquivo no editor"""
    try:
        data = await request.json()
        path = data.get('path', '')
        if not path:
            return web.json_response({'error': 'path required'}, status=400)
        
        # Resolve caminho completo
        full_path = Path(ECOSSISTEMA_DIR) / path
        if not full_path.exists():
            # Tenta caminhos alternativos
            alt_paths = [
                ECOSSISTEMA_DIR / path,
                Path.cwd() / path,
                Path(path)
            ]
            for alt in alt_paths:
                if alt.exists():
                    full_path = alt
                    break
        
        # Abre no editor (code, cursor, notepad++, etc.)
        # Detecta VS Code no Windows
        code_paths = [
            os.environ.get('EDITOR'),
            r"C:\Users\David Jr\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd",
            r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
            r"C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd",
            'code',  # fallback se estiver no PATH
        ]
        code_cmd = next((p for p in code_paths if p and (os.path.exists(p) or p == 'code')), 'code')
        
        try:
            subprocess.Popen([code_cmd, str(full_path)], start_new_session=True, shell=True)
            return web.json_response({'ok': True, 'path': str(full_path), 'editor': code_cmd})
        except Exception as e:
            logger.error(f"Failed to open file with {code_cmd}: {e}")
            # Fallback: notepad
            try:
                subprocess.Popen(['notepad', str(full_path)], start_new_session=True)
                return web.json_response({'ok': True, 'path': str(full_path), 'fallback': 'notepad'})
            except Exception as e2:
                logger.error(f"Failed to open file with notepad: {e2}")
                return web.json_response({'error': str(e2)}, status=500)
    except Exception as e:
        logger.error(f"/open-file error: {e}")
        return web.json_response({'error': str(e)}, status=500)


# ============ ECOW STATE PERSISTENCE ============
async def handle_ecow_state_get(request):
    """GET /api/ecow/state - carrega estado salvo do EcoW"""
    try:
        state_path = Path(ECOSSISTEMA_DIR) / 'runtime' / 'state.json'
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            ecow_state = state.get('ecow', {})
            return web.json_response({'ok': True, 'state': ecow_state})
        return web.json_response({'ok': True, 'state': {}})
    except Exception as e:
        logger.error(f"/api/ecow/state GET error: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def handle_ecow_state_post(request):
    """POST /api/ecow/state - salva estado do EcoW"""
    try:
        data = await request.json()
        ecow_state = data.get('state', {})
        
        state_path = Path(ECOSSISTEMA_DIR) / 'runtime' / 'state.json'
        state = {}
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        
        state['ecow'] = ecow_state
        
        # Escrita atômica
        tmp_path = state_path.with_suffix('.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, state_path)
        
        return web.json_response({'ok': True})
    except Exception as e:
        logger.error(f"/api/ecow/state POST error: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def start_http_server():
    """Inicia servidor HTTP aiohttp na porta 8766"""
    # CORS middleware simples
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == 'OPTIONS':
                return web.Response(
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Max-Age': '86400'
                    }
                )
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        return middleware_handler
    
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get('/api/memories', handle_memories)
    app.router.add_post('/open-file', handle_open_file)
    app.router.add_get('/health', lambda r: web.json_response({'status': 'ok'}))
    app.router.add_get('/api/logs', handle_logs)
    
    # EcoW state persistence
    app.router.add_get('/api/ecow/state', handle_ecow_state_get)
    app.router.add_post('/api/ecow/state', handle_ecow_state_post)
    app.router.add_options('/api/ecow/state', lambda r: web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    ))
    
    app.router.add_options('/api/memories', lambda r: web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    ))
    app.router.add_options('/open-file', lambda r: web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    ))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8766)
    await site.start()
    logger.info(f"HTTP API server started on http://0.0.0.0:8766 (CORS enabled)")
    return runner


async def servir():
    logger.info("="*50)
    logger.info("  Vox UmGrau Bridge v6 (serve HTTP API + Dashboard)")
    logger.info(f"  modelo: deepseek-v4-flash-free")
    logger.info(f"  ws://0.0.0.0:8765")
    logger.info(f"  http://localhost:8766/dashboard")
    logger.info(f"  serve: {SERVE_URL}")
    logger.info(f"  sistema: {len(SISTEMA)} chars")
    logger.info(f"  estado: atualizado por request")
    logger.info(f"  voz: {TTS_VOICE}")
    logger.info(f"  historico: {HIST_PATH.name}")
    logger.info("="*50)
    # Keepalive nativo WebSocket (Fase 1 - recuperacao rapida de conexao, decisao 112):
    # - ping_interval=20: envia ping a cada 20s
    # - ping_timeout=20: se nao receber pong em 20s, fecha conexao (deteccao ~20s)
    # - close_timeout=10: tempo para handshake de fechamento
    # - max_queue=16: flow control para nao estourar memoria
    # Deteccao de conexao morta cai de ~40s para ~20s, sem codigo manual.
    async with websockets.serve(
        lidar, "0.0.0.0", 8765,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=10,
        max_size=2 * 1024 * 1024,
        max_queue=16,
    ):
        # Inicia servidor HTTP API (EcoW endpoints)
        http_runner = await start_http_server()
        
        # Warm-up automatico do LLM em background (usa _http_async/urllib,
        # mesmo cliente da cadeia principal — sem dependencia de aiohttp)
        async def warmup():
            max_tentativas = 3
            for tentativa in range(1, max_tentativas + 1):
                try:
                    logger.info(f"warm-up: tentativa {tentativa}/{max_tentativas} para aquecer modelo...")
                    if not await _ensure_serve_global():
                        logger.warning("warm-up: serve indisponivel")
                        if tentativa < max_tentativas:
                            await asyncio.sleep(5 * tentativa)  # backoff
                            continue
                        return
                    sess = await _http_async("POST", "/session", {"title": "warmup"}, timeout=30)
                    if not sess:
                        logger.warning("warm-up: falha ao criar sessao")
                        if tentativa < max_tentativas:
                            await asyncio.sleep(5 * tentativa)
                            continue
                        return
                    sid = sess.get("id")
                    if not sid:
                        logger.warning("warm-up: sessao sem id")
                        if tentativa < max_tentativas:
                            await asyncio.sleep(5 * tentativa)
                            continue
                        return
                    body = {"parts": [{"type": "text", "text": "Ola, apenas confirme que esta online em uma linha."}]}
                    result = await _http_async("POST", f"/session/{sid}/message", body, timeout=120)
                    if result:
                        logger.info("warm-up: modelo aquecido com sucesso")
                        return
                    else:
                        logger.warning("warm-up: resposta inesperada do serve")
                        if tentativa < max_tentativas:
                            await asyncio.sleep(5 * tentativa)
                            continue
                except asyncio.CancelledError:
                    return
                except Exception as e:
                    logger.warning(f"warm-up: erro na tentativa {tentativa}: {e}")
                    if tentativa < max_tentativas:
                        await asyncio.sleep(5 * tentativa)
            logger.warning("warm-up: todas as tentativas falharam (modelo pode estar frio)")

        asyncio.create_task(warmup())
        try:
            await asyncio.Future()
        finally:
            if http_runner:
                await http_runner.cleanup()

if __name__ == "__main__":
    asyncio.run(servir())
