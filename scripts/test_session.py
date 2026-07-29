import asyncio, websockets, json

async def test():
    async with websockets.connect("ws://127.0.0.1:8765") as ws:
        resp = json.loads(await ws.recv())
        print(f"Saudacao: {resp['text'][:80]}")

        await ws.send("teste de sessao unificada, diga apenas: primeira mensagem")
        resp = json.loads(await ws.recv())
        print(f"1a resposta: {resp['text'][:80]}")

        await ws.send("diga apenas: segunda mensagem, continuacao")
        resp = json.loads(await ws.recv())
        print(f"2a resposta: {resp['text'][:80]}")

        await ws.send("diga: terceira e ultima mensagem")
        resp = json.loads(await ws.recv())
        print(f"3a resposta: {resp['text'][:80]}")

asyncio.run(test())
