#!/usr/bin/env python3
import sys
import re

sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the activate and deactivate functions
activate_func = '''
def activate() -> dict:
    """Ativa Eco: garante widget rodando, mostra janela, seta estado ativo."""
    # 1. Garante bridge flag
    BRIDGE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    BRIDGE_FLAG.touch(exist_ok=True)

    # 2. Inicia widget se necessario
    pid = _iniciar_widget()
    if not pid:
        return {"ok": False, "erro": "widget nao iniciou"}

    # 3. Mostra widget
    _mostrar_widget(pid)

    # 4. Seta estado ativo
    _escrever_estado(ativo=True, pausado=False)

    # 5. Narra "Eco ativado"
    try:
        from jarvis_audio import speak_direct
        speak_direct("Eco ativado")
    except Exception:
        pass

    return {"ok": True, "widget_pid": pid, "widget_visivel": True, "bridge_up": True, "narrador_ativo": True, "mensagem": "Eco ativado"}

def deactivate() -> dict:
    """Desativa Eco: esconde widget, seta estado inativo, widget narra "Eco desativado"."""
    # 1. Seta estado inativo
    _escrever_estado(ativo=False, pausado=True)

    # 2. Esconde widget
    pid = _widget_pid()
    if pid:
        try:
            import win32gui
            win32gui.ShowWindow(pid, 6)  # SW_MINIMIZE
        except Exception:
            pass

    # 3. Narra "Eco desativado"
    try:
        from jarvis_audio import speak_direct
        speak_direct("Eco desativado")
    except Exception:
        pass

    return {"ok": True, "widget_pid": pid, "widget_visivel": False, "bridge_up": True, "narrador_ativo": False, "mensagem": "Eco desativado"}
'''

# Find where to insert - look for _escrever_estado function and add after it
# Or just insert at the end before any trailing content

# Find _escrever_estado function
idx = content.find('def _escrever_estado')
if idx >= 0:
    # Find end of this function
    rest = content[idx:]
    # Find next def or end
    matches = list(re.finditer(r'^def ', rest, re.MULTILINE))
    if len(matches) > 1:
        end_idx = idx + matches[1].start()
    else:
        end_idx = len(content)
    
    # Insert before the next function
    new_content = content[:end_idx] + activate_func + content[end_idx:]
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS: activate e deactivate inseridos após _escrever_estado')
else:
    # Just append at the very end
    new_content = content + activate_func
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS: activate e deactivate inseridos no final do arquivo')