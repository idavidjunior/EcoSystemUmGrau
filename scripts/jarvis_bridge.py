import asyncio
import websockets
import edge_tts
import base64
import json
import logging
import os
import subprocess
import re

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

COMUM_BASE = [
    OPENCODE_BIN, "run",
    "--format", "json",
    "--model", "opencode/deepseek-v4-flash-free",
    "--dir", WORKDIR,
    "--auto",
]


def sanitizar_texto(texto):
    texto = re.sub(r'```[\s\S]*?```', '', texto)
    texto = re.sub(r'`[^`]+`', '', texto)
    texto = re.sub(r'[*_~#]', '', texto)
    texto = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto)
    texto = re.sub(r'[<>{}()\[\]]', '', texto)
    texto = texto.replace('"', '').replace("'", '').replace('`', '')
    texto = re.sub(r'^\s*[-*+]\s+', '', texto, flags=re.MULTILINE)
    texto = texto.replace('\n', ' ').replace('\r', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


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
    tipos = {}
    textos_raw = []
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            t = obj.get("type", "?")
            tipos[t] = tipos.get(t, 0) + 1
            if t == "text":
                part = obj.get("part", {})
                if isinstance(part, dict):
                    texto = part.get("text", "")
                elif isinstance(part, str):
                    texto = part
                else:
                    texto = str(part) if part else ""
                textos_raw.append(repr(texto[:300]))
                if texto.strip():
                    ultimo_texto = texto.strip()
        except json.JSONDecodeError:
            continue
    logger.info(f"tipos de eventos no stdout: {tipos}")
    logger.info(f"textos encontrados: {textos_raw}")
    if ultimo_texto is None:
        logger.info(f"stdout (primeiros 800 chars): {stdout_text[:800]}")
    return ultimo_texto or "Sem resposta."


class OpenCodeClient:
    def __init__(self):
        self._historico = []

    async def consultar(self, mensagem: str) -> str:
        if self._historico:
            contexto = "\n".join(self._historico[-6:])
            prompt = f"{contexto}\n\nUsuário: {mensagem}"
        else:
            prompt = f"Usuário: {mensagem}"

        cmd = list(COMUM_BASE)
        cmd.append(prompt)

        cmd_str = subprocess.list2cmdline(cmd)
        logger.info(f"OC (hist={len(self._historico)//2}): {mensagem[:80]}")

        proc = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)

        stdout_text = stdout.decode(errors="replace")
        stderr_text = stderr.decode(errors="replace")

        rc = proc.returncode
        logger.info(f"RC={rc} stdout={len(stdout_text)}b stderr={len(stderr_text)}b")

        for line in stderr_text.splitlines():
            line = line.strip()
            if line:
                logger.info(f"[oc:err] {line}")

        resposta = extrair_resposta(stdout_text)
        logger.info(f"Resposta: {resposta[:200]}")
        self._historico.append(f"Usuário: {mensagem}")
        self._historico.append(f"Jarvis: {resposta}")
        return resposta


async def handler(ws, oc):
    saudacao = "Olá, sou o Jarvis do EcoSystemUmGrau. Estou ouvindo."
    logger.info("Gerando áudio da saudação...")
    audio = await gerar_audio(saudacao)
    await ws.send(json.dumps({"audio": audio, "text": saudacao}))
    logger.info(f"Saudação enviada ({len(audio)} chars)")

    try:
        async for msg in ws:
            logger.info(f"Recebido: {msg}")
            try:
                resposta = await oc.consultar(msg)
            except Exception as e:
                resposta = f"Erro ao processar: {e}"
                logger.error(f"Erro: {e}")

            logger.info("Gerando áudio da resposta...")
            audio = await gerar_audio(resposta)
            if audio:
                await ws.send(json.dumps({"audio": audio, "text": resposta}))
                logger.info(f"Resposta enviada ({len(audio)} chars)")
            else:
                await ws.send(json.dumps({"text": resposta}))
                logger.info("Resposta enviada (sem áudio)")
    except websockets.exceptions.ConnectionClosed:
        logger.info("Conexão encerrada pelo cliente.")


async def main():
    logger.info("=" * 50)
    logger.info("  Vox UmGrau — Bridge OpenCode + Edge-TTS")
    logger.info(f"  Voz: {TTS_VOICE}")
    logger.info("  ws://0.0.0.0:8765")
    logger.info("  Modelo: opencode/deepseek-v4-flash-free")
    logger.info("  Contexto: persistente (--continue)")
    logger.info("=" * 50)
    async with websockets.serve(lambda ws: handler(ws, OpenCodeClient()), "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
