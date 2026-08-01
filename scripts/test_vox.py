import asyncio, websockets, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def teste_fix_punctuation():
    sys.path.insert(0, __import__('os').path.dirname(__file__))
    from jarvis_bridge import fix_punctuation
    casos = {
        "qual é o meu endereço": "Qual é o meu endereço?",
        "que horas são": "Que horas são?",
        "liga a luz da sala": "Liga a luz da sala.",
        "oi tudo bem": "Oi, tudo bem?",
        "bom dia que horas são": "Bom dia, que horas são?",
        "tudo bem você pode me ajudar": "Tudo bem. Você pode me ajudar?",
        "obrigado": "Obrigado.",
    }
    falhas = 0
    for entrada, esperado in casos.items():
        saida = fix_punctuation(entrada)
        ok = saida == esperado
        falhas += 0 if ok else 1
        print(f"[{'OK' if ok else 'FALHOU'}] {entrada!r} -> {saida!r}")
    assert falhas == 0, f"{falhas} caso(s) de pontuação falharam"
    print(f"fix_punctuation: {len(casos)}/{len(casos)} OK")


def teste_horas_para_fala():
    sys.path.insert(0, __import__('os').path.dirname(__file__))
    from jarvis_bridge import melhorar_fala
    casos = {
        "São 21:44.": "São 21 horas e 44.",
        "São exatamente 21:44.": "São exatamente 21 horas e 44.",
        "Agora são 22:00.": "Agora, são 22 horas em ponto.",
        "às 21:44 da noite": "Às 21 horas e 44 da noite.",
        "Sem hora nenhuma aqui.": "Sem hora nenhuma aqui.",
    }
    falhas = 0
    for entrada, esperado in casos.items():
        saida = melhorar_fala(entrada)
        ok = saida == esperado
        falhas += 0 if ok else 1
        print(f"[{'OK' if ok else 'FALHOU'}] {entrada!r} -> {saida!r}")
    assert falhas == 0, f"{falhas} caso(s) de hora falharam"
    print(f"horas_para_fala: {len(casos)}/{len(casos)} OK")


async def teste():
    async with websockets.connect("ws://127.0.0.1:8765") as ws:
        perguntas = [
            "qual o resumo das ultimas tarefas",       # STT cru → deve virar "Qual o resumo das últimas tarefas?"
            "me de um resumo do que fizemos hoje",     # → pergunta
            "esta tudo pronto para o deploy",          # → pergunta
            "toca uma musica",                          # → afirmação/ordem
        ]
        for p in perguntas:
            print(f">> Enviando: {p}")
            await ws.send(p)
            resp = await ws.recv()
            print(f"<< Resposta: {resp[:200]}")
            print("-" * 50)


if __name__ == "__main__":
    teste_fix_punctuation()
    teste_horas_para_fala()
    asyncio.run(teste())
