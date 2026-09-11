#!/usr/bin/env python3
"""Ciclo 9 — build/run script reproduzível da trilha web.

Roda os testes de todos os labs de conhecimento/web/labs de forma
agregada e reporta STATUS, no mesmo padrão dos labs. Uso:

    python conhecimento/web/run_suite.py            # só os determinísticos
    python conhecimento/web/run_suite.py --tudo     # inclui IA/playwright

Método: cada lab roda no SEU diretório (imports relativos); o teste do
ciclo 6 exige o servidor de pé — o orquestrador sobe e derruba sozinho.
Exit code: 0 = todos os do escopo passaram; 1 = qualquer falha.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import time

_AQUI = os.path.dirname(os.path.abspath(__file__))
LABS = os.path.join(_AQUI, "labs")

# (pasta, arquivo de teste, exige servidor prévio, requer IA/playwright)
_CATALOGO = [
    ("ciclo-1-fundamentos", "test_server.py", False, False),
    ("ciclo-2-backend-estruturado", "test_server.py", False, False),
    ("ciclo-3-websocket", "test_ws.py", False, False),
    ("ciclo-5-persistencia-web", "test_persistencia.py", False, False),
    ("ciclo-6-seguranca-owasp", "test_seguranca.py", True, False),
    ("ciclo-4-ia-chat", "test_ia_chat.py", False, True),
    ("ciclo-7-performance-acessibilidade", "test_performance.py", False, True),
    ("ciclo-8-produto-quadro-notas", "test_produto.py", False, True),
]

_TIMEOUT_S = 120
_PORTA_CICLO6 = 8096


def _porta_livre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _espera_health(porta, segundos=15):
    import urllib.request
    fim = time.time() + segundos
    while time.time() < fim:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{porta}/api/health", timeout=2
            ) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def _sobe_servidor(func):
    """Sobe servidor do lab, espera health e devolve o processo."""
    proc = subprocess.Popen(
        [sys.executable, "server.py", str(_PORTA_CICLO6)],
        cwd=func["dir"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not _espera_health(_PORTA_CICLO6):
        proc.terminate()
        return None
    return proc


def _executa(func, todo):
    """Executa um lab e retorna (ok: bool, detalhe: str)."""
    test = os.path.join(func["dir"], func["test"])
    if not os.path.isfile(test):
        return False, f"teste ausente: {func['test']}"
    if func["ia"] and not todo:
        return True, "SKIP (IA/playwright) — rode com --tudo"

    proc = None
    if func["server"]:
        proc = _sobe_servidor(func)
        if proc is None:
            return False, f"servidor não subiu ({func['nome']}, health timeout)"
    try:
        resultado = subprocess.run(
            [sys.executable, func["test"]],
            cwd=func["dir"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_S,
        )
        saida = resultado.stdout + resultado.stderr
        ok = resultado.returncode == 0
        return ok, saida
    except subprocess.TimeoutExpired:
        return False, f"timeout ({_TIMEOUT_S}s)"
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


def main():
    todo = "--tudo" in sys.argv
    catalogo = [_C for _C in _CATALOGO if todo or not _C[3]]
    total = {"ok": 0, "fail": 0, "skip": 0}
    detalhes = {}

    print("=" * 60)
    print("  RUN SUITE WEB — build/run reproduzível (Ciclo 9)")
    print(f"  escopo: {'tudo (IA+playwright)' if todo else 'determinístico'}")
    print("=" * 60)

    for nome, teste, server, ia in catalogo:
        print(f"\n[{nome}]")
        func = {"nome": nome, "dir": os.path.join(LABS, nome), "test": teste,
                "server": server, "ia": ia}
        ok, saida = _executa(func, todo)
        linha_resumo = None
        for lin in saida.splitlines():
            if "STATUS:" in lin:
                linha_resumo = lin.strip()
                break
        if ok and "SKIP" in saida[:12]:
            total["skip"] += 1
            print(f"  → SKIP")
            continue
        if ok:
            total["ok"] += 1
            print(f"  → PASS  {linha_resumo or ''}")
        else:
            total["fail"] += 1
            print(f"  → FAIL  {linha_resumo or ''}")
            detalhes[nome] = saida

    print("\n" + "=" * 60)
    print(f"  STATUS: OK ({total['ok']} labs aprovados, "
          f"{total['fail']} falhas, {total['skip']} skips)")
    print("=" * 60)

    for nome, saida in detalhes.items():
        print(f"\n--- saída de {nome} (fail) ---")
        print(saida[-3000:])

    # Evidência JSON (mesmo padrão dos benchmarks dos labs).
    evidencia = os.path.join(_AQUI, "benchmarks", "ciclo-9-run-suite.json")
    os.makedirs(os.path.dirname(evidencia), exist_ok=True)
    payload = {
        "ciclo": 9,
        "escopo": "tudo" if todo else "deterministico",
        "data_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "labs_ok": total["ok"],
        "labs_fail": total["fail"],
        "labs_skip": total["skip"],
        "status": "OK" if total["fail"] == 0 else "FALHA",
    }
    with open(evidencia, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return 0 if total["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())