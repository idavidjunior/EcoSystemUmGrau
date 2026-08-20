#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

# Read current eco_widget.py
with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find _iniciar_widget and replace
target_start = 'def _iniciar_widget()'
idx = content.find(target_start)

if idx >= 0:
    # Find function end - look for next top-level def
    rest = content[idx:]
    # Find next 'def ' at column 0 (start of line)
    import re
    matches = list(re.finditer(r'^\s*def ', rest, re.MULTILINE))
    if len(matches) > 1:
        # Second def is the next function
        end_idx = matches[1].start() + idx
    else:
        end_idx = len(content)
    
    # Build new function
    new_func = '''def _iniciar_widget() -> int:
    """Inicia widget: prioriza unified_bridge.py, caiia para widget_controle_jarvis.py."""
    # 1. Verificar se unified_bridge.py ja esta rodando
    import subprocess
    try:
        saida = subprocess.run(
            ["tasklist", "/FI", "PID eq ", "/NH"]
        ).stdout
        for linha in saida.splitlines():
            if "unified_bridge" in linha.lower():
                # unified_bridge ja esta ativo - pedir para ele mostrar o widget
                try:
                    from jarvis_bridge import Cliente
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    c = Cliente()
                    result = loop.run_until_complete(c.mostrar_widget())
                    loop.close()
                    return 0  # Indica que bridge vai gerenciar
                except Exception as e:
                    print("[eco] erro ao contactar bridge: {e}")
    except Exception:
        pass
    
    # 2. Se nao tiver unified_bridge, inicia widget_controle_jarvis.py antigo
    pid = _widget_pid()
    if pid:
        return pid
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.Popen(
            [PYTHON, str(WIDGET_SCRIPT)],
            cwd=str(ROOT),
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNUL,
        )
        MIC_PID.write_text(str(proc.pid), encoding="utf-8")
        return proc.pid
    except Exception as e:
        print("[widget] erro iniciar widget antigo: {e}", flush=True)
        return 0'''
    
    content = content[:idx] + new_func + content[end_idx:]
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: _iniciar_widget substituido')
else:
    print('_iniciar_widget not found in file')
    # Debug: show what's around line 200
    lines = content.split('\n')
    for i in range(min(250, len(lines))):
        if 'iniciar' in lines[i].lower() or 'widget' in lines[i].lower():
            print(f"Line {i+1}: {lines[i].rstrip()}")