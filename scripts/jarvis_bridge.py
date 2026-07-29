import asyncio, websockets, edge_tts, base64, json, logging, os, subprocess, re, time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler(r"C:\Users\Playtec-bancada\Desktop\Codigos\bridge_log.txt", mode="a")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger("vox")

TTS_VOICE = "pt-BR-ThalitaMultilingualNeural"
TTS_PITCH = "-30Hz"
TTS_RATE = "+0%"

OPENCODE_BIN = str(Path(os.environ.get("APPDATA", "")) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
WORKDIR = r"C:\Users\Playtec-bancada\Desktop\Codigos"
HISTORICO_PATH = r"C:\Users\Playtec-bancada\Desktop\Codigos\bridge_historico.json"

SERVER_URL = "http://127.0.0.1:8766"
SERVER_USER = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
SERVER_PASS = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
MAX_HIST = 8
MAX_TOOL_OUTPUT = 500

WRK = WORKDIR

models = [
    "opencode/deepseek-v4-flash-free",
    "opencode/deepseek-v4-flash-free",
]

def sanitizar(texto):
    if not texto: return ""
    for p in [r'```[\s\S]*?```', r'`[^`]+`', r'[*_~#]', r'\[([^\]]+)\]\([^)]+\)', r'[<>{}()\[\]]']:
        texto = re.sub(p, '', texto)
    texto = texto.replace('"','').replace("'",'').replace('`','')
    texto = re.sub(r'^\s*[-*+]\s+', '', texto, flags=re.MULTILINE)
    return re.sub(r'\s+', ' ', texto).strip()[:2000]

async def tts(texto):
    texto = sanitizar(texto)
    if not texto: return ""
    com = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    audio = b""
    async for chunk in com.stream():
        if chunk["type"] == "audio": audio += chunk["data"]
    return base64.b64encode(audio).decode()

def extrair_resposta(stdout: str) -> tuple[str | None, list]:
    text_events = []
    tool_outputs = []
    tipos = {}
    erros = 0
    ultimo_step_finish = None

    for line in stdout.splitlines():
        line = line.strip()
        if not line: continue
        try:
            obj = json.loads(line)
            t = obj.get("type", "?")
            tipos[t] = tipos.get(t, 0) + 1

            if t == "text":
                part = obj.get("part")
                if isinstance(part, dict):
                    txt = part.get("text", "")
                elif isinstance(part, str):
                    txt = part
                else:
                    continue
                if isinstance(txt, str) and txt.strip():
                    text_events.append(txt.strip())

            if t in ("tool_use", "tool_result"):
                part = obj.get("part")
                if isinstance(part, dict):
                    state = part.get("state")
                    if isinstance(state, dict) and state.get("status") == "completed":
                        out = state.get("output")
                        if isinstance(out, str) and out.strip():
                            tool_outputs.append(out.strip())

            if t == "step_finish":
                reason = obj.get("part", {}).get("reason") if isinstance(obj.get("part"), dict) else None
                if reason == "stop":
                    ultimo_step_finish = "stop"

        except json.JSONDecodeError:
            erros += 1

    logger.info(f"tipos={tipos} text_events={len(text_events)} tool_outputs={len(tool_outputs)} step_finish_stop={ultimo_step_finish=='stop'}")

    if text_events:
        return text_events[-1], tool_outputs

    if tool_outputs:
        return tool_outputs[-1][:MAX_TOOL_OUTPUT], tool_outputs

    return None, tool_outputs


async def _run_cmd(cmd: list, prompt: str, timeout=180) -> tuple[str | None, list]:
    full = list(cmd) + [prompt]
    cmd_str = subprocess.list2cmdline(full)
    logger.info(f"OC: {cmd[0]} ... {prompt[:60]}")
    t0 = time.time()
    proc = await asyncio.create_subprocess_shell(cmd_str, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        so, se = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        logger.error("timeout")
        return None, []
    so_text = so.decode(errors="replace")
    se_text = se.decode(errors="replace")
    logger.info(f"RC={proc.returncode} out={len(so_text)}b t={time.time()-t0:.0f}s")
    for line in se_text.splitlines():
        if line.strip(): logger.info(f"[oc:err] {line.strip()}")
    return extrair_resposta(so_text)


async def consultar_modelo(prompt: str, timeout=180) -> tuple[str | None, list]:
    for modelo in models:
        cmd = [
            OPENCODE_BIN, "run",
            "--attach", SERVER_URL,
            "--format", "json",
            "--auto",
            "--username", SERVER_USER,
            "--password", SERVER_PASS,
            "--dir", WRK,
        ]
        resp, tools = await _run_cmd(cmd, prompt, timeout)
        if resp:
            return resp, tools
        logger.warning(f"modelo {modelo} retornou vazio, tentando proximo...")
    return None, []


class OpenCodeClient:
    def __init__(self):
        self._historico = self._carregar()

    def _carregar(self) -> list:
        try:
            with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data[-MAX_HIST:] if isinstance(data, list) else []
        except: return []

    def _salvar(self):
        try:
            with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
                json.dump(self._historico[-MAX_HIST:], f, ensure_ascii=False, indent=2)
        except Exception as e: logger.error(f"salvar: {e}")

    def _montar_prompt(self, msg: str) -> str:
        p = ""
        if self._historico:
            for i in range(0, len(self._historico), 2):
                p += f"{self._historico[i]}\n{self._historico[i+1]}\n"
        p += f"Usuário: {msg}\nJarvis:"
        return p

    async def consultar(self, mensagem: str) -> str:
        prompt = self._montar_prompt(mensagem)
        qtd = len(self._historico)//2
        logger.info(f"hist={qtd}: {mensagem[:60]}")

        resposta, tools = await consultar_modelo(prompt)

        if not resposta:
            logger.warning("vazio, retry com ferramentas")
            ctx = ""
            for t in tools[-3:]:
                ctx += f"Resultado: {t[:300]}\n"
            prompt2 = f"{ctx}Com base nos resultados acima, responda em português: {mensagem}\nJarvis:"
            resposta, _ = await consultar_modelo(prompt2)

        if not resposta:
            resposta = "Sem resposta."

        if len(resposta) > 60:
            self._historico.append(f"Usuário: {mensagem}")
            self._historico.append(f"Jarvis: {resposta[:300]}")
            self._salvar()
        return resposta


async def handler(ws):
    oc = OpenCodeClient()
    logger.info(f"Conexao hist={len(oc._historico)//2}")

    try:
        audio_s = await tts("Olá, sou o Jarvis do EcoSystemUmGrau. Estou ouvindo.")
    except: audio_s = ""
    await ws.send(json.dumps({"audio": audio_s, "text": "Olá, sou o Jarvis do EcoSystemUmGrau. Estou ouvindo."}))

    try:
        async for msg in ws:
            logger.info(f"msg: {msg[:80]}")
            resposta = ""
            try:
                resposta = await oc.consultar(msg)
            except Exception as e:
                resposta = f"Erro: {e}"
                logger.error(f"handler: {e}", exc_info=True)

            await ws.send(json.dumps({"text": resposta}))
            logger.info(f"texto enviado ({len(resposta)} chars)")

            try:
                logger.info("gerando audio...")
                audio = await tts(resposta)
                if audio:
                    await ws.send(json.dumps({"audio": audio}))
                    logger.info(f"audio enviado ({len(audio)} chars)")
            except Exception as e:
                logger.warning(f"tts: {e}")
    except websockets.exceptions.ConnectionClosed:
        logger.info("cliente desconectou")


async def main():
    logger.info("="*50)
    logger.info("  Vox UmGrau Bridge v3")
    logger.info(f"  serve: {SERVER_URL}")
    logger.info(f"  auth: {SERVER_USER}:{SERVER_PASS[:4]}...")
    logger.info(f"  modelos: {models}")
    logger.info(f"  ws://0.0.0.0:8765")
    logger.info("="*50)

    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
