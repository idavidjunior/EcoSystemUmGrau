"""desejos_loop.py — manifesta os desejos de aprendizado do Jarvis periodicamente.

Roda em background e invoca desejos_aprendizado.py com voz em intervalos
regulares, respeitando uma janela de horario (quiet hours).

Variaveis de ambiente:
  DESEJOS_INTERVALO  segundos entre manifestacoes (padrao 2700 = 45 min)
  DESEJOS_INICIO     hora inicial da janela (padrao 9)
  DESEJOS_FIM        hora final da janela (padrao 22)
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "desejo_aprendizado.py"
LOG = ROOT / "scripts" / "desejos_loop_log.txt"

INTERVALO = int(os.environ.get("DESEJOS_INTERVALO", "2700"))
INICIO = int(os.environ.get("DESEJOS_INICIO", "9"))
FIM = int(os.environ.get("DESEJOS_FIM", "22"))


def log(msg):
    linha = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(linha, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def na_janela(agora):
    return INICIO <= agora.hour < FIM


def main():
    log(f"Loop de desejos iniciado (intervalo={INTERVALO}s, janela {INICIO}h-{FIM}h)")
    try:
        while True:
            agora = datetime.now()
            if na_janela(agora):
                try:
                    subprocess.run([sys.executable, str(SCRIPT), "--voz", "--max", "3", "--linha-unica"],
                                   cwd=str(ROOT), timeout=120, check=False)
                except Exception as e:
                    log(f"manifestacao falhou: {e}")
                log("proxima manifestacao em %ds" % INTERVALO)
            else:
                log(f"fora da janela ({INICIO}h-{FIM}h); aguardando")
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        log("loop encerrado")


if __name__ == "__main__":
    main()
