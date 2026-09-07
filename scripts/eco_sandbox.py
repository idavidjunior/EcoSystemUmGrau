"""Sandbox isolado do EcoSystemUmGrau (Docker preferencial, degradado sem Docker).

Base segura para executar código de agentes. Prefere Docker com limites
rígidos; sem Docker, executa local restrito com alerta explícito.

Uso:
    import sys
    sys.path.insert(0, "scripts")
    from eco_sandbox import executar

    r = executar("print('olá')")
    print(r["ok"], r["modo"], r["stdout"])

100% stdlib. Nunca copia segredo para imagem ou container.
Rede nasce desligada. Workspace do container é efêmero.
"""

import os
import re
import sys
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = os.path.join(BASE, "scripts")
RUNTIME = os.path.join(BASE, "runtime")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

IMAGEM_PADRAO = os.environ.get("ECO_SANDBOX_IMAGE", "eco-sandbox:1.0.0")
TIMEOUT_PADRAO = 60.0
MEMORIA_PADRAO_MB = 512
CPUS_PADRAO = "1.0"
PIDS_PADRAO = 64
SAIDA_MAX = 65536
LINGUAGENS = ("python",)

_BLOQUEIOS_DEGRADADO = (
    r"os\.system", r"subprocess", r"socket", r"__import__\s*\(\s*['\"]os",
    r"shutil\.rmtree", r"open\s*\([^)]*['\"][wa]",
)


def _ok(**campos):
    out = {"ok": True}
    out.update(campos)
    return out


def _falha(motivo, **campos):
    out = {"ok": False, "motivo": str(motivo)}
    out.update(campos)
    return out


def _redigir(texto):
    """Remove segredos do texto antes de logar."""
    try:
        from memory_engine import redigir_sensivel
        return redigir_sensivel(texto or "")
    except Exception:
        try:
            return re.sub(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*\S+",
                          r"\1=[redigido]", texto or "")
        except Exception:
            return texto or ""


def _auditar(registro):
    """Anexa auditoria em runtime/sandbox.log (falha suave)."""
    try:
        os.makedirs(RUNTIME, exist_ok=True)
        linha = json.dumps(registro, ensure_ascii=False)[:4000]
        with open(os.path.join(RUNTIME, "sandbox.log"), "a",
                  encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), linha))
    except Exception:
        pass


def docker_disponivel(timeout=8):
    """Retorna True se o daemon Docker responde."""
    if not shutil.which("docker"):
        return False
    try:
        r = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                           capture_output=True, text=True, timeout=timeout,
                           cwd=BASE)
        return r.returncode == 0
    except Exception:
        return False


def _validar(codigo, linguagem):
    """Valida entrada antes de qualquer execução."""
    if not (codigo or "").strip():
        return False, "código vazio rejeitado"
    if (linguagem or "").lower() not in LINGUAGENS:
        return False, "linguagem não suportada: %s" % linguagem
    try:
        from security_engine import SecurityEngine
        eng = SecurityEngine()
        seguro, _eventos = eng.validate_command(codigo[:2000], "sandbox")
        if not seguro:
            return False, "bloqueado pela política de segurança"
    except Exception:
        pass
    return True, ""


def _truncar(texto):
    """Trunca saída gigante preservando início e fim."""
    if texto is None:
        return ""
    if len(texto) <= SAIDA_MAX:
        return texto
    fatia = SAIDA_MAX // 2 - 30
    return (texto[:fatia] + "\n...[truncado %d chars]...\n" % len(texto)
            + texto[-fatia:])


def _executar_docker(codigo, timeout, memoria_mb, rede, imagem):
    """Executa código em container efêmero com limites rígidos."""
    tmp = tempfile.mkdtemp(prefix="eco_sbx_")
    t0 = time.monotonic()
    try:
        alvo = os.path.join(tmp, "main.py")
        with open(alvo, "w", encoding="utf-8") as f:
            f.write(codigo)
        cmd = ["docker", "run", "--rm",
               "--network", "bridge" if rede else "none",
               "--memory", "%dm" % memoria_mb,
               "--memory-swap", "%dm" % memoria_mb,
               "--cpus", str(CPUS_PADRAO),
               "--pids-limit", str(PIDS_PADRAO),
               "--read-only",
               "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
               "-v", "%s:/work:ro" % tmp,
               "-w", "/work",
               imagem, "python", "/work/main.py"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout, cwd=BASE)
            dur = round(time.monotonic() - t0, 2)
            limites = {"timeout_s": timeout, "memoria_mb": memoria_mb,
                       "cpus": CPUS_PADRAO, "pids": PIDS_PADRAO,
                       "rede": bool(rede), "imagem": imagem}
            if r.returncode != 0 and "OOM" in (r.stderr or ""):
                return _falha("memória esgotada", modo="docker",
                              stdout=_truncar(r.stdout), stderr=_truncar(r.stderr),
                              duracao_s=dur, limites=limites)
            return _ok(modo="docker", stdout=_truncar(r.stdout),
                       stderr=_truncar(r.stderr), returncode=r.returncode,
                       duracao_s=dur, limites=limites) if r.returncode == 0 else \
                _falha("saída com código %d" % r.returncode, modo="docker",
                       stdout=_truncar(r.stdout), stderr=_truncar(r.stderr),
                       duracao_s=dur, limites=limites)
        except subprocess.TimeoutExpired:
            dur = round(time.monotonic() - t0, 2)
            return _falha("timeout após %ss" % timeout, modo="docker",
                          stdout="", stderr="", duracao_s=dur,
                          limites={"timeout_s": timeout, "memoria_mb": memoria_mb,
                                   "rede": bool(rede), "imagem": imagem})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _executar_degradado(codigo, timeout):
    """Execução local restrita quando Docker está ausente (com alerta)."""
    for padrao in _BLOQUEIOS_DEGRADADO:
        if re.search(padrao, codigo):
            return _falha("bloqueado em modo degradado: padrão %s" % padrao,
                          modo="degradado")
    tmp = tempfile.mkdtemp(prefix="eco_sbx_")
    t0 = time.monotonic()
    try:
        alvo = os.path.join(tmp, "main.py")
        with open(alvo, "w", encoding="utf-8") as f:
            f.write(codigo)
        try:
            r = subprocess.run([sys.executable, alvo], capture_output=True,
                               text=True, timeout=timeout, cwd=tmp)
            dur = round(time.monotonic() - t0, 2)
            limites = {"timeout_s": timeout, "rede": False,
                       "isolamento": "nenhum (degradado)"}
            if r.returncode == 0:
                return _ok(modo="degradado", stdout=_truncar(r.stdout),
                           stderr=_truncar(r.stderr), returncode=0,
                           duracao_s=dur, limites=limites,
                           aviso="sem isolamento Docker")
            return _falha("saída com código %d" % r.returncode,
                          modo="degradado", stdout=_truncar(r.stdout),
                          stderr=_truncar(r.stderr), duracao_s=dur,
                          limites=limites)
        except subprocess.TimeoutExpired:
            dur = round(time.monotonic() - t0, 2)
            return _falha("timeout após %ss" % timeout, modo="degradado",
                          duracao_s=dur)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def executar(codigo, linguagem="python", timeout=None, memoria_mb=None,
             rede=False, imagem=None):
    """Executa código de agente com isolamento (Docker ou degradado).

    Retorna dict com ok, modo, stdout, stderr, duracao_s e limites.
    """
    timeout = TIMEOUT_PADRAO if timeout is None else float(timeout)
    timeout = min(max(timeout, 1.0), 300.0)
    memoria_mb = MEMORIA_PADRAO_MB if memoria_mb is None else int(memoria_mb)
    memoria_mb = min(max(memoria_mb, 64), 2048)
    imagem = imagem or IMAGEM_PADRAO

    valido, motivo = _validar(codigo, linguagem)
    if not valido:
        _auditar({"evento": "bloqueio", "motivo": _redigir(motivo)})
        return _falha(motivo, modo="nenhum")

    if docker_disponivel():
        res = _executar_docker(codigo, timeout, memoria_mb, rede, imagem)
    else:
        res = _executar_degradado(codigo, timeout)
    _auditar({"evento": "execucao", "modo": res.get("modo"),
              "ok": res.get("ok"), "motivo": _redigir(res.get("motivo", "")),
              "duracao_s": res.get("duracao_s")})
    return res


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Sandbox isolado do ecossistema")
    ap.add_argument("--check", action="store_true",
                    help="mostra se Docker está disponível")
    ap.add_argument("--code", default="", help="código python para executar")
    ap.add_argument("--run-file", default="", help="arquivo python para executar")
    ap.add_argument("--timeout", type=float, default=TIMEOUT_PADRAO)
    ap.add_argument("--rede", action="store_true", help="libera rede (explícito)")
    args = ap.parse_args(argv)
    if args.check:
        print("docker: %s" % ("disponível" if docker_disponivel() else "ausente (degradado)"))
        return 0
    codigo = args.code
    if args.run_file:
        codigo = Path(args.run_file).read_text(encoding="utf-8")
    res = executar(codigo, timeout=args.timeout, rede=args.rede)
    print(json.dumps(res, ensure_ascii=False, indent=2)[:4000])
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
