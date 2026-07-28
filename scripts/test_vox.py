import asyncio, websockets, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

async def teste():
    async with websockets.connect("ws://127.0.0.1:8765") as ws:
        perguntas = [
            "O que o ecossistema fez hoje?",
            "Me de um resumo das ultimas tarefas",
            "Esta tudo pronto para o deploy?"
        ]
        for p in perguntas:
            print(f">> Enviando: {p}")
            await ws.send(p)
            resp = await ws.recv()
            print(f"<< Resposta: {resp[:200]}")
            print("-" * 50)

asyncio.run(teste())
