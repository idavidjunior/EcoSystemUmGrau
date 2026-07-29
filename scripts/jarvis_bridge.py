import asyncio
import websockets
import edge_tts
import base64
import json
import logging
import os
import subprocess
import re
import sys
import time

logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler(r"C:\Users\Playtec-bancada\Desktop\Codigos\bridge_log.txt", mode="a")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger("vox")

TTS_VOICE = "pt-BR-ThalitaMultilingualNeural"
TTS_PITCH = "-30Hz"
TTS_RATE = "+0%"

OPENCODE_BIN = os.path.join(
    os.environ.get("APPDATA", ""),
    r"npm\node_modules\opencode-ai\bin\opencode.exe"
)
WORKDIR = r"C:\Users\Playtec-bancada\Desktop\Codigos"
HISTORICO_PATH = r"C:\Users\Playtec-bancada\Desktop\Codigos\bridge_historico.json"
MAX_HIST = 8
MAX_TOOL_OUTPUT = 500


def sanitizar_texto(texto):
    if not texto:
        return ""
    texto = re.sub(r'```[\s\S]*?```', '', texto)
    texto = re.sub(r'`[^`]+`', '', texto)
    texto = re.sub(r'[*_~#]', '', texto)
    texto = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto)
    texto = re.sub(r'[<>{}()\[\]]', '', texto)
    texto = texto.replace('"', '').replace("'", '').replace('`', '')
    texto = re.sub(r'^\s*[-*+]\s+', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto[:2000]


async def gerar_audio(texto):
    texto = sanitizar_texto(texto)
    if not texto:
        logger.warning("texto vazio, pulando TTS")
        return ""
    communicate = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    audio = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return base64.b64encode(audio).decode()


def extrair_resposta(stdout_text: str) -> str:
    ultimo_texto = None
    tool_outputs = []
    tipos = {}
    erros_json = 0
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            t = obj.get("type", "?")
            tipos[t] = tipos.get(t, 0) + 1
            if t == "text":
                part = obj.get("part")
                if isinstance(part, dict):
                    texto = part.get("text", "")
                elif isinstance(part, str):
                    texto = part
                else:
                    continue
                if isinstance(texto, str) and texto.strip():
                    ultimo_texto = texto.strip()
            if t in ("tool_use", "tool_result"):
                part = obj.get("part")
                if isinstance(part, dict):
                    state = part.get("state")
                    if isinstance(state, dict) and state.get("status") == "completed":
                        output = state.get("output")
                        if isinstance(output, str) and output.strip():
                            tool_outputs.append(output.strip())
        except json.JSONDecodeError:
            erros_json += 1
            continue

    logger.info(f"tipos={tipos} tool_outputs={len(tool_outputs)} erros_json={erros_json}")

    if ultimo_texto:
        return ultimo_texto

    if tool_outputs:
        melhor = tool_outputs[-1][:MAX_TOOL_OUTPUT]
        return melhor

    logger.info(f"stdout(800): {stdout_text[:800]}")
    return None


async def executar_opencode(prompt: str, timeout_sec: int = 180) -> str | None:
    cmd = [
        OPENCODE_BIN, "run",
        "--format", "json",
        "--model", "opencode/deepseek-v4-flash-free",
        "--dir", WORKDIR,
        "--auto",
        prompt,
    ]
    cmd_str = subprocess.list2cmdline(cmd)

    proc = await asyncio.create_subprocess_shell(
        cmd_str,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    t0 = time.time()
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        proc.kill()
        logger.error("timeout exec opencode")
        return None

    elapsed = time.time() - t0
    stdout_text = stdout.decode(errors="replace")
    stderr_text = stderr.decode(errors="replace")

    logger.info(f"RC={proc.returncode} stdout={len(stdout_text)}b stderr={len(stderr_text)}b t={elapsed:.1f}s")

    for line in stderr_text.splitlines():
        line = line.strip()
        if line:
            logger.info(f"[oc:err] {line}")

    return extrair_resposta(stdout_text)


class OpenCodeClient:
    def __init__(self):
        self._historico = self._carregar_historico()

    def _carregar_historico(self) -> list:
        try:
            with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data[-MAX_HIST:]
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return []

    def _salvar_historico(self):
        try:
            with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
                json.dump(self._historico[-MAX_HIST:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"erro salvando historico: {e}")

    def _montar_prompt(self, mensagem: str) -> str:
        if self._historico:
            if len(self._historico) >= 2:
                ctx = ""
                for i in range(0, len(self._historico), 2):
                    u = self._historico[i] if i < len(self._historico) else ""
                    j = self._historico[i + 1] if i + 1 < len(self._historico) else ""
                    ctx += f"{u}\n{j}\n"
                return f"{ctx}---\nUsuário: {mensagem}\nJarvis:"
            return f"Usuário: {mensagem}\nJarvis:"
        return f"Usuário: {mensagem}\nJarvis:"

    async def consultar(self, mensagem: str) -> str:
        prompt = self._montar_prompt(mensagem)
        qtd_hist = len(self._historico) // 2
        logger.info(f"OC hist={qtd_hist}: {mensagem[:80]}")

        resposta = await executar_opencode(prompt)

        if not resposta:
            logger.warning("resposta vazia, tentando retry com prompt direto")
            resposta = await executar_opencode(f"Responda em português: {mensagem}")

        if not resposta:
            logger.warning("retry falhou, usando fallback tool_output")
            resposta = None

        if not resposta:
            resposta = "Sem resposta."

        self._historico.append(f"Usuário: {mensagem}")
        self._historico.append(f"Jarvis: {resposta[:300]}")
        self._salvar_historico()
        return resposta


async def handler(ws):
    oc = OpenCodeClient()
    qtd_hist = len(oc._historico) // 2
    logger.info(f"Conexao aberta, historico={qtd_hist} turnos")

    saudacao = "Olá, sou o Jarvis do EcoSystemUmGrau. Estou ouvindo."
    log = logger
    log.info("Gerando audio da saudacao...")
    audio = await gerar_audio(saudacao)
    await ws.send(json.dumps({"audio": audio, "text": saudacao}))
    log.info(f"saudacao enviada ({len(audio)} chars)")

    try:
        async for msg in ws:
            log.info(f"Recebido: {msg[:100]}")
            try:
                resposta = await oc.consultar(msg)
            except Exception as e:
                resposta = f"Erro ao processar: {e}"
                log.error(f"Erro handler: {e}", exc_info=True)

            log.info("Gerando audio da resposta...")
            audio = await gerar_audio(resposta)
            payload = {"text": resposta}
            if audio:
                payload["audio"] = audio
            await ws.send(json.dumps(payload))
            log.info(f"resposta enviada text={len(resposta)} audio={len(audio) if audio else 0}")
    except websockets.exceptions.ConnectionClosed:
        log.info("Conexao encerrada pelo cliente.")


async def main():
    log = logger
    log.info("=" * 50)
    log.info("  Vox UmGrau — Bridge OpenCode + Edge-TTS")
    log.info(f"  Voz: {TTS_VOICE}")
    log.info("  ws://0.0.0.0:8765")
    log.info("  Modelo: opencode/deepseek-v4-flash-free")
    log.info(f"  Contexto: injecao + JSON ({MAX_HIST} entradas)")
    log.info("  Fallback: tool_output + retry")
    log.info("=" * 50)

    historico_path = HISTORICO_PATH
    log.info(f"Historico em: {historico_path}")

    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
