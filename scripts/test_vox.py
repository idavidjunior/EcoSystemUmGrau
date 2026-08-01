import asyncio, websockets, sys, re

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


def teste_normalizar_hora_display():
    sys.path.insert(0, __import__('os').path.dirname(__file__))
    from jarvis_bridge import normalizar_hora_display, melhorar_fala
    casos = {
        "São 23:29 em São Paulo.": "São 23:29 em São Paulo.",
        "São 23 horas e 29 em São Paulo.": "São 23:29 em São Paulo.",
        "Agora são 22 horas em ponto.": "Agora são 22:00.",
        "Já são 22 horas e 30.": "Já são 22:30.",
        "São 09h30 agora.": "São 09:30 agora.",
        "São 09 hs 30.": "São 09:30.",
        "São 23 e 29 da noite.": "São 23:29 da noite.",
        "São 15 e 45.": "São 15:45.",
        "Sem hora nenhuma aqui.": "Sem hora nenhuma aqui.",
        "Faltam 2 e 3 coisas na lista.": "Faltam 2 e 3 coisas na lista.",
    }
    falhas = 0
    for entrada, esperado in casos.items():
        saida = normalizar_hora_display(entrada)
        ok = saida == esperado
        falhas += 0 if ok else 1
        print(f"[{'OK' if ok else 'FALHOU'}] tela {entrada!r} -> {saida!r}")
    roundtrip = [
        ("São 23:29 em São Paulo.", "São 23 horas e 29 em São Paulo."),
        ("Agora são 22:00.", "Agora, são 22 horas em ponto."),
        ("São 23 horas e 29 em São Paulo.", "São 23 horas e 29 em São Paulo."),
    ]
    for tela, fala in roundtrip:
        f = melhorar_fala(normalizar_hora_display(tela))
        ok = f == fala
        falhas += 0 if ok else 1
        print(f"[{'OK' if ok else 'FALHOU'}] roundtrip tela={normalizar_hora_display(tela)!r} fala={f!r}")
    assert falhas == 0, f"{falhas} caso(s) de hora na tela falharam"
    print(f"normalizar_hora_display: {len(casos)}/{len(casos)} OK")


def teste_caminho_rapido():
    sys.path.insert(0, __import__('os').path.dirname(__file__))
    from jarvis_bridge import caminho_rapido
    casas = {
        "que horas são": ("horas", r'\d{2}:\d{2}'),
        "que horas": ("horas", r'\d{2}:\d{2}'),
        "qual a data de hoje": ("data", r'\d{2}/\d{2}/\d{4}'),
        "que dia é hoje": ("dia", r'\d{2}/\d{2}/\d{4}'),
        "você está aí": ("status", r'online|atendendo'),
        "status do sistema": ("status", r'online|inicializando'),
        "você está funcionando": ("status", r'online'),
        "tá funcionando?": ("status", r'online'),
        "lista os arquivos do projeto": (None, None),
        "toca uma música": (None, None),
        "você já fez o teste com a conexão da NVidia está funcionando": (None, None),
        "o que está funcionando agora": (None, None),
        "amanhã eu preciso ir ao mercado": (None, None),
        "vai chover amanhã": ("previsao", r'Amanh'),
    }
    falhas = 0
    for entrada, (esperado, padrao) in casas.items():
        saida = caminho_rapido(entrada)
        if esperado is None:
            ok = saida is None
            print(f"[{'OK' if ok else 'FALHOU'}] {entrada!r} -> {saida!r} (deve ser None)")
        else:
            ok = saida is not None and re.search(padrao, saida) is not None
            print(f"[{'OK' if ok else 'FALHOU'}] {entrada!r} -> {saida!r}")
        falhas += 0 if ok else 1
    assert falhas == 0, f"{falhas} caso(s) de caminho rapido falharam"
    print(f"caminho_rapido: {len(casas)}/{len(casas)} OK")


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
    teste_normalizar_hora_display()
    teste_caminho_rapido()
    asyncio.run(teste())
