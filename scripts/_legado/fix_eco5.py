#!/usr/bin/env python3
import sys
import re

sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "def _iniciar_widget()"
idx = content.find(target)

if idx >= 0:
    rest = content[idx:]
    matches = list(re.finditer(r"^    def |\n    def ", rest, re.MULTILINE))
    if len(matches) > 1:
        end_idx = matches[1].start() + idx
    else:
        end_idx = len(content)
    
    new_func = "def _iniciar_widget() -> int:\\n    \"\"\"Inicia widget_controle_jarvis.py se nao estiver rodando.\"\"\"\\n    pid = _widget_pid()\\n    if pid:\\n        return pid\\n    try:\\n        import subprocess\\n        creationflags = subprocess.CREATE_NO_WINDOW if os.name == \"nt\" else 0\\n        proc = subprocess.Popen(\\n            [PYTHON, str(WIDGET_SCRIPT)],\\n            cwd=str(ROOT),\\n            creationflags=creationflags,\\n            stdout=subprocess.DEVNULL,\\n            stderr=subprocess.DEVNUL,\\n        )\\n        MIC_PID.write_text(str(proc.pid), encoding=\"utf-8\")\\n        return proc.pid\\n    except Exception as e:\\n        print(\"[widget] erro iniciar widget antigo: {e}\", flush=True)\\n        return 0"
    
    content = content[:idx] + new_func + content[end_idx:]
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: _iniciar_widget substituido')
else:
    print('_iniciar_widget nao encontrado')