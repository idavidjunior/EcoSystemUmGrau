import asyncio
import websockets
import httpx
import edge_tts
import base64
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vox")

OPENCODE_URL = "http://127.0.0.1:4096"
TTS_VOICE = "pt-BR-AntonioNeural"

async def gerar_audio(texto):
    communicate = edge_tts.Communicate(texto, TTS_VOICE)
    audio = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return base64.b64encode(audio).decode()

async def handler(ws):
    async with httpx.AsyncClient(timeout=120) as http:
        opencode_ok = True
        sess_id = None

        try:
            r = await http.post(f"{OPENCODE_URL}/session")
            sess_id = r.json()["id"]
            logger.info(f"OpenCode OK. Sessão: {sess_id}")
        except Exception as e:
            opencode_ok = False
            logger.warning(f"OpenCode offline: {e}")

        saudacao = "Olá, sou o Jarvis do EcoSystemUmGrau. Estou ouvindo."
        logger.info("Gerando áudio da saudação...")
        audio = await gerar_audio(saudacao)
        await ws.send(json.dumps({"audio": audio, "text": saudacao}))
        logger.info(f"Saudação enviada ({len(audio)} chars)")

        try:
            async for msg in ws:
                logger.info(f"Recebido: {msg}")

                if not opencode_ok:
                    resposta = f"Recebi sua mensagem: '{msg}'. Estou em modo offline."
                else:
                    try:
                        r = await http.post(
                            f"{OPENCODE_URL}/session/{sess_id}/message",
                            json={"parts": [{"type": "text", "text": msg}]}
                        )
                        resposta = r.json()["parts"][0]["text"]
                    except Exception as e:
                        resposta = f"Erro ao processar: {e}"
                        opencode_ok = False

                logger.info("Gerando áudio da resposta...")
                audio = await gerar_audio(resposta)
                await ws.send(json.dumps({"audio": audio, "text": resposta}))
                logger.info(f"Resposta enviada ({len(audio)} chars)")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Conexão encerrada pelo cliente.")

async def main():
    logger.info("=" * 50)
    logger.info("  Vox UmGrau — Bridge Edge-TTS")
    logger.info(f"  Voz: {TTS_VOICE}")
    logger.info("  ws://0.0.0.0:8765")
    logger.info("=" * 50)
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
