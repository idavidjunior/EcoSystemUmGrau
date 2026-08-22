"""Cria atalho .lnk para o Cerebro Vivo no desktop e na pasta do projeto."""
import os
import sys
from pathlib import Path

try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    # Tenta instalar
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "winshell", "pywin32", "-q"])
    import winshell
    from win32com.client import Dispatch

ROOT = Path(__file__).resolve().parent
PYTHONW = Path(sys.executable).with_name("pythonw.exe")
SCRIPT = ROOT / "scripts" / "widget_grafo.py"

def criar_atalho(destino: Path):
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(destino))
    shortcut.TargetPath = str(PYTHONW)
    shortcut.Arguments = f'"{SCRIPT}"'
    shortcut.WorkingDirectory = str(ROOT)
    shortcut.Description = "Cerebro Vivo - Telemetria visual do Jarvis"
    shortcut.IconLocation = f"{PYTHONW}, 0"
    shortcut.Save()
    print(f"Atalho criado: {destino}")

# Desktop
desktop = Path(winshell.desktop())
criar_atalho(desktop / "Cerebro Vivo.lnk")

# Pasta do projeto
criar_atalho(ROOT / "Cerebro Vivo.lnk")

print("OK - Atalhos criados no Desktop e na pasta do projeto")