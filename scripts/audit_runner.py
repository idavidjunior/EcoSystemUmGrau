#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_runner.py — Runner permanente de auditoria.

Executa audit_eco.py de forma protegida (não morre no RAM cleanup),
escreve resultado atomicamente em runtime/audit_result.json.
O system_guardian lê esse arquivo em vez de rodar subprocesso.
"""
import json
import os
import sys
import time
try:
    import fcntl
except ImportError:
    fcntl = None
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
RUNTIME = ROOT / "runtime"
RESULT_FILE = RUNTIME / "audit_result.json"
LOCK_FILE = RUNTIME / "audit_runner.lock"

# Proteção contra múltiplas instâncias (Windows usa lock file simples)
lock_acquired = False
try:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    if fcntl:
        lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_acquired = True
    else:
        # Windows: usa arquivo de lock exclusivo
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            lock_acquired = True
        except FileExistsError:
            pass
except (IOError, OSError):
    pass

if not lock_acquired:
    print("Outro audit_runner já rodando", file=sys.stderr)
    sys.exit(0)

# Baixa prioridade para não competir por RAM
try:
    import psutil
    p = psutil.Process(os.getpid())
    p.nice(psutil.IDLE_PRIORITY_CLASS if os.name == "nt" else 19)
except Exception:
    pass

sys.path.insert(0, str(SCRIPTS))
from audit_eco import run_audit, print_report
from audit_eco import Severity

RUNTIME.mkdir(parents=True, exist_ok=True)

def atomic_write(path: Path, data: dict):
    """Escrita atômica: tmp + replace."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        import os as _os
        _os.replace(tmp, path)

def main():
    print(f"[audit_runner] Iniciando auditoria...", flush=True)
    start = time.time()
    
    try:
        # Executa auditoria
        report = run_audit(quick=False)
        
        # Prepara resultado
        findings = []
        for f in report.findings:
            findings.append({
                "category": f.category,
                "check": f.check,
                "severity": f.severity.name.lower(),
                "message": f.message,
                "fix": f.fix,
                "file": str(f.file) if f.file else None
            })
        
        result = {
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "score": report.score,
            "findings": findings,
            "duration_sec": round(time.time() - start, 2)
        }
        
        # Escrita atômica
        atomic_write(RESULT_FILE, result)
        
        print(f"[audit_runner] Concluído em {result['duration_sec']}s - Score: {report.score}/100", flush=True)
        
    except Exception as e:
        error_result = {
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "error": str(e),
            "score": 0,
            "findings": [{
                "category": "Auditoria",
                "check": "Execução",
                "severity": "error",
                "message": f"Auditoria falhou: {e}",
                "fix": None,
                "file": None
            }],
            "duration_sec": round(time.time() - start, 2)
        }
        atomic_write(RESULT_FILE, error_result)
        print(f"[audit_runner] ERRO: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()