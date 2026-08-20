#!/usr/bin/env python3
import sys
import re

sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "def _iniciar_widget"
idx = content.find(target)

if idx >= 0:
    rest = content[idx:]
    lines = rest.split('\n')
    # Find next def line
    end_idx = idx
    for i, line in enumerate(lines):
        if line.strip().startswith('def ') and i > 0:
            end_idx = idx + sum(len(l) + 1 for l in lines[:i])
            break
        end_idx = idx + len(rest)
    
    new_func = '''    def _iniciar_widget() -> int:
        """Inicia widget_controle_jarvis.py se nao estiver rodando."""
        pid = _widget_pid()
        if pid:
            return pid
        try:
            import subprocess
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(
                ["python", str(WIDGET_SCRIPT)],
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
    print('_iniciar_widget nao encontrado')