"""Emissor de atividade real do Jarvis para o Cerebro Vivo.

Cada estado operacional escreve runtime/atividade/<tipo>.json com escrita
atomica (tmp + os.replace). O widget le a pasta periodicamente e expira
atividades por TTL; intensidade 0 encerra a atividade na hora.
Tipos em uso: fala, memoria, busca, ferramenta, resposta.
"""
import json
import os
import time
from pathlib import Path

_DIR = Path(__file__).resolve().parent.parent / "runtime" / "atividade"


def emitir(tipo, intensidade=1.0):
    """Registra estado de atividade. intensidade 0 = terminou agora."""
    try:
        _DIR.mkdir(parents=True, exist_ok=True)
        tmp = _DIR / f"{tipo}.tmp"
        tmp.write_text(json.dumps(
            {"quando": time.time(), "intensidade": float(intensidade)}),
            encoding="utf-8")
        os.replace(tmp, _DIR / f"{tipo}.json")
    except Exception:
        pass
