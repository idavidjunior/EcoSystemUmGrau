"""Loop periódico da agenda — chama executar_vencidas a cada minuto.

Roda em background e registra prova de vida para o watchdog.
Janela de tick: 60 segundos (padrão do vigilante para projetos).

Variáveis de ambiente:
  AGENDA_INTERVALO  segundos entre ticks (padrão 60)
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

INTERVALO = int(os.environ.get("AGENDA_INTERVALO", "60"))

LOG = ROOT / "runtime" / "agenda_tick.log"


def log(msg):
    linha = "[%s] %s" % (datetime.now().isoformat(timespec="seconds"), msg)
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def main():
    from eco_agenda import executar_vencidas, watchdog
    log("tick loop iniciado (intervalo=%ds)" % INTERVALO)
    try:
        while True:
            try:
                res = executar_vencidas()
                feitas = res.get("executadas", []) if res.get("ok") else []
                if feitas:
                    log("tick: %d executada(s)" % len(feitas))
                alerta = watchdog(janela_s=max(INTERVALO * 5, 300))
                if alerta.get("alerta"):
                    log("watchdog: %s" % alerta.get("motivo"))
            except Exception as e:
                log("tick falhou: %s" % e)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        log("tick loop encerrado")


if __name__ == "__main__":
    main()
