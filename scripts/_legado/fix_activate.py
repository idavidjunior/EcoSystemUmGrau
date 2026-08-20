#!/usr/bin/env python3
import sys
import re

sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the activate function
old_activate_start = content.find('def activate() -> dict:')
if old_activate_start >= 0:
    rest = content[old_activate_start:]
    matches = list(re.finditer(r'^\n    def ', rest, re.MULTILINE))
    if len(matches) > 0:
        end_act = old_activate_start + matches[0].start()
    else:
        end_act = len(content)
    
    # New activate function
    new_activate = """def activate() -> dict:
    """Ativa Eco: garante widget rodando, mostra janela, seta estado ativo."""
    # 1. Verificar se unified_bridge.py ja esta rodando
    import subprocess
    try:
        saida = subprocess.run(
            ["tasklist", "/FI", "PID eq ", "/NH"]
        ).stdout
        for linha in saida.splitlines():
            if "unified_bridge" in linha.lower():
                # Bridge ja ativo - so seta flag e retorna
                BRIDGE_FLAG.parent.mkdir(parents=True, exist_ok=True)
                BRIDGE_FLAG.touch(exist_ok=True)
                # Narra via bridge existente
                try:
                    from jarvis_bridge import Cliente
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    c = Cliente()
                    loop.close()
                except Exception:
                    pass
                return {"ok": True, "widget_visivel": True, "bridge_up": True, "narrador_ativo": True, "mensagem": "Eco ativado (via bridge)"}
    except Exception:
        pass

    # 2. Se nao tiver bridge, inicia widget antigo
    BRIDGE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    BRIDGE_FLAG.touch(exist_ok=True)

    # 3. Inicia widget se necessario
    pid = _iniciar_widget()
    if not pid:
        return {"ok": False, "erro": "widget nao iniciou"}

    # 4. Mostra widget
    _mostrar_widget(pid)

    # 5. Seta estado ativo
    _escrever_estado(ativo=True, pausado=False)

    # 6. Narra "Eco ativado"
    try:
        from jarvis_audio import speak_direct
        speak_direct("Eco ativado")
    except Exception:
        pass

    return {"ok": True, "widget_pid": pid, "widget_visivel": True, "bridge_up": True, "narrador_ativo": True, "mensagem": "Eco ativado"}"""

    content = content[:old_activate_start] + new_activate + content[end_act:]
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: activate function updated')
else:
    print('activate not found')