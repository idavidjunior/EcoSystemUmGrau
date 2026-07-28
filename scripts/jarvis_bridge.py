import asyncio
import websockets
import httpx
import base64
import json
import io
import wave
import logging

from piper import PiperVoice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vox")

OPENCODE_URL = "http://127.0.0.1:4096"
VOZ_MODELO = "C:\\Users\\Playtec-bancada\\.cache\\huggingface\\hub\\models--jgkawell--jarvis\\snapshots\\37f8763122312665f091d1fc760abaf1f79b02cc\\en\\en_GB\\jarvis\\medium\\jarvis-medium.onnx"

voice = PiperVoice.load(VOZ_MODELO)

def gerar_wav(texto):
    chunks = list(voice.synthesize(texto))
    audio = b""
    sr, ch, sw = 22050, 1, 2
    for c in chunks:
        audio += c.audio_int16_bytes
        sr = c.sample_rate or sr
        ch = c.sample_channels or ch
        sw = c.sample_width or sw
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(sw)
        w.setframerate(sr)
        w.writeframes(audio)
    return base64.b64encode(buf.getvalue()).decode()

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

        saudacao = "Ola, sou o Jarvis do EcoSystemUmGrau. Estou ouvindo."
        logger.info(f"Gerando áudio para saudação...")
        audio = gerar_wav(saudacao)
        await ws.send(json.dumps({"audio": audio, "text": saudacao}))
        logger.info(f"Enviada saudação ({len(audio)} chars base64)")

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

                logger.info(f"Gerando áudio para resposta...")
                audio = gerar_wav(resposta)
                await ws.send(json.dumps({"audio": audio, "text": resposta}))
                logger.info(f"Resposta enviada ({len(audio)} chars base64)")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Conexão encerrada pelo cliente.")

async def main():
    logger.info("=" * 50)
    logger.info("  Vox UmGrau — Bridge")
    logger.info("  Piper TTS + Modelo Jarvis (Hugging Face)")
    logger.info("  ws://0.0.0.0:8765")
    logger.info("=" * 50)
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
