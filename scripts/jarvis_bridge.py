import asyncio
import websockets
import edge_tts
import base64
import json
import logging
import os
import subprocess
import shlex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vox")

TTS_VOICE = "en-US-AndrewMultilingualNeural"
TTS_PITCH = "-30Hz"
TTS_RATE = "+0%"

OPENCODE_BIN = os.path.join(
    os.environ.get("APPDATA", ""),
    r"npm\node_modules\opencode-ai\bin\opencode.exe"
)
WORKDIR = r"C:\Users\Playtec-bancada\Desktop\Codigos"


async def gerar_audio(texto):
    communicate = edge_tts.Communicate(texto, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    audio = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return base64.b64encode(audio).decode()


async def consultar_opencode(mensagem):
    cmd_list = [
        OPENCODE_BIN, "run", mensagem,
        "--format", "json",
        "--model", "opencode/deepseek-v4-flash-free",
        "--dir", WORKDIR,
        "--auto",
    ]
    # --print-logs causa problemas no Windows, logs vao pro stderr msm sem flag
    cmd_str = subprocess.list2cmdline(cmd_list)
    logger.info(f"Executando: [{len(cmd_str)} chars] {cmd_str}")

    proc = await asyncio.create_subprocess_shell(
        cmd_str,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)

    rc = proc.returncode
    stderr_text = stderr.decode(errors="replace")
    stdout_text = stdout.decode(errors="replace")
    logger.info(f"RC={rc} STDERR({len(stderr_text)}) bytes")
    for line in stderr_text.splitlines():
        logger.info(f"[opencode:stderr] {line}")
    logger.info(f"STDOUT({len(stdout_text)} bytes): {stdout_text[:500]}")
    resposta = "Sem resposta."
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get("type") == "text" and "text" in obj.get("part", {}):
                resposta = obj["part"]["text"]
                break
        except json.JSONDecodeError:
            continue

    logger.info(f"Resposta: {resposta}")
    return resposta


async def handler(ws):
    saudacao = "Olá, sou o Jarvis do EcoSystemUmGrau. Estou ouvindo."
    logger.info("Gerando áudio da saudação...")
    audio = await gerar_audio(saudacao)
    await ws.send(json.dumps({"audio": audio, "text": saudacao}))
    logger.info(f"Saúdação enviada ({len(audio)} chars)")

    try:
        async for msg in ws:
            logger.info(f"Recebido: {msg}")
            try:
                resposta = await consultar_opencode(msg)
            except Exception as e:
                resposta = f"Erro ao processar: {e}"
                logger.error(f"Erro: {e}")

            logger.info("Gerando áudio da resposta...")
            audio = await gerar_audio(resposta)
            await ws.send(json.dumps({"audio": audio, "text": resposta}))
            logger.info(f"Resposta enviada ({len(audio)} chars)")
    except websockets.exceptions.ConnectionClosed:
        logger.info("Conexão encerrada pelo cliente.")


async def main():
    logger.info("=" * 50)
    logger.info("  Vox UmGrau — Bridge OpenCode + Edge-TTS")
    logger.info(f"  Voz: {TTS_VOICE}")
    logger.info("  ws://0.0.0.0:8765")
    logger.info("  Modelo: opencode/deepseek-v4-flash-free")
    logger.info("=" * 50)
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
