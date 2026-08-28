#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_runner.py — Produtor do resultado periódico de auditoria do ecossistema.

O System Guardian (scripts/system_guardian.py) executa este script a cada
~30 minutos em processo separado e depois lê runtime/audit_result.json para
reportar erros/warnings no log. Sem este script, o resultado fica antigo e o
guardian registra "AUDIT: resultado antigo" indefinidamente.

Formato do resultado (contrato com system_guardian.run_audit_periodico):
    timestamp     float  epoch seconds (usado no cálculo de idade)
    iso_timestamp str    legível, mesma data
    score         int    0-100
    findings      list   [{category, check, severity, message, fix, file}]
    duration_sec  float

A auditoria em si vem de audit_eco.run_audit() (fonte única).
"""
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RESULT_FILE = BASE / "runtime" / "audit_result.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from audit_eco import Severity, run_audit
except Exception as exc:
    payload = {
        "timestamp": time.time(),
        "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "score": 0,
        "findings": [{
            "category": "Runner",
            "check": "import audit_eco",
            "severity": "error",
            "message": f"Falha ao importar audit_eco: {exc}",
            "fix": None,
            "file": None,
        }],
        "duration_sec": 0.0,
    }
    _atomic_write(payload)
    sys.exit(1)


def _atomic_write(payload: dict) -> None:
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = RESULT_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, RESULT_FILE)


def main() -> int:
    start = time.time()
    try:
        report = run_audit(quick=False)
    except Exception as exc:
        payload = {
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "score": 0,
            "findings": [{
                "category": "Runner",
                "check": "run_audit",
                "severity": "error",
                "message": f"Falha na auditoria: {exc}",
                "fix": None,
                "file": None,
            }],
            "duration_sec": round(time.time() - start, 2),
        }
        _atomic_write(payload)
        return 1

    payload = {
        "timestamp": time.time(),
        "iso_timestamp": report.timestamp,
        "score": report.score,
        "findings": [
            {
                "category": f.category,
                "check": f.check,
                "severity": f.severity.value,
                "message": f.message,
                "fix": f.fix,
                "file": f.file,
            }
            for f in report.findings
        ],
        "duration_sec": round(time.time() - start, 2),
    }
    _atomic_write(payload)

    errors = sum(1 for f in payload["findings"] if f["severity"] == Severity.ERROR.value)
    warns = sum(1 for f in payload["findings"] if f["severity"] == Severity.WARN.value)
    print(f"AUDIT: score={report.score}/100, {errors} erros, {warns} warnings, "
          f"duracao {payload['duration_sec']}s -> {RESULT_FILE.name}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())