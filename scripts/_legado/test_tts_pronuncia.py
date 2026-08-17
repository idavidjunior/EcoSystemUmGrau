import asyncio
import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from tts import SpeechPipeline
import base64, tempfile, os, ctypes

async def test():
    pipeline = SpeechPipeline()
    text = 'a d b auto connect ponto pai'
    print(f'Texto original: {text}')
    prepared, meta = pipeline.prepare(text)
    print(f'Texto preparado: {prepared}')
    print(f'Metadata: {meta}')
    audio_b64 = await pipeline.synthesize(text)
    print(f'Áudio gerado: {len(audio_b64)} chars base64')
    audio_bytes = base64.b64decode(audio_b64)
    tmp = tempfile.mktemp(suffix='.mp3')
    with open(tmp, 'wb') as f:
        f.write(audio_bytes)
    print(f'Salvo em: {tmp}')
    mci = ctypes.windll.winmm.mciSendStringW
    alias = 'test_tts'
    r = mci(f'open "{tmp}" type mpegvideo alias {alias}', None, 0, 0)
    if r == 0:
        mci(f'play {alias} wait', None, 0, 0)
        mci(f'close {alias}', None, 0, 0)
        print('Reproduzido!')
    else:
        print(f'Erro MCI: {r}')
    os.unlink(tmp)

asyncio.run(test())