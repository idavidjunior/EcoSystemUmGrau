import asyncio
import websockets
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vox")

OPENCODE_URL = "http://127.0.0.1:4096"

async def handler(ws):
    async with httpx.AsyncClient(timeout=120) as http:
        opencode_ok = True
        sess_id = None

        try:
            r = await http.post(f"{OPENCODE_URL}/session")
            sess_id = r.json()["id"]
            logger.info(f"OpenCode conectado. Sessão: {sess_id}")
        except Exception as e:
            opencode_ok = False
            logger.warning(f"OpenCode offline: {e}. Modo eco ativado.")

        saudacao = "Olá! Sou o Jarvis do EcoSystemUmGrau. Estou ouvindo."
        await ws.send(saudacao)
        logger.info(f"→ Android: {saudacao}")

        async for msg in ws:
            logger.info(f"← Android: {msg}")

            if not opencode_ok:
                resposta = f"[Vox UmGrau] Recebi: '{msg}'. (OpenCode offline)"
            else:
                try:
                    r = await http.post(
                        f"{OPENCODE_URL}/session/{sess_id}/message",
                        json={"parts": [{"type": "text", "text": msg}]}
                    )
                    resposta = r.json()["parts"][0]["text"]
                except Exception as e:
                    resposta = f"[Vox UmGrau] Erro no OpenCode: {e}"
                    opencode_ok = False

            await ws.send(resposta)
            logger.info(f"→ Android: {resposta[:120]}")

async def main():
    logger.info("=" * 50)
    logger.info("  Vox UmGrau — Bridge aguardando conexões")
    logger.info("  ws://0.0.0.0:8765")
    logger.info("=" * 50)
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
