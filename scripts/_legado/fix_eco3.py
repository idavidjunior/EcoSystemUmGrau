#!/usr/bin/env python3
import sys
import re
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
    matches = list(re.finditer(r'^\s*def ', rest, re.MULTILINE))
    if len(matches) > 1:
        end_idx = matches[1].start() + idx
    else:
        end_idx = len(content)
    
    # Build new function
    new_func = """def _iniciar_widget() -> int:
    \"\"\"Inicia widget: prioriza unified_bridge.py.\"\"\"
    # Tenta contactar o bridge unificado
    try:
        from jarvis_bridge import Cliente
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        c = Cliente()
        # Teste simples: verifica se bridge responde
        result = loop.run_until_complete(c.perguntar("teste"))
        loop.close()
        return 0  # Bridge esta ativo, nao iniciar widget antigo
    except Exception:
        pass  # Bridge nao disponivel, tenta widget antigo
    
    # Se nao tiver bridge, inicia widget_controle_jarvis.py antigo
    try:
        pid = _widget_pid()
        if pid:
            return pid
        import subprocess
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
        return 0"""

    content = content[:idx] + new_func + content[end_idx:]
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: _iniciar_widget substituido (versao simplificada)')
else:
    print('_iniciar_widget nao encontrado nao encontrado')