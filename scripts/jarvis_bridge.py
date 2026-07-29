import asyncio, websockets, edge_tts, base64, json, logging, os, subprocess, re, time, xml.sax.saxutils, socket
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler(r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\scripts\bridge_log.txt", mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger("vox")

TTS_VOICE = "pt-BR-ThalitaMultilingualNeural"
TTS_PITCH = "-30Hz"
TTS_RATE = "+0%"

BIN = str(Path(os.environ["APPDATA"]) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
WORKDIR = r"C:\Users\Playtec-bancada\Desktop\Codigos"
HIST_PATH = Path(WORKDIR) / "EcoSystemUmGrau" / "conversa_unica.json"
SYS_PATH = r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\scripts\JARVIS_SYSTEM.md"
PRON_PATH = r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\scripts\pronuncias.json"

MAX_HIST = 50
MAX_TOOL = 500
MAX_STDOUT = 5_000_000

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

def carregar_pronuncias():
    try:
        with open(PRON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

PRONUNCIAS = carregar_pronuncias()

def gerar_estado_atual():
    """Gera um resumo dinâmico do estado atual do ecossistema."""
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

def corrigir_pronuncia(texto):
    """Substitui palavras por suas versoes foneticas para melhor TTS."""
    if not texto or not PRONUNCIAS: return texto
    palavras = sorted(PRONUNCIAS.keys(), key=len, reverse=True)
    for palavra in palavras:
        alias = PRONUNCIAS[palavra]
        texto = re.sub(re.escape(palavra), lambda m: alias, texto, flags=re.IGNORECASE)
    return texto.strip()


async def gerar_audio(texto):
    t = sanitizar(texto)
    if not t: return ""
    t = corrigir_pronuncia(t)
    c = edge_tts.Communicate(t, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    audio = b""
    async for chunk in c.stream():
        if chunk["type"] == "audio": audio += chunk["data"]
    return base64.b64encode(audio).decode()


def extrair_resposta(stdout: str) -> tuple[str | None, list]:
    texts = []
    tools = []
    tipos = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line: continue
        try:
            obj = json.loads(line)
            t = obj.get("type", "")
            tipos[t] = tipos.get(t, 0) + 1
            if t == "text":
                part = obj.get("part")
                txt = part.get("text", "") if isinstance(part, dict) else (part if isinstance(part, str) else "")
                if isinstance(txt, str) and txt.strip():
                    texts.append(txt.strip())
            elif t in ("tool_use",):
                part = obj.get("part")
                if isinstance(part, dict):
                    st = part.get("state")
                    if isinstance(st, dict) and st.get("status") == "completed":
                        out = st.get("output")
                        if isinstance(out, str) and out.strip():
                            tools.append(out.strip())
        except json.JSONDecodeError:
            pass
    logger.info(f"eventos={tipos} texts={len(texts)} tools={len(tools)}")
    if texts: return texts[-1], tools
    if tools: return tools[-1][:MAX_TOOL], tools
    return None, tools


MAX_RETRY = 2
MAX_PROMPT = 28000

async def executar(prompt: str, timeout=300, retry=True) -> str | None:
    args = [BIN, "run", "--format", "json", "--auto", "--dir", WORKDIR, prompt]
    logger.info(f"run: {len(prompt)}b prompt...")
    t0 = time.time()
    try:
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        so, se = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        try: proc.kill()
        except: pass
        logger.error("timeout")
        return None
    except Exception as e:
        logger.error(f"exec: {e}", exc_info=True)
        return None
    so_text = so.decode(errors="replace")[:MAX_STDOUT]
    se_text = se.decode(errors="replace")
    logger.info(f"RC={proc.returncode} out={len(so_text)}b t={time.time()-t0:.0f}s")
    for line in se_text.splitlines():
        if line.strip(): logger.info(f"[oc:err] {line.strip()}")
    resp, tools = extrair_resposta(so_text)
    if resp: return resp
    logger.warning(f"vazio, tools={len(tools)}")
    if tools and retry:
        ctx = "\n".join(f"Resultado: {t[:300]}" for t in tools[-3:])
        prompt2 = f"{ctx}\nResponda em portugues: o que foi encontrado?"
        logger.info("retry com tools...")
        return await executar(prompt2, timeout=120, retry=False)
    return None


class Cliente:
    def __init__(self):
        self._hist = self._carregar()
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

    async def perguntar(self, msg):
        prompt = self._montar(msg)
        logger.info(f"hist={len(self._hist)//2} prompt={len(prompt)}b: {msg[:80]}")
        if len(prompt) > 30000:
            logger.error(f"prompt enorme ({len(prompt)}b), forcando limpeza")
            hist = self._hist[:2]
            self._hist = hist
            prompt = self._montar(msg)
        resp = await executar(prompt)
        if not resp:
            resp = "Sem resposta. (opencode nao retornou resultado)"
        self._hist.append(f"Usuário: {msg}")
        self._hist.append(f"Jarvis: {resp}")
        self._salvar()
        return resp


def gerar_status_natural():
    """Gera uma frase em linguagem natural com o estado do sistema."""
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
            ok.append("servidor web na porta 8766")
    except: pass
    try:
        if Path(BIN).exists():
            ok.append("OpenCode pronto")
    except: pass
    if ok:
        return "O sistema está funcionando: " + " e ".join(ok) + ". "
    return "O sistema está inicializando. "

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
    saudacao = f"Olá, sou o Jarvis do Ecossistema Um Grau. {status}Estou ouvindo."
    try:
        a = await gerar_audio(saudacao)
    except Exception as e:
        logger.warning(f"tts startup: {e}")
        a = ""
    await ws.send(json.dumps({"audio": a, "text": saudacao}))

    try:
        async for m in ws:
            logger.info(f"msg({len(m)}): {m[:120]}")
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
    logger.info("  Vox UmGrau Bridge v4 (expert)")
    logger.info(f"  modelo: deepseek-v4-flash-free")
    logger.info(f"  ws://0.0.0.0:8765")
    logger.info(f"  sistema: {len(SISTEMA)} chars")
    logger.info(f"  estado: atualizado por request")
    logger.info(f"  pronuncias: {len(PRONUNCIAS)} palavras")
    logger.info(f"  historico: {HIST_PATH.name}")
    logger.info("="*50)
    async with websockets.serve(lidar, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(servir())
