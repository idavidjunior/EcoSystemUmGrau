"""Teste de latência TTS: mede tempo de geração vs reprodução."""
import asyncio
import ctypes
import os
import tempfile
import time
import edge_tts

VOICE = "pt-BR-AntonioNeural"
RATE = "+0%"
PITCH = "+0Hz"
TEXT = "Teste de latência do Jarvis. Isso é apenas um teste rápido."

async def gen():
    communicate = edge_tts.Communicate(TEXT, VOICE, rate=RATE, pitch=PITCH)
    audio = b""
    t0 = time.time()
    chunk_count = 0
    first_chunk_time = None
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
            chunk_count += 1
            if first_chunk_time is None and len(audio) > 2000:
                first_chunk_time = time.time() - t0
    t1 = time.time()
    return audio, t1 - t0, first_chunk_time, chunk_count

t_start = time.time()
audio, gen_time, first_chunk_time, chunks = asyncio.run(gen())
t_gen_done = time.time()

mp3 = os.path.join(tempfile.gettempdir(), "test_latency.mp3")
with open(mp3, "wb") as f:
    f.write(audio)

print(f"Texto: {len(TEXT)} chars")
print(f"Áudio: {len(audio)} bytes, {chunks} chunks")
print(f"Geração TTS completa: {gen_time:.2f}s")
print(f"Primeiro chunk (>2KB): {first_chunk_time:.2f}s" if first_chunk_time else "Primeiro chunk: N/A")

# MCI playback
mci = ctypes.windll.winmm.mciSendStringW
alias = f"lat{int(time.time()*1000)}"
r = mci(f'open "{mp3}" type mpegvideo alias {alias}', None, 0, 0)
t2 = time.time()
mci(f"play {alias}", None, 0, 0)
t3 = time.time()
print(f"MCI open: {t2 - t_gen_done:.2f}s")
print(f"MCI play: {t3 - t2:.2f}s")
print(f"Tempo até começar a tocar (geração + open + play): {t3 - t_start:.2f}s")

time.sleep(3)
mci(f"close {alias}", None, 0, 0)
print(f"Total: {time.time() - t_start:.2f}s")
