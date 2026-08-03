import base64, tempfile
from pathlib import Path
import ctypes
import asyncio
import edge_tts

# Teste direto do MCI
mp3 = Path(tempfile.gettempdir()) / 'teste_mci.mp3'

async def gen():
    c = edge_tts.Communicate('Teste direto MCI', 'pt-BR-AntonioNeural')
    a = b''
    async for chunk in c.stream():
        if chunk['type'] == 'audio':
            a += chunk['data']
    return a

audio = asyncio.run(gen())
mp3.write_bytes(audio)
print('Arquivo criado:', mp3.exists(), mp3.stat().st_size)

mci = ctypes.windll.winmm.mciSendStringW
alias = 'teste123'
r = mci(f'open "{mp3}" type mpegvideo alias {alias}', None, 0, 0)
print('open:', r)
r = mci(f'play {alias}', None, 0, 0)
print('play:', r)
import time
time.sleep(3)
mci(f'stop {alias}', None, 0, 0)
mci(f'close {alias}', None, 0, 0)
print('Fim')