#!/usr/bin/env python3
"""eco_widget.py — Coordenador simples do EcoSystemUmGrau.

Funções principais:
- activate(): seta estado ativo + flag para o bridge
- deactivate(): seta estado inativo + remove flag
- status(): retorna estado atual

O controle visual real do widget (mostrar/esconder, botões) é feito
pelo unified_bridge.py via seu próprio webview + poller JS.
Este módulo apenas coordena o estado de narração.
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
NARRACAO_FILE = RUNTIME / "narracao_estado.json"
BRIDGE_FLAG = RUNTIME / "bridge_enabled.flag"

PYTHON = sys.executable


def _atomic_write(path: Path, data: dict):
    """Escrita atômica: tmp + replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        import os
        os.replace(tmp, path)


# --- Estado de narração ---

def activate() -> dict:
    """Ativa Eco: seta estado ativo e flag para o bridge controlar o widget."""
    _atomic_write(NARRACAO_FILE, {"ativo": True, "pausado": False})
    _atomic_write(BRIDGE_FLAG, {"ativo": True, "timestamp": int(time.time())})
    return {"ok": True, "widget_visivel": True, "bridge_up": True, "narrador_ativo": True, "mensagem": "Eco ativado"}


def deactivate() -> dict:
    """Desativa Eco: seta estado inativo e remove flag."""
    try:
        BRIDGE_FLAG.unlink(missing_ok=True)
    except Exception:
        pass
    _atomic_write(NARRACAO_FILE, {"ativo": False, "pausado": True})
    return {"ok": True, "widget_visivel": False, "bridge_up": True, "narrador_ativo": False, "mensagem": "Eco desativado"}


def status() -> dict:
    """Retorna status do widget e bridge."""
    # Ler estado de narracao
    try:
        with open(NARRACAO_FILE, encoding="utf-8") as f:
            estado = json.loads(f.read())
        narrador_ativo = bool(estado.get("ativo", False))
    except Exception:
        narrador_ativo = False

    # Verificar flag do bridge
    bridge_ativo = BRIDGE_FLAG.exists()
    try:
        if BRIDGE_FLAG.exists():
            with open(BRIDGE_FLAG, encoding="utf-8") as f:
                d = json.loads(f.read())
            bridge_ativo = bool(d.get("ativo", False))
    except Exception:
        bridge_ativo = False

    return {
        "ok": True,
        "widget_visivel": bridge_ativo,
        "bridge_up": True,
        "narrador_ativo": narrador_ativo,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("acao", choices=["ativar", "desativar", "status"])
    args = parser.parse_args()

    if args.acao == "ativar":
        r = activate()
        print("Ativar:", r)
    elif args.acao == "desativar":
        r = deactivate()
        print("Desativar:", r)
    elif args.acao == "status":
        r = status()
        print("Status:", r)