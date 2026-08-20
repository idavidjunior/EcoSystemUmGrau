#!/usr/bin/env python3
import sys
import re

sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if _iniciar_widget exists
if 'def _iniciar_widget' not in content:
    # Add it before activate
    new_func = "def _iniciar_widget() -> int:\\n    \"\"\"Inicia widget_controle_jarvis.py se nao estiver rodando.\"\"\"\\n    pid = _widget_pid()\\n    if pid:\\n        return pid\\n    try:\\n        import subprocess\\n        creationflags = subprocess.CREATE_NO_WINDOW if os.name == \"nt\" else 0\\n        proc = subprocess.Popen(\\n            [\"python\", str(WIDGET_SCRIPT)],\\n            cwd=str(ROOT),\\n            creationflags=creationflags,\\n            stdout=subprocess.DEVNULL,\\n            stderr=subprocess.DEVNUL,\\n        )\\n        MIC_PID.write_text(str(proc.pid), encoding=\"utf-8\")\\n        return proc.pid\\n    except Exception as e:\\n        print(\"[widget] erro iniciar widget antigo: {e}\", flush=True)\\n        return 0"
    
    # Find where activate starts and insert _iniciar_widget before it
    idx = content.find('def activate')
    if idx >= 0:
        new_content = content[:idx] + new_func + content[idx:]
        with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\eco_widget.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('SUCCESS: _iniciar_widget adicionado')
    else:
        print('_activate not found')
else:
    print('_iniciar_widget ja existe')