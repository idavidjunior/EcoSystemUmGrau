"""Executa health_check e salva em UTF-8 puro no runtime/health/."""
import sys
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from runtime_state import health_check, render_health_check

HEALTH_DIR = BASE / "runtime" / "health"
HEALTH_DIR.mkdir(parents=True, exist_ok=True)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out_file = HEALTH_DIR / f"health_{ts}.txt"

resultado = health_check()
texto = render_health_check(resultado)

with open(out_file, 'w', encoding='utf-8') as f:
    f.write(texto)

print(f"OK: {out_file}")
