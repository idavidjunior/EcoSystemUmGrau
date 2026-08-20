#!/usr/bin/env python3
import sys
import re
import os

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
    
    # Build new function - simplified: just try old widget
    new_func = '''def _iniciar_widget() -> int:
    \"\"\"Inicia widget_controle_jarvis.py se nao estiver rodando.\"\"\"
    pid = _widget_pid()
    if pid:
        return pid
    try:
        import subprocess
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == \"nt\" else 0
        proc = subprocess.Popen(
            [PYTHON, str(WIDGET_SCRIPT)],
            cwd=str(ROOT),
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNUL,
        )
        MIC_PID.write_text(str(proc.pid), encoding=\"utf-8\")
        return proc.pid
    except Exception as e:
        print(\"[widget] erro iniciar widget antigo: {e}\", flush=True)
        return 0'''

    content = content[:idx] + new_func + content[end_idx:]
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: _iniciar_widget substituido')
else:
    print('_iniciar_widget nao encontrado')