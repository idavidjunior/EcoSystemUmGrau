"""Launcher sem console para o Cerebro Vivo.

Executa widget_grafo.py via pythonw.exe (sem janela preta).
Integrado ao EcoSystemUmGrau: usa mesmo runtime, mesmas configs.
"""
import sys
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "widget_grafo.py"

if __name__ == "__main__":
    # Executa com pythonw.exe (sem console)
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.exists():
        # Fallback: python.exe com CREATE_NO_WINDOW
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen([sys.executable, str(SCRIPT)], 
                         cwd=str(ROOT), creationflags=CREATE_NO_WINDOW)
    else:
        subprocess.Popen([str(pythonw), str(SCRIPT)], cwd=str(ROOT))