import asyncio, websockets

async def teste():
    async with websockets.connect("ws://127.0.0.1:8765") as ws:
        perguntas = [
            "O que o ecossistema fez hoje?",
            "Me dê um resumo das últimas tarefas",
            "Está tudo pronto para o deploy?"
        ]
        for p in perguntas:
            print(f"→ Enviando: {p}")
            await ws.send(p)
            resp = await ws.recv()
            print(f"← Resposta: {resp[:200]}")
            print("-" * 50)

asyncio.run(teste())
