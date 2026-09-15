#!/usr/bin/env pythonw3
"""Launcher do Widget de Supervisao — executa sem console."""
import subprocess
import sys
from pathlib import Path

base = Path(__file__).resolve().parent.parent
script = base / "scripts" / "widget_supervisao.py"
pythonw = Path(sys.executable).parent / "pythonw.exe"

if not pythonw.exists():
    pythonw = Path(sys.executable)

subprocess.Popen(
    [str(pythonw), "-u", str(script)],
    cwd=str(base),
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
)
