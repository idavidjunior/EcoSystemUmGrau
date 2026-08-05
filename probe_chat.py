import asyncio, websockets, json, time, sys

async def t():
    print('conectando...')
    async with websockets.connect('ws://127.0.0.1:8765', open_timeout=15) as ws:
        print('conectado, esperando saudacao (60s)...')
        try:
            saud = await asyncio.wait_for(ws.recv(), timeout=60)
            d = json.loads(saud)
            print('saudacao text:', d.get('text','')[:80], '| audio:', len(d.get('audio','')))
        except asyncio.TimeoutError:
            print('saudacao TIMEOUT - serve lento gerando')
            return
        t0 = time.time()
        await ws.send('o que voce sabe sobre persistencia em runtime')
        try:
            r = await asyncio.wait_for(ws.recv(), timeout=180)
            dt = time.time() - t0
            d = json.loads(r)
            print(f'Resposta em {dt:.1f}s')
            print('  text:', d.get('text','')[:300])
            print('  audio:', len(d.get('audio','')), 'bytes')
        except asyncio.TimeoutError:
            print(f'LLM TIMEOUT apos {time.time()-t0:.1f}s')

asyncio.run(t())
