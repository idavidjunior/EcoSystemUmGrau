import asyncio, websockets, edge_tts, base64, json, logging, os, re, time, xml.sax.saxutils, socket, urllib.request, urllib.error, random, datetime
from pathlib import Path
from clima_api import get_weather
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler(r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\scripts\bridge_log.txt", mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger("vox")

TTS_VOICE = "pt-BR-AntonioNeural"
TTS_PITCH = "+0Hz"
TTS_RATE = "+0%"

BIN = str(Path(os.environ["APPDATA"]) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
SERVE_URL = "http://127.0.0.1:8766"
SERVER_USER = "opencode"
SERVER_PASS = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
WORKDIR = r"C:\Users\Playtec-bancada\Desktop\Codigos"
HIST_PATH = Path(WORKDIR) / "EcoSystemUmGrau" / "conversa_unica.json"
SYS_PATH = r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\scripts\JARVIS_SYSTEM.md"
PRON_PATH = r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\scripts\pronuncias.json"  # ipa metadata apenas

MAX_HIST = 50

DIAS = ["segunda-feira","terca-feira","quarta-feira","quinta-feira","sexta-feira","sabado","domingo"]
MESES = ["janeiro","fevereiro","marco","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
INTERRUPCAO = re.compile(r'^(ok|ta bom|esta bom|chega|para|cala a boca|já chega|valeu|obrigado|entendi|deixa pra lá|depois eu pergunto)', re.IGNORECASE)

def briefing_espontaneo():
    agora = datetime.datetime.now()
    dia_semana = DIAS[agora.weekday()]
    mes = MESES[agora.month - 1]
    data = f"{agora.day} de {mes}"
    clima = get_weather()
    linhas = [f"Hoje e {dia_semana}, {data}. "]
    linhas.append(f"{clima}. ")
    if agora.weekday() < 5 and 7 <= agora.hour <= 9:
        linhas.append("Hor\u00e1rio de pico matinal, tr\u00e2nsito intenso nas principais vias. ")
    elif agora.weekday() < 5 and 17 <= agora.hour <= 19:
        linhas.append("Hor\u00e1rio de pico noturno, tr\u00e2nsito intenso para quem vai voltar pra casa. ")
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
        skills = list((ECOSSISTEMA_DIR / "skills").iterdir())
        if skills:
            linhas.append(f"\n### Skills: {len(skills)} diretorios")
    except: pass
    try:
        plugins = list((ECOSSISTEMA_DIR / "plugins").iterdir())
        if plugins:
            linhas.append(f"### Plugins: {len(plugins)}")
    except: pass
    try:
        ler_agent = LER_DIR / "agent"
        if ler_agent.exists():
            agents = [f.stem for f in ler_agent.iterdir() if f.suffix == ".py"]
            linhas.append(f"### Agentes LER: {len(agents)}")
    except: pass
    return "\n".join(linhas)

ESTADO_ATUAL = gerar_estado_atual()


def sanitizar(t):
    if not t: return ""
    for p in [r'```[\s\S]*?```', r'`[^`]+`', r'[*_~#]', r'\[([^\]]+)\]\([^)]+\)', r'[<>{}()\[\]]']:
        t = re.sub(p, '', t)
    t = t.replace('"','').replace("'",'').replace('`','')
    t = re.sub(r'^\s*[-*+]\s+', '', t, flags=re.MULTILINE)
    return re.sub(r'\s+', ' ', t).strip()[:2000]




def aplicar_phonemes(texto):
    try:
        with open(PRON_PATH, "r", encoding="utf-8") as f:
            ipas = json.load(f)
    except: return texto, False
    if not ipas: return texto, False
    palavras = sorted(ipas.keys(), key=len, reverse=True)
    def sub(m):
        w = m.group(0)
        if w.lower() in ipas:
            ipa = ipas[w.lower()]["ipa"].strip("/")
            return f'<phoneme alphabet="ipa" ph="/{ipa}/">{w}</phoneme>'
        return w
    texto = re.sub(r'\b([A-Za-zÀ-ÿ]+)\b', sub, texto)
    return texto, True

async def gerar_audio(texto):
    t = sanitizar(texto)
    if not t: return ""
    t, tem_phoneme = aplicar_phonemes(t) if PRON_PATH else (t, False)
    if tem_phoneme:
        t = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='pt-BR'>{t}</speak>"
    c = edge_tts.Communicate(t, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    audio = b""
    async for chunk in c.stream():
        if chunk["type"] == "audio": audio += chunk["data"]
    return base64.b64encode(audio).decode()


# --- HTTP client para opencode serve ---

def _http(method, path, data=None):
    url = f"{SERVE_URL}{path}"
    creds = base64.b64encode(f"{SERVER_USER}:{SERVER_PASS}".encode()).decode()
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP {e.code} {method} {path}: {e.read().decode()[:300]}")
        return None
    except Exception as e:
        logger.error(f"HTTP {method} {path}: {e}")
        return None

async def _http_async(method, path, data=None):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _http, method, path, data)


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
        estado = gerar_estado_atual()
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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            r = s.connect_ex(("127.0.0.1", 8766))
            s.close()
            if r == 0:
                return True
        except:
            s.close()
        logger.info("serve not running, starting...")
        proc = await asyncio.create_subprocess_exec(
            BIN, "serve", "--port", "8766",
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        for _ in range(15):
            await asyncio.sleep(1)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            try:
                r = s.connect_ex(("127.0.0.1", 8766))
                s.close()
                if r == 0:
                    logger.info("serve started")
                    return True
            except:
                s.close()
        logger.error("failed to start serve")
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

    async def perguntar(self, msg, tentativa=1):
        prompt = self._montar(msg)
        logger.info(f"hist={len(self._hist)//2} prompt={len(prompt)}b tentativa={tentativa}: {msg[:80]}")

        if not await self._ensure_serve():
            return "Erro: servidor OpenCode não está disponível."

        session_id = await self._get_session()
        if not session_id:
            return "Erro: não foi possível criar sessão no servidor."

        result = await _http_async("POST", f"/session/{session_id}/message", {
            "parts": [{"type": "text", "text": prompt}]
        })

        if not result:
            if tentativa < 2:
                self._session_id = None
                logger.info("result vazio, tentando nova sessao")
                return await self.perguntar(msg, tentativa=2)
            return "Sem resposta do servidor."

        parts = result.get("parts", [])
        texts = [p.get("text", "") for p in parts if p.get("type") == "text" and p.get("text", "").strip()]
        resp = texts[-1] if texts else None

        if not resp:
            if tentativa < 2:
                self._session_id = None
                logger.info(f"resp vazia parts={len(parts)}, criando nova sessao")
                return await self.perguntar(msg, tentativa=2)
            resp = "Sem resposta."

        self._hist.append(f"Usuário: {msg}")
        self._hist.append(f"Jarvis: {resp}")
        self._salvar()
        return resp


def gerar_status_natural():
    ok = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        r = s.connect_ex(("127.0.0.1", 8765))
        s.close()
        if r == 0:
            ok.append("bridge operante na porta 8765")
    except: pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        r = s.connect_ex(("127.0.0.1", 8766))
        s.close()
        if r == 0:
            ok.append("servidor OpenCode na porta 8766")
    except: pass
    try:
        if Path(BIN).exists():
            ok.append("OpenCode pronto")
    except: pass
    if ok:
        return "O sistema está funcionando: " + " e ".join(ok) + ". "
    return "O sistema está inicializando. "

def fix_punctuation(text):
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:] if text[0].islower() else text
    palavras_q = r"^(qual|quem|onde|quando|como|por que|porque|pq|q|oq|o que|quanto|quantos|quantas|qto|qtos|qtas|pra que|para que|sera que|vai|tem|existe|dá para|da pra|posso|pode|poderia|queria saber|me diga|me fale|explique|conte|preciso saber|sabe me dizer|como que|que que|quem que|onde que)"
    e_questao = bool(re.match(palavras_q, text.lower().lstrip()))
    if e_questao and not text.rstrip().endswith(("?", ".")):
        return text.rstrip() + "?"
    elif not text.rstrip().endswith((".", "?", "!", ":")):
        return text.rstrip() + "."
    return text

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
    saudacao = f"Ola. {extra}{status}Como posso ajudar?"
    try:
        a = await gerar_audio(saudacao)
    except Exception as e:
        logger.warning(f"tts startup: {e}")
        a = ""
    await ws.send(json.dumps({"audio": a, "text": saudacao}))

    try:
        async for m in ws:
            msg_fix = fix_punctuation(m)
            if msg_fix != m:
                logger.info(f"pontuacao corrigida: {m[:80]} -> {msg_fix[:80]}")
                m = msg_fix
            logger.info(f"msg({len(m)}): {m[:120]}")
            if INTERRUPCAO.match(m.strip()):
                r = "Interrompido. Pode falar quando quiser."
                try:
                    a = await gerar_audio(r)
                    await ws.send(json.dumps({"text": r, "audio": a}) if a else {"text": r})
                except:
                    await ws.send(json.dumps({"text": r}))
                continue
            try:
                r = await c.perguntar(m)
            except Exception as e:
                r = f"Erro no processamento: {e}"
                logger.error(f"erro: {e}", exc_info=True)

            try:
                a = await gerar_audio(r)
                if a:
                    await ws.send(json.dumps({"text": r, "audio": a}))
                    logger.info(f"resp: {len(r)}c / audio {len(a)}c")
                else:
                    await ws.send(json.dumps({"text": r}))
                    logger.info(f"resp texto: {len(r)}c")
            except Exception as e:
                await ws.send(json.dumps({"text": r}))
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
