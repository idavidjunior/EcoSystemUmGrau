#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime_maestro.py — ÚNICO chefe de processos do EcoSystemUmGrau.

Fase 1 (observador): detecta, registra e compara decisões.
NÃO bloqueia nenhum componente. Após validação (1-3 dias), vira fase 2 (ativo).

Comunicação: arquivo de comando (runtime/maestro_cmd.json) mesmo padrão
do tts_cmd.json. Componentes escrevem, maestro lê e responde em
runtime/maestro_resp_<request_id>.json.

Comandos suportados:
  pode_iniciar       script=X     -> pode? True/False + motivo
  registrar          script=X pid=Y owner=Z  -> adiciona ao livro
  heartbeat          script=X pid=Y          -> atualiza timestamp
  parar              script=X                -> marca como morto
  matar_duplicatas   script=X                -> quantos matou
  listar_vivos       -                        -> inventario

Livro de estado: runtime/maestro_estado.json (inventário único).

Uso direto (CLI para testes):
    python scripts/runtime_maestro.py status
    python scripts/runtime_maestro.py listar
    python scripts/runtime_maestro.py pode_iniciar tts_service.py
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
CMD_FILE = RUNTIME / "maestro_cmd.json"
ESTADO_FILE = RUNTIME / "maestro_estado.json"
LOG_FILE = RUNTIME / "maestro.log"
PID_FILE = RUNTIME / "maestro.pid"

# Singleton deste proprio maestro
_MAESTRO_PID = None

# Cooldown padrao entre restarts do mesmo script (segundos)
COOLDOWN_S = 15

# Timeout de leitura de comando (loop daemon)
LOOP_INTERVAL_S = 0.3

# Scripts que o maestro conhece (singleton scripts do ecossistema)
SCRIPTS_CONHECIDOS = frozenset({
    "widget_edge.py",
    "tts_service.py",
    "dialogo.py",
    "system_guardian.py",
    "jarvis_bridge.py",
})


def _log(msg, level="INFO"):
    """Log estruturado no arquivo maestro.log."""
    try:
        linha = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] [{level}] {msg}"
        print(linha, flush=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def _atomic_write(path: Path, data: dict):
    """Escrita atomica (tmp + replace) para evitar corrupcao."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        os.replace(tmp, path)


def _read_estado():
    """Le livro de estado. Se corrompido, retorna vazio."""
    if not ESTADO_FILE.exists():
        return {"servicos": {}, "cooldowns": {}, "owner_atual": {}}
    try:
        return json.loads(ESTADO_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"servicos": {}, "cooldowns": {}, "owner_atual": {}}


def _save_estado(estado):
    """Persiste livro de estado."""
    _atomic_write(ESTADO_FILE, estado)


def _limpar_cooldowns_vencidos(estado):
    """Remove entradas de cooldown ja vencidas (limpeza periodica)."""
    agora = time.time()
    vencidos = [
        s for s, ts in estado.get("cooldowns", {}).items()
        if agora - ts > COOLDOWN_S * 10
    ]
    for s in vencidos:
        estado["cooldowns"].pop(s, None)


def pode_iniciar(script: str) -> dict:
    """Decide se um script pode ser iniciado agora.

    Retorna dict {pode: bool, motivo: str}. NAO bloqueia nada na fase 1:
    o caller decide se obedece ou so registra.
    """
    estado = _read_estado()
    _limpar_cooldowns_vencidos(estado)
    servicos = estado.get("servicos", {})
    cooldowns = estado.get("cooldowns", {})

    # Singleton: ja existe vivo?
    for s, info in servicos.items():
        if s == script and info.get("vivo"):
            pid = info.get("pid")
            return {
                "pode": False,
                "motivo": f"ja_vivo (pid={pid}, owner={info.get('owner','?')})",
            }

    # Cooldown: foi reiniciado muito recentemente?
    ultimo = cooldowns.get(script, 0)
    if time.time() - ultimo < COOLDOWN_S:
        return {
            "pode": False,
            "motivo": f"cooldown (faz {time.time() - ultimo:.0f}s, precisa {COOLDOWN_S}s)",
        }

    return {"pode": True, "motivo": "ok"}


def registrar(script: str, pid: int, owner: str = "?") -> dict:
    """Adiciona servico ao livro de estado."""
    if script not in SCRIPTS_CONHECIDOS:
        _log(f"registrar: script desconhecido '{script}'", "WARN")
    estado = _read_estado()
    estado["servicos"][script] = {
        "pid": pid,
        "owner": owner,
        "vivo": True,
        "started_at": time.time(),
        "last_heartbeat": time.time(),
    }
    estado["cooldowns"][script] = time.time()
    estado["owner_atual"][script] = owner
    _save_estado(estado)
    _log(f"registrar: {script} pid={pid} owner={owner}")
    return {"status": "ok"}


def heartbeat(script: str, pid: int) -> dict:
    """Atualiza last_heartbeat de um servico."""
    estado = _read_estado()
    info = estado.get("servicos", {}).get(script)
    if not info or info.get("pid") != pid:
        return {"status": "nao_encontrado"}
    info["last_heartbeat"] = time.time()
    estado["servicos"][script] = info
    _save_estado(estado)
    return {"status": "ok"}


def parar(script: str) -> dict:
    """Marca servico como morto no livro."""
    estado = _read_estado()
    info = estado.get("servicos", {}).get(script)
    if info:
        info["vivo"] = False
        info["parado_em"] = time.time()
        estado["servicos"][script] = info
        _save_estado(estado)
        _log(f"parar: {script} marcado como morto")
        return {"status": "ok"}
    return {"status": "nao_encontrado"}


def listar_vivos() -> dict:
    """Retorna inventario completo."""
    estado = _read_estado()
    vivos = {
        s: info for s, info in estado.get("servicos", {}).items()
        if info.get("vivo")
    }
    return {"vivos": vivos, "total": len(vivos)}


def matar_duplicatas(script: str) -> dict:
    """Detecta PIDs duplicados do mesmo script via psutil.

    Retorna quantos matou. NAO bloqueia componentes: e o maestro
    chamando o anti-orfao por sua conta.
    """
    import psutil
    pids_do_script = []
    for p in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            cmd = " ".join(p.info["cmdline"] or [])
            if script in cmd and (p.info["name"] or "").lower() == "python.exe":
                pids_do_script.append((p.info["create_time"], p.info["pid"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if len(pids_do_script) <= 1:
        return {"mortos": 0, "mantido": pids_do_script[0][1] if pids_do_script else None}

    pids_do_script.sort()
    dono = pids_do_script[0][1]
    orfaos = [pid for _, pid in pids_do_script[1:]]

    mortos = 0
    for pid in orfaos:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
            mortos += 1
            _log(f"matar_duplicatas: {script} pid={pid} morto (dono={dono})")
        except Exception as e:
            _log(f"matar_duplicatas: erro matando {pid}: {e}", "ERROR")

    return {"mortos": mortos, "mantido": dono}


def processar_comando(cmd: dict) -> dict:
    """Processa um comando e retorna resposta."""
    acao = cmd.get("cmd", "")
    try:
        if acao == "pode_iniciar":
            script = cmd.get("script", "")
            return pode_iniciar(script)
        if acao == "registrar":
            script = cmd.get("script", "")
            pid = int(cmd.get("pid", 0))
            owner = cmd.get("owner", "?")
            return registrar(script, pid, owner)
        if acao == "heartbeat":
            script = cmd.get("script", "")
            pid = int(cmd.get("pid", 0))
            return heartbeat(script, pid)
        if acao == "parar":
            return parar(cmd.get("script", ""))
        if acao == "listar_vivos":
            return listar_vivos()
        if acao == "matar_duplicatas":
            return matar_duplicatas(cmd.get("script", ""))
        return {"status": "erro", "motivo": f"cmd desconhecido: {acao}"}
    except Exception as e:
        return {"status": "erro", "motivo": str(e)[:200]}


def _write_resp(req_id: str, resposta: dict):
    """Escreve resposta em maestro_resp_<req_id>.json."""
    if not req_id:
        return
    resp_file = RUNTIME / f"maestro_resp_{req_id}.json"
    _atomic_write(resp_file, resposta)
    try:
        resp_file.unlink()  # Limpa apos escrever (caller ja leu?)
    except Exception:
        pass


def _limpar_resp_antigas(max_age_sec: int = 600):
    """Remove arquivos de resposta com mais de 10 min."""
    try:
        agora = time.time()
        for f in RUNTIME.glob("maestro_resp_*.json"):
            try:
                if agora - f.stat().st_mtime > max_age_sec:
                    f.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass


def daemon_loop():
    """Loop principal: le comandos do disco e responde."""
    global _MAESTRO_PID
    _MAESTRO_PID = os.getpid()
    PID_FILE.write_text(str(_MAESTRO_PID), encoding="utf-8")
    _log(f"maestro iniciado pid={_MAESTRO_PID} fase=observador")
    last_mtime = 0
    last_cleanup = 0
    try:
        while True:
            try:
                # Cleanup periodico de respostas
                if time.time() - last_cleanup > 60:
                    _limpar_resp_antigas()
                    last_cleanup = time.time()

                if CMD_FILE.exists():
                    mtime = CMD_FILE.stat().st_mtime
                    if mtime != last_mtime:
                        last_mtime = mtime
                        try:
                            cmd = json.loads(CMD_FILE.read_text(encoding="utf-8-sig"))
                            CMD_FILE.unlink(missing_ok=True)
                            req_id = cmd.get("request_id", str(uuid.uuid4())[:8])
                            resp = processar_comando(cmd)
                            _write_resp(req_id, resp)
                            _log(f"cmd={cmd.get('cmd')} script={cmd.get('script','-')} resp={resp}")
                        except Exception as e:
                            _log(f"erro processando comando: {e}", "ERROR")
            except KeyboardInterrupt:
                _log("encerrando por KeyboardInterrupt")
                break
            except Exception as e:
                _log(f"erro loop: {e}", "ERROR")
            time.sleep(LOOP_INTERVAL_S)
    finally:
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        _log("maestro encerrado")


def cmd_status():
    """Imprime estado atual para o CLI."""
    estado = _read_estado()
    print("=== MAESTRO STATUS ===")
    print(f"Estado arquivo: {ESTADO_FILE}")
    print(f"PID arquivo: {PID_FILE}")
    if PID_FILE.exists():
        print(f"  PID vivo: {PID_FILE.read_text().strip()}")
    print(f"Log: {LOG_FILE}")
    print()
    print("Servicos conhecidos:", ", ".join(sorted(SCRIPTS_CONHECIDOS)))
    print()
    print("Livro de estado:")
    for s, info in estado.get("servicos", {}).items():
        vivo = "VIVO" if info.get("vivo") else "MORTO"
        print(f"  [{vivo}] {s}: pid={info.get('pid')} owner={info.get('owner')}")


def main():
    """CLI: status / loop / comandos diretos."""
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "loop":
        daemon_loop()
    elif cmd == "status":
        cmd_status()
    elif cmd == "pode_iniciar":
        script = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(pode_iniciar(script), indent=2, ensure_ascii=False))
    elif cmd == "listar":
        print(json.dumps(listar_vivos(), indent=2, ensure_ascii=False))
    elif cmd == "matar_duplicatas":
        script = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(matar_duplicatas(script), indent=2, ensure_ascii=False))
    elif cmd == "registrar":
        # registrar <script> <pid> <owner>
        if len(sys.argv) < 4:
            print("uso: registrar <script> <pid> <owner>")
            return 1
        print(json.dumps(registrar(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "?")))
    else:
        print(f"comando desconhecido: {cmd}")
        print("uso: runtime_maestro.py [status|loop|listar|pode_iniciar <script>|matar_duplicatas <script>|registrar <script> <pid> <owner>]")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
