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

HAB_ROOT = Path(__file__).resolve().parent.parent / "Habilidades"
for _hp in [HAB_ROOT / "tecnicas" / "clima-api"]:
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
MODELO_VISION_PROVIDER = "nvidia"
MODELO_VISION_MODEL = "qwen/qwen-image"
WORKDIR = r"C:\Users\David Jr\Documents\Default Project"
HIST_PATH = Path(WORKDIR) / "EcoSystemUmGrau" / "conversa_unica.json"
SYS_PATH = str(Path(__file__).parent / "JARVIS_SYSTEM.md")
PRON_PATH = str(Path(__file__).parent / "pronuncias.json")  # ipa metadata apenas

MAX_HIST = 50

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
        tecnicas = list((ECOSSISTEMA_DIR / "Habilidades" / "tecnicas").iterdir())
        if tecnicas:
            linhas.append(f"\n### Habilidades tecnicas: {len(tecnicas)}")
    except: pass
    try:
        pontes = list((ECOSSISTEMA_DIR / "Habilidades" / "pontes").iterdir())
        if pontes:
            linhas.append(f"### Habilidades pontes: {len(pontes)}")
    except: pass
    try:
        comportamentais = list((ECOSSISTEMA_DIR / "Habilidades" / "comportamentais").iterdir())
        if comportamentais:
            linhas.append(f"### Habilidades comportamentais: {len(comportamentais)}")
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
    try:
        with open(PRON_PATH, "r", encoding="utf-8") as f:
            ipas = json.load(f)
    except: return texto, False
    if not ipas: return texto, False
    palavras = sorted(ipas.keys(), key=len, reverse=True)
    def sub(m):
        w = m.group(0)
        key = w.lower()
        if key in ipas:
            meta = ipas[key]
            if "fala" in meta:
                return meta["fala"]
            ipa = meta.get("ipa", "").strip("/")
            if ipa:
                return f'<phoneme alphabet="ipa" ph="/{ipa}/">{w}</phoneme>'
        return w
    texto, n = re.subn(r'\b([^\W\d_]+)\b', sub, texto)
    return texto, n > 0

def _ssml_enriquecer(t):
    """Enriquence texto puro (ja passado por melhorar_fala e aplicar_phonemes)
    com SSML para maior naturalidade no audio, SEM alterar a ortografia exibida.

    Evolucoes:
    1. <say-as> para porcentagens, numeros ordinais e datas — leitura correta
       (ex.: '85 %' -> 'oitenta e cinco por cento', '1' -> 'primeiro',
       '31/07/2026' -> data naturalmente).
    2. <break> pausas estrategicas: apos saudacoes/iniciais (respiracao) e
       entre frases (ritmo mais humano).
    3. <prosody>/<emphasis> sutil: frases perguntam com tom ascendente e
       alertas de recursos (CPU/disco cheio) ganham enfase.

    Regra: se nada for enriquecido, devolve texto puro. Qualquer falha ->
    fallback texto puro (edge-tts sempre funciona com texto corrido).
    """
    if not t:
        return "", False

    orig = t
    tem_ssml = False
    try:
        # --- datas DD/MM/AAAA -> say-as dmy (formato brasileiro) ---
        def _data(m):
            nonlocal tem_ssml
            d, mes, a = m.group(1), m.group(2), m.group(3)
            try:
                dd, mm = int(d), int(mes)
            except ValueError:
                return m.group(0)
            if not (1 <= dd <= 31 and 1 <= mm <= 12):
                return m.group(0)
            tem_ssml = True
            return "<say-as interpret-as='date' format='dmy'>%02d/%02d/%s</say-as>" % (dd, mm, a)
        t = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', _data, t)

        # --- porcentagens: 10 % -> say-as percent (apenas inteiro, sem virgula) ---
        def _pct(m):
            nonlocal tem_ssml
            base = m.group(1) or m.group(2)
            if not base:
                return m.group(0)
            if '.' in base or ',' in base:
                return m.group(0)
            tem_ssml = True
            return "<say-as interpret-as='number' format='percent'>%s</say-as>" % base
        t = re.sub(r'(\d{1,3})\s*%|\b(\d{1,3})\s*por cento', _pct, t)

        # --- numeros ordinais: 1º/2º -> say-as ordinal (ate 100) ---
        def _ord(m):
            nonlocal tem_ssml
            num = int(m.group(1))
            if num > 100:
                return m.group(0)
            tem_ssml = True
            return "<say-as interpret-as='ordinal'>%d</say-as>" % num
        t, n_ord = re.subn(r'\b(\d+)º\b', _ord, t)
        if n_ord:
            tem_ssml = True

        # --- <break> apos saudacao abertura (respiracao natural) ---
        aberturas = re.compile(
            r'^(Entao|Oi|Ola|Bom dia|Boa tarde|Boa noite|E aí|Ei|Olha|Bem|vamos|agora)',
            re.IGNORECASE,
        )
        t, n_ab = aberturas.subn(lambda m: m.group(0) + ", <break time=\"350ms\"/>", t, count=1)
        if n_ab:
            tem_ssml = True

        # --- pausa entre frases: <break> leve apos ponto/fechamento ---
        t, n_brk = re.subn(
            r'(?<=[.!?])\s+(?![\"\'])([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ])',
            r'. <break time="150ms"/> \1', t,
        )
        if n_brk:
            tem_ssml = True

        # --- pergunta: prosso ascendente suave (reforça ? que o edge ja faz) ---
        if t.rstrip().endswith('?'):
            tem_ssml = True

        # --- enfase: alertas de recursos do PC/saude ---
        if re.search(r'CPU em \d+%|disco em \d+%|memória em \d+%|bateria crítica', t, re.IGNORECASE):
            t = re.sub(r'(\d+%)', r'<emphasis level="modified">\1</emphasis>', t)
            tem_ssml = True

        if not tem_ssml:
            return orig, False
        return _escapar(t), True
    except Exception as e:
        logger.warning("ssml_enriquecer: %s; fallback texto puro" % e)
        return orig, False


def _escapar(ssml):
    """Escapa textos dentro do SSML (atributos já usam aspas simples).
    Não escapa as tags <say-as>/<break>/<prosody> já formadas."""
    if '<' not in ssml and '>' not in ssml:
        return ssml
    # protege tags existentes
    protegidas = re.split(r'(<[^>]+>)', ssml)
    out = []
    for i, p in enumerate(protegidas):
        if p.startswith('<') and p.endswith('>'):
            out.append(p)
        else:
            p = p.replace('&', '&amp;')
            p = p.replace('<', '&lt;').replace('>', '&gt;')
            p = p.replace('"', '&quot;')
            out.append(p)
    return ''.join(out)


async def gerar_audio(texto):
    t = sanitizar(texto)
    if not t: return ""
    t = melhorar_fala(t)
    # 1) camada de pronuncia (phoneme) sobre texto puro — evita regex dentro de tags
    t_phon, tem_fonema = aplicar_phonemes(t)
    # 2) camada SSML enriquece a naturalidade sobre texto ja com phoneme
    t_ssml, usou_ssml = _ssml_enriquecer(t_phon)


    async def _stream(entrada):
        c = edge_tts.Communicate(entrada, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
        a = b""
        async for chunk in c.stream():
            if chunk["type"] == "audio":
                a += chunk["data"]
        return a

    try:
        audio = await _stream(t_phon if tem_fonema else (t_ssml if usou_ssml else t))
    except Exception as e:
        logger.warning(f"ssml com fonemas falhou ({e}); fallback texto puro")
        try:
            audio = await _stream(melhorar_fala(sanitizar(texto)))
        except Exception as e2:
            logger.error(f"tts texto puro tambem falhou: {e2}")
            return ""
    return base64.b64encode(audio).decode()


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
        sufixo = f"Usuário: {msg}\nJarvis:"
        livre = MAX_PROMPT - len(SISTEMA) - len(estado) - 4 - len(sufixo)
        p = SISTEMA + "\n\n" + estado + "\n\n"
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

    async def saudar(self, briefing, status):
        """Gera saudação criativa via LLM em sessão dedicada, sem gravar no histórico."""
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
        result = await _http_async("POST", f"/session/{session_id}/message", body, timeout=25)
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
    saudacao = ""
    try:
        saudacao = await c.saudar(extra, status)
    except Exception as e:
        logger.warning(f"saudar: {e}")
    if not saudacao:
        abridores = [
            "Olá", "Opa", "E aí", "Fala", "Oi", "Bom te ver", "Salve", "Chegou, chegou"
        ]
        fechos = [
            "Como posso ajudar?", "O que vamos fazer hoje?", "Estou por aqui. O que precisa?",
            "Diga o que você precisa.", "O que posso fazer por você hoje?"
        ]
        saudacao = f"{random.choice(abridores)}! {extra}{status}{random.choice(fechos)}"
    logger.info(f"saudacao: {saudacao[:120]}")
    saudacao_tela = normalizar_hora_display(saudacao)
    try:
        a = await gerar_audio(saudacao_tela)
    except Exception as e:
        logger.warning(f"tts startup: {e}")
        a = ""
    await ws.send(json.dumps({"audio": a, "text": saudacao_tela}))

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
                    if obj.get("tipo") == "imagem":
                        m = obj.get("texto") or "O que você vê nesta imagem?"
                        img_atual = obj.get("imagem", "")
                        img_mime = obj.get("mime", "image/jpeg")
                        logger.info(f"imagem recebida: {len(img_atual)} chars base64")
            except json.JSONDecodeError:
                pass
            msg_fix = fix_punctuation(m)
            if msg_fix != m:
                logger.info(f"pontuacao corrigida: {m[:80]} -> {msg_fix[:80]}")
                m = msg_fix
            if not m.strip():
                logger.info("mensagem vazia ignorada")
                continue
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
                try:
                    r = await c.perguntar(m, img_base64=img_atual, img_mime=img_mime)
                except Exception as e:
                    r = f"Erro no processamento: {e}"
                    logger.error(f"erro: {e}", exc_info=True)
            else:
                logger.info(f"resposta rapida ({len(r)}c): {r[:80]}")

            r_tela = normalizar_hora_display(r)
            try:
                a = await gerar_audio(r_tela)
                if a:
                    await ws.send(json.dumps({"text": r_tela, "audio": a, "corrigido": m}))
                    logger.info(f"resp: {len(r_tela)}c / audio {len(a)}c")
                else:
                    await ws.send(json.dumps({"text": r_tela, "corrigido": m}))
                    logger.info(f"resp texto: {len(r_tela)}c")
            except Exception as e:
                await ws.send(json.dumps({"text": r_tela, "corrigido": m}))
                logger.warning(f"audio: {e}")
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
    async with websockets.serve(lidar, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(servir())
