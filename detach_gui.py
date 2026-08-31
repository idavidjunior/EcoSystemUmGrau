"""Helper para desacoplar a GUI do console que a invocou.

Uso: python detach_gui.py
Cria o processo pythonw.exe detached e fecha. A GUI continua rodando.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv-gui"
PYTHONW = VENV / "Scripts" / "pythonw.exe"
MAIN = ROOT / "gui-desktop" / "main.py"

if not PYTHONW.exists():
    sys.exit(f"venv-gui nao encontrado: {PYTHONW}")
if not MAIN.exists():
    sys.exit(f"main.py nao encontrado: {MAIN}")

subprocess.Popen(
    [str(PYTHONW), str(MAIN)],
    cwd=str(ROOT),
    creationflags=0x00000008 | 0x00000200,
    close_fds=True,
)
print("GUI detached")
