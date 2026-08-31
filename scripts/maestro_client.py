"""maestro_client.py — Helper para componentes consultarem o Maestro.

Uso:
    from maestro_client import consultar_maestro, fallback_degraded

    decisao = consultar_maestro("pode_iniciar", script="tts_service.py")
    if not decisao and not fallback_degraded("guardian"):
        return False  # maestro mandou esperar
    # ... faz a acao ...
"""
import json
import os
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
CMD_FILE = RUNTIME / "maestro_cmd.json"

# Timeout pra aguardar resposta do maestro
TIMEOUT_S = 1.5
# Se maestro nao responder em ate este tempo, modo degraded
DEGRADED_TIMEOUT_S = 5.0


def consultar_maestro(cmd: str, **kwargs) -> dict:
    """Envia comando ao maestro e aguarda resposta.

    Args:
        cmd: acao ("pode_iniciar", "registrar", "heartbeat", "parar", etc)
        **kwargs: campos extras (script, pid, owner)

    Returns:
        dict da resposta do maestro, ou {"status": "offline"} se nao respondeu.
    """
    # PRIMEIRO: verifica se maestro esta vivo. Sem isso, resposta cacheada
    # antiga do maestro anterior poderia ser lida como se fosse atual.
    if not maestro_disponivel():
        return {"status": "offline", "motivo": "maestro_nao_esta_rodando"}

    req_id = str(uuid.uuid4())[:8]
    payload = {"cmd": cmd, "request_id": req_id, **kwargs}

    # Limpa resposta antiga deste mesmo req_id (se sobrou de chamada anterior)
    resp_file = RUNTIME / f"maestro_resp_{req_id}.json"
    resp_file.unlink(missing_ok=True)

    # Estrategia: arquivo unico por request, evita race com o maestro
    # deletando o cmd global. Maestro procura em maestro_cmd.json e em
    # maestro_cmd_<id>.json (fallback).
    cmd_file_req = RUNTIME / f"maestro_cmd_{req_id}.json"
    tmp = cmd_file_req.with_suffix(".tmp")
    # Retry ate 3x pra evitar WinError 32 (arquivo em uso)
    escrito = False
    for tentativa in range(3):
        try:
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, cmd_file_req)
            escrito = True
            break
        except OSError:
            time.sleep(0.05)
    if not escrito:
        return {"status": "offline", "motivo": "falha_escrita_cmd"}

    # Tambem tenta no arquivo global (compatibilidade)
    try:
        tmp2 = CMD_FILE.with_suffix(".tmp")
        tmp2.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp2, CMD_FILE)
    except OSError:
        pass  # nao bloqueia se o global falhar

    # Aguarda resposta
    t0 = time.time()
    while time.time() - t0 < TIMEOUT_S:
        if resp_file.exists():
            try:
                # Verifica novamente se maestro ainda esta vivo antes de ler
                if not maestro_disponivel():
                    resp_file.unlink(missing_ok=True)
                    cmd_file_req.unlink(missing_ok=True)
                    return {"status": "offline", "motivo": "maestro_caiu_durante_consulta"}
                resp = json.loads(resp_file.read_text(encoding="utf-8"))
                resp_file.unlink(missing_ok=True)
                cmd_file_req.unlink(missing_ok=True)
                return resp
            except Exception:
                pass
        time.sleep(0.05)
    cmd_file_req.unlink(missing_ok=True)
    return {"status": "offline", "motivo": "timeout"}


def maestro_disponivel() -> bool:
    """Checa se o maestro esta vivo (PID file existe e processo existe)."""
    pid_file = RUNTIME / "maestro.pid"
    if not pid_file.exists():
        return False
    try:
        import psutil
        pid = int(pid_file.read_text().strip())
        return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except Exception:
        return False


def fallback_degraded(owner: str, motivo: str = "") -> bool:
    """Chamado quando o maestro nao respondeu. Retorna True (permite + alerta).

    Args:
        owner: quem esta pedindo (guardian, widget, bridge, etc)
        motivo: o que tentou fazer

    Returns:
        sempre True na fase 1. Caller deve agir normalmente mas logar alerta.
    """
    log_file = RUNTIME / "maestro.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] [ALERTA] "
                f"[MAESTRO_OFFLINE] {owner} agiu sem maestro. motivo={motivo}\n"
            )
    except Exception:
        pass
    return True
