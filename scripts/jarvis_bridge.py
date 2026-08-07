import asyncio, websockets, edge_tts, base64, json, logging, os, re, time, xml.sax.saxutils, socket, urllib.request, urllib.error, random, datetime, subprocess, sys, unicodedata
from pathlib import Path

# NVIDIA Quota Monitor
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from nvidia_quota_monitor import get_monitor, nvidia_request_with_quota
    NVIDIA_QUOTA_AVAILABLE = True
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

logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler(Path(__file__).parent / "bridge_log.txt", mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger("vox")

TTS_VOICE = "pt-BR-AntonioNeural"
TTS_PITCH = "+0Hz"
TTS_RATE = "+0%"

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
# Janela de conversa ativa: se a última fala no histórico foi há menos de
# JANELA_CONVERSA_MIN minutos, NÃO repetir saudação inicial — a conversa
# continua fluindo (evita o "recomeço" a cada reconexão dentro da mesma sessão).
JANELA_CONVERSA_MIN = 30

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


def sanitizar(t):
    if not t: return ""
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
    t = sanitizar(texto)
    if not t: return ""
    t = melhorar_fala(t)
    # edge-tts >= 7.x escapa todo texto e não suporta SSML custom: enviamos
    # TEXTO PURO. Pronúncias por grafia falada ("fala") são texto e funcionam;
    # tags <phoneme>/<break>/<say-as> seriam lidas literalmente, então não existem.

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
    """Async generator que yield chunks base64 de audio conforme o edge-tts
    gera. Clients podem tocar audio progressivamente sem esperar geracao completa.

    Protocolo streaming:
        1. Bridge envia {text, corrigido, audio_streaming: True}  (texto imediato)
        2. Bridge envia {audio_chunk: <b64>} para cada chunk (play imediato)
        3. Bridge envia {audio_done: True}  (finaliza playback)
    """
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

def _http(method, path, data=None, timeout=120):
    url = f"{SERVE_URL}{path}"
    creds = base64.b64encode(f"{SERVER_USER}:{SERVER_PASS}".encode()).decode()
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP {e.code} {method} {path}: {e.read().decode()[:300]}")
        return None
    except Exception as e:
        logger.error(f"HTTP {method} {path}: {e}")
        return None

async def _http_async(method, path, data=None, timeout=120):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _http, method, path, data, timeout)


async def _ensure_serve_global():
    """Versão no nível do módulo de Cliente._ensure_serve: garante um
    `opencode serve` saudável na porta configurada (com failover para a reserva)."""
    for porta in (PORTA_SERVE, PORTA_SERVE_RESERVA):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            r = s.connect_ex(("127.0.0.1", porta))
            s.close()
            if r == 0:
                return True
        except Exception:
            pass
        proc = await asyncio.create_subprocess_exec(
            BIN, "serve", "--port", str(porta),
            cwd=WORKDIR,
            env={**os.environ},
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        for _ in range(15):
            await asyncio.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                r = s.connect_ex(("127.0.0.1", porta))
                s.close()
                if r == 0:
                    return True
            except Exception:
                pass
    return False


MAX_PROMPT = 28000

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
                env={**os.environ},
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            for _ in range(15):
                await asyncio.sleep(1)
                if await self._serve_ok(porta):
                    logger.info(f"serve started on {porta}")
                    return True
            logger.error(f"failed to start serve on {porta}")
        return False

    async def _serve_ok(self, porta):
        """True se a porta responde (servidor de pé)."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            r = s.connect_ex(("127.0.0.1", porta))
            s.close()
            return r == 0
        except Exception:
            try:
                s.close()
            except Exception:
                pass
            return False

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
        if self._session_id:
            return self._session_id
        sessions = await _http_async("GET", "/session")
        if sessions and len(sessions) > 0:
            sid = sessions[-1].get("id")
            if sid:
                self._session_id = sid
                logger.info(f"reusing session {sid}")
                return sid
        result = await _http_async("POST", "/session", {"title": "Jarvis"})
        if result:
            self._session_id = result.get("id")
            logger.info(f"created session {self._session_id}")
        return self._session_id

    async def perguntar(self, msg, img_base64=None, img_mime="image/jpeg", tentativa=1):
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
        result = await _http_async("POST", f"/session/{session_id}/message", body)

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
            instrucao = (
                "Você é o Jarvis, assistente de voz do EcoSystemUmGrau, do usuário David. "
                "A conexão de voz VOLTOU AGORA, no meio de uma conversa já existente — "
                "NÃO é a primeira vez que fala com o David hoje. "
                "NÃO se apresente, NÃO recite briefing, NÃO diga 'data e hora', "
                "NÃO pergunte 'o que precisa' como se fosse um encontro novo. "
                "Faça uma saudação CURTA (1 frase, no máximo 2) de quem está retomando "
                "uma conversa, como um assistente que já estava trabalhando e reconhece "
                "a volta do usuário. Pode ser leve, seca, bem-humorada ou direta — variando. "
                f"Saudações que você JÁ USOU e NÃO deve repetir: {ultimas_txt}. "
                "Escolha um tom diferente dos já usados. "
                "Nada de emojis, markdown, listas ou aspas. "
                "Responda apenas com a saudação de retomada."
            )
        else:
            instrucao = (
                "Você é o Jarvis, assistente de voz do EcoSystemUmGrau, do usuário David. "
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
            previsao = get_forecast_data(days=2)
            if "erro" not in previsao and len(previsao["previsoes"]) >= 2:
                d = previsao["previsoes"][1]
                txt = f"Amanhã: mínima de {d['tmin']:.0f} e máxima de {d['tmax']:.0f} graus"
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


def _carregar_saudacao_estado():
    """Carrega o estado persistente de saudações (reconexões, últimas saudações)."""
    try:
        if SAUDACAO_ESTADO.exists():
            d = json.loads(SAUDACAO_ESTADO.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
    except Exception as e:
        logger.warning(f"saudacao_estado load: {e}")
    return {"conexoes": 0, "hoje": "", "saudacoes_hoje": [], "ultima_saudacao": ""}


def _salvar_saudacao_estado(d):
    try:
        SAUDACAO_ESTADO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"saudacao_estado save: {e}")


def _classificar_conexao():
    """Classifica a conexão como PRIMEIRA (sem atividade recente) ou RECONEXÃO
    (atividade recente). Fontes de verdade, em ordem:
      1. Estado de saudações: se já saudou hoje, a próxima conexão é reconexão
         (a menos que a última saudação seja de muito tempo atrás).
      2. Ponte: timestamp de atividade persistido (atualizado a cada mensagem).
      3. Histórico: mtime do conversa_unica.json."""
    agora = time.time()
    # 1) Estado de saudações — a fonte mais confiável para "já conversamos hoje".
    try:
        es = _carregar_saudacao_estado()
        if es.get("hoje") == datetime.datetime.now().strftime("%Y-%m-%d") and es.get("saudacoes_hoje"):
            ts_ultima_saud = es.get("ultima_saudacao_ts")
            if ts_ultima_saud and (agora - float(ts_ultima_saud)) / 3600.0 < 6:
                return {
                    "eh_reconexao": True,
                    "minutos_desde_atividade": (agora - float(ts_ultima_saud)) / 60.0,
                    "hist_tamanho": 0,
                }
    except Exception as e:
        logger.warning(f"_classificar_conexao estado_saud: {e}")
    # 2) Atividade persistida pela ponte
    try:
        if TMP_ESTADO.exists():
            d = json.loads(TMP_ESTADO.read_text(encoding="utf-8"))
            ts = d.get("ultima_atividade")
            if ts and (agora - float(ts)) / 60.0 < JANELA_CONVERSA_MIN:
                return {
                    "eh_reconexao": True,
                    "minutos_desde_atividade": (agora - float(ts)) / 60.0,
                    "hist_tamanho": 0,
                }
    except Exception:
        pass
    # 3) mtime do histórico
    minutos_ultima = _ultima_atividade_minutos()
    hist_tamanho = 0
    try:
        if HIST_PATH.exists():
            d = json.loads(HIST_PATH.read_text(encoding="utf-8-sig"))
            if isinstance(d, list):
                hist_tamanho = len(d) // 2
    except Exception:
        pass
    eh_reconexao = (
        minutos_ultima is not None
        and minutos_ultima < JANELA_CONVERSA_MIN
        and hist_tamanho > 0
    )
    return {
        "eh_reconexao": eh_reconexao,
        "minutos_desde_atividade": minutos_ultima,
        "hist_tamanho": hist_tamanho,
    }


async def lidar(ws):
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
    # Classifica a conexão: primeira do dia vs reconexão de conversa ativa.
    cx = _classificar_conexao()
    estado_saud = _carregar_saudacao_estado()
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
                "Aí de novo, senhor. Onde paramos?",
                "Voltou. Sistemas seguem quentes, é só falar.",
                "Reconectado. Continue de onde estava.",
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
        await ws.send(json.dumps({"audio": a, "text": saudacao_tela}))
    else:
        logger.info("sem saudacao (conversa ativa) — aguardando próxima fala do usuário")

    try:
        async for m in ws:
            img_atual = None
            img_mime = "image/jpeg"
            try:
                obj = json.loads(m)
                if isinstance(obj, dict):
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
                    await ws.send(json.dumps({"text": r, "audio": a, "corrigido": m}) if a else {"text": r, "corrigido": m})
                except:
                    await ws.send(json.dumps({"text": r, "corrigido": m}))
                continue
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
                # ---- Pipeline multi-LLM curado: opencode serve + fallback cadeia ----
                import time as _t
                _t0 = _t.time()
                try:
                    r = await c.perguntar(m, img_base64=img_atual, img_mime=img_mime)
                    _ms = int((_t.time() - _t0) * 1000)
                    _fb_registrar("opencode-serve", ok=True, latencia_ms=_ms)
                except Exception as e:
                    _ms = int((_t.time() - _t0) * 1000)
                    _fb_registrar("opencode-serve", ok=False, latencia_ms=_ms)
                    logger.warning(f"opencode-serve falhou ({_ms}ms), tentando cadeia curada: {e}")
                    r = await _fallback_cadeia_curada(m, img_base64=img_atual, img_mime=img_mime)
                    if r is None:
                        r = f"Erro no processamento: {e}"
            else:
                logger.info(f"resposta rapida ({len(r)}c): {r[:80]}")

            r_tela = normalizar_hora_display(r)
            try:
                await ws.send(json.dumps({"text": r_tela, "corrigido": m, "audio_streaming": True}))
                logger.info(f"resp inicio: {len(r_tela)}c (streaming)")
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


async def servir():
    logger.info("="*50)
    logger.info("  Vox UmGrau Bridge v6 (serve HTTP API)")
    logger.info(f"  modelo: deepseek-v4-flash-free")
    logger.info(f"  ws://0.0.0.0:8765")
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
        # Warm-up automatico do LLM em background (usa _http_async/urllib,
        # mesmo cliente da cadeia principal — sem dependencia de aiohttp)
        async def warmup():
            try:
                logger.info("warm-up: iniciando requisicao para aquecer modelo...")
                if not await _ensure_serve_global():
                    logger.warning("warm-up: serve indisponivel")
                    return
                sess = await _http_async("POST", "/session", {"title": "warmup"}, timeout=20)
                if not sess:
                    logger.warning("warm-up: falha ao criar sessao")
                    return
                sid = sess.get("id")
                if not sid:
                    logger.warning("warm-up: sessao sem id")
                    return
                body = {"parts": [{"type": "text", "text": "Ola, apenas confirme que esta online em uma linha."}]}
                result = await _http_async("POST", f"/session/{sid}/message", body, timeout=90)
                if result:
                    logger.info("warm-up: modelo aquecido com sucesso")
                else:
                    logger.warning("warm-up: resposta inesperada do serve")
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"warm-up: erro (modelo pode estar frio): {e}")

        asyncio.create_task(warmup())
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(servir())
