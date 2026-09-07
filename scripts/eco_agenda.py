"""Tarefas agendadas do EcoSystemUmGrau — extensão do runtime_state.

Agenda ações na hora certa com auditoria, sem travar o ecossistema.
Tick idempotente: pode rodar a cada minuto sem duplicar execução.

Uso:
    import sys
    sys.path.insert(0, "scripts")
    from eco_agenda import agendar, listar, executar_vencidas

    agendar("nota diária", "nota", {"texto": "revisar pendências"},
            recorrencia="janela", hora="09:00")
    print(executar_vencidas())

100% stdlib. Sem shell arbitrário: só ações permitidas.
Nunca faz commit ou push (exclusivo do gate de persistência).
"""

import os
import re
import sys
import json
import subprocess
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = os.path.join(BASE, "scripts")
RUNTIME = os.path.join(BASE, "runtime")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

LOCK = os.path.join(RUNTIME, "agenda.lock")
LOG = os.path.join(RUNTIME, "agenda.log")
HEARTBEAT = os.path.join(RUNTIME, "agenda_heartbeat.json")
TIMEOUT_PADRAO = 120.0
MAX_TENTATIVAS = 3
BACKOFF_BASE_S = 60
BACKOFF_TETO_S = 3600
ORFAO_LIMITE_S = 600
TRANSITORIOS = ("timeout",)
ESTADOS = ("pending", "running", "success", "failed")

ACOES = ("nota", "checkpoint", "pendencia", "script")
CHAVES_ESTADO = ("active_project", "objective", "last_task",
                 "operational_context")


def _ok(**campos):
    out = {"ok": True}
    out.update(campos)
    return out


def _falha(motivo, **campos):
    out = {"ok": False, "motivo": str(motivo)}
    out.update(campos)
    return out


def _agora():
    return datetime.now()


def _iso(dt):
    return dt.isoformat(timespec="seconds")


def _parse_iso(valor):
    try:
        return datetime.fromisoformat(valor)
    except Exception:
        return None


def _auditar(registro):
    try:
        os.makedirs(RUNTIME, exist_ok=True)
        linha = json.dumps(registro, ensure_ascii=False)[:3000]
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (_iso(_agora()), linha))
    except Exception:
        pass


def _carregar():
    """Carrega estado migrando agenda e tarefas antigas."""
    from runtime_state import load_state, save_state
    estado = load_state()
    migrou = False
    if not isinstance(estado.get("agendadas"), list):
        estado["agendadas"] = []
        migrou = True
    for t in estado["agendadas"]:
        if not isinstance(t, dict):
            continue
        if t.get("estado") not in ESTADOS:
            t["estado"] = "pending"
            migrou = True
        for campo, padrao in (("tentativa", 0), ("max_tentativas", MAX_TENTATIVAS),
                              ("dispatch_id", ""), ("ultimo_motivo", ""),
                              ("running_inicio", "")):
            if campo not in t:
                t[campo] = padrao
                migrou = True
        if not isinstance(t.get("disparos"), list):
            t["disparos"] = []
            migrou = True
    if migrou:
        try:
            save_state(estado)
        except Exception:
            pass
    return estado


def _salvar(estado):
    from runtime_state import save_state
    save_state(estado)


def _proxima(recorrencia, ref=None, intervalo_s=0, hora=""):
    """Calcula a próxima execução a partir da referência."""
    ref = ref or _agora()
    if recorrencia == "intervalo":
        intervalo_s = max(int(intervalo_s or 0), 60)
        return _iso(ref + timedelta(seconds=intervalo_s))
    if recorrencia == "janela":
        m = re.match(r"^(\d{1,2}):(\d{2})$", (hora or "").strip())
        if not m:
            return ""
        h = int(m.group(1))
        mi = int(m.group(2))
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            return ""
        alvo = ref.replace(hour=h, minute=mi, second=0, microsecond=0)
        if alvo <= ref:
            alvo = alvo + timedelta(days=1)
        return _iso(alvo)
    return ""


def _caminho_seguro(alvo):
    """Normaliza script e garante contenção na raiz do repo."""
    alvo = (alvo or "").replace("\\", "/").strip()
    if not alvo.endswith(".py") or not alvo or ".." in alvo.split("/"):
        return False, "script fora do repo ou inexistente"
    base_real = os.path.realpath(BASE)
    caminho = os.path.realpath(os.path.join(base_real, alvo.lstrip("/")))
    try:
        dentro = os.path.commonpath([base_real, caminho]) == base_real
    except ValueError:
        dentro = False
    if not dentro or not os.path.isfile(caminho):
        return False, "script fora do repo ou inexistente"
    return True, caminho


def _e_transitoria(motivo):
    texto = (motivo or "").lower()
    return any(m in texto for m in TRANSITORIOS)


def _backoff(tentativa):
    espera = BACKOFF_BASE_S * (2 ** max(int(tentativa) - 1, 0))
    return min(espera, BACKOFF_TETO_S)


def agendar(nome, acao, params=None, recorrencia="once", em="",
            intervalo_s=0, hora="", ativa=True):
    """Agenda tarefa e retorna dict com a tarefa criada."""
    params = params or {}
    if not (nome or "").strip():
        return _falha("nome vazio rejeitado")
    if acao not in ACOES:
        return _falha("ação desconhecida: %s" % acao)
    if recorrencia not in ("once", "intervalo", "janela"):
        return _falha("recorrência desconhecida: %s" % recorrencia)
    agora = _agora()
    if recorrencia == "once":
        dt = _parse_iso(em or "")
        if not dt:
            return _falha("horário inválido para execução única (ISO)")
        proxima = _iso(dt)
    elif recorrencia == "intervalo":
        try:
            intervalo_s = int(intervalo_s)
        except Exception:
            return _falha("intervalo inválido (segundos)")
        if intervalo_s < 60:
            return _falha("intervalo mínimo é 60 segundos")
        proxima = _iso(agora + timedelta(seconds=intervalo_s))
    else:
        proxima = _proxima("janela", ref=agora, hora=hora)
        if not proxima:
            return _falha("hora inválida para janela (HH:MM)")
    if acao == "script":
        alvo = str((params or {}).get("script", ""))
        ok_caminho, _ = _caminho_seguro(alvo)
        if not ok_caminho:
            return _falha("script fora do repo ou inexistente")
    estado = _carregar()
    nid = max([t.get("id", 0) for t in estado["agendadas"]], default=0) + 1
    tarefa = {"id": nid, "nome": nome, "acao": acao, "params": params,
              "recorrencia": recorrencia, "intervalo_s": int(intervalo_s or 0),
              "hora": hora, "proxima": proxima, "ultima": None,
              "ativa": bool(ativa), "criada": _iso(agora),
              "estado": "pending", "tentativa": 0,
              "max_tentativas": MAX_TENTATIVAS, "dispatch_id": "",
              "ultimo_motivo": "", "running_inicio": "", "disparos": []}
    estado["agendadas"].append(tarefa)
    _salvar(estado)
    _auditar({"evento": "agendada", "id": nid, "nome": nome, "acao": acao,
              "proxima": proxima})
    return _ok(tarefa=tarefa)


def listar(somente_ativas=False):
    """Lista tarefas agendadas do estado."""
    try:
        estado = _carregar()
        tarefas = estado.get("agendadas") or []
        if somente_ativas:
            tarefas = [t for t in tarefas if t.get("ativa")]
        return _ok(tarefas=tarefas)
    except Exception as e:
        return _falha(e)


def cancelar(tarefa_id):
    """Desativa tarefa pelo id."""
    try:
        estado = _carregar()
        for t in estado.get("agendadas") or []:
            if t.get("id") == int(tarefa_id):
                t["ativa"] = False
                _salvar(estado)
                _auditar({"evento": "cancelada", "id": t["id"]})
                return _ok(tarefa=t)
        return _falha("tarefa não encontrada: %s" % tarefa_id)
    except Exception as e:
        return _falha(e)


def _rodar_acao(tarefa, timeout=None, dispatch_id=None):
    """Executa uma ação permitida com timeout. Retorna (ok, detalhe, idempotency_key)."""
    from runtime_state import add_note, save_checkpoint, add_pending
    acao = tarefa.get("acao")
    params = tarefa.get("params") or {}
    timeout = TIMEOUT_PADRAO if timeout is None else float(timeout)
    if acao == "nota":
        texto = str(params.get("texto", tarefa.get("nome", "")))
        return True, add_note(texto), "nota:%s:%s" % (tarefa.get("id"), dispatch_id)
    if acao == "checkpoint":
        rotulo = str(params.get("rotulo", "agenda"))
        return True, save_checkpoint(rotulo), "checkpoint:%s:%s" % (tarefa.get("id"), dispatch_id)
    if acao == "pendencia":
        texto = str(params.get("texto", tarefa.get("nome", "")))
        return True, add_pending(texto), "pendencia:%s:%s" % (tarefa.get("id"), dispatch_id)
    if acao == "script":
        alvo = str(params.get("script", ""))
        ok_caminho, caminho = _caminho_seguro(alvo)
        if not ok_caminho:
            return False, caminho, None
        try:
            r = subprocess.run([sys.executable, caminho], capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               timeout=timeout, cwd=BASE)
            saida = (r.stdout or "")[-2000:]
            err = (r.stderr or "")[-500:]
            if err:
                saida = "%s\n[stderr] %s" % (saida, err)
            if r.returncode == 0:
                return True, saida or "[OK] script executado", "script:%s:%s" % (tarefa.get("id"), dispatch_id)
            return False, saida or ("código %d" % r.returncode), "script:%s:%s" % (tarefa.get("id"), dispatch_id)
        except subprocess.TimeoutExpired:
            return False, "timeout após %ss" % timeout, "script:%s:%s" % (tarefa.get("id"), dispatch_id)
    return False, "ação desconhecida: %s" % acao, None


def _adquirir_trava(stale_s=300):
    try:
        os.makedirs(RUNTIME, exist_ok=True)
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            if time.time() - os.path.getmtime(LOCK) > stale_s:
                os.remove(LOCK)
                return _adquirir_trava(stale_s)
        except OSError:
            pass
        return False
    except OSError:
        return False


def _liberar_trava():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def _recuperar_orfaos(estado, agora):
    """Marca running órfão como failed com motivo (crash recovery)."""
    recuperadas = []
    for t in estado.get("agendadas") or []:
        if not t.get("ativa") or t.get("estado") != "running":
            continue
        inicio = _parse_iso(t.get("running_inicio") or "")
        idade = (agora - inicio).total_seconds() if inicio else ORFAO_LIMITE_S + 1
        if idade < ORFAO_LIMITE_S:
            continue
        t["tentativa"] = int(t.get("tentativa") or 0) + 1
        t["ultimo_motivo"] = "órfã após crash (running sem conclusão)"
        t["disparos"].append({"dispatch_id": t.get("dispatch_id", ""),
                              "inicio": t.get("running_inicio", ""),
                              "fim": _iso(agora), "ok": False,
                              "motivo": t["ultimo_motivo"]})
        t["disparos"] = t["disparos"][-10:]
        t["running_inicio"] = ""
        if t.get("recorrencia") == "once":
            if t["tentativa"] > int(t.get("max_tentativas", MAX_TENTATIVAS)):
                t["estado"] = "failed"
                t["ativa"] = False
                t["proxima"] = ""
            else:
                t["estado"] = "failed"
                t["proxima"] = _iso(agora + timedelta(seconds=_backoff(t["tentativa"])))
        else:
            t["estado"] = "failed"
            t["proxima"] = _iso(agora + timedelta(seconds=_backoff(t["tentativa"])))
        recuperadas.append(t.get("id"))
        _auditar({"evento": "orfa-recuperada", "id": t.get("id"),
                  "tentativa": t["tentativa"]})
    return recuperadas


def _reagendar(t, agora, sucesso):
    """Recalcula próxima execução após disparo concluído."""
    rec = t.get("recorrencia")
    if rec == "once":
        t["ativa"] = False
        t["proxima"] = ""
    elif rec == "intervalo":
        t["proxima"] = _iso(agora + timedelta(
            seconds=max(int(t.get("intervalo_s") or 60), 60)))
    elif rec == "janela":
        nxt = _proxima("janela", ref=agora, hora=t.get("hora", ""))
        if nxt:
            t["proxima"] = nxt
        else:
            t["ativa"] = False
            t["ultimo_motivo"] = "hora inválida"


def _disparar(estado, t, agora, timeout):
    """Executa um disparo com estado running persistido antes da ação."""
    dispatch_id = uuid.uuid4().hex[:8]
    idempotency_key = "dispatch:%s:%s" % (t.get("id"), dispatch_id)
    t["estado"] = "running"
    t["dispatch_id"] = dispatch_id
    t["running_inicio"] = _iso(agora)
    _salvar(estado)
    ok_acao, detalhe, idem_key = _rodar_acao(t, timeout=timeout, dispatch_id=dispatch_id)
    fim = _agora()
    t["ultima"] = _iso(fim)
    t["running_inicio"] = ""
    motivo = str(detalhe)[:500]
    t["disparos"].append({"dispatch_id": dispatch_id,
                          "idempotency_key": idem_key,
                          "inicio": _iso(agora), "fim": _iso(fim),
                          "ok": ok_acao, "motivo": motivo})
    t["disparos"] = t["disparos"][-10:]
    if ok_acao:
        t["estado"] = "success"
        t["tentativa"] = 0
        t["ultimo_motivo"] = ""
        _reagendar(t, fim, True)
    else:
        t["tentativa"] = int(t.get("tentativa") or 0) + 1
        t["ultimo_motivo"] = motivo
        if _e_transitoria(motivo) and \
                t["tentativa"] <= int(t.get("max_tentativas", MAX_TENTATIVAS)):
            t["estado"] = "failed"
            t["proxima"] = _iso(fim + timedelta(seconds=_backoff(t["tentativa"])))
        else:
            t["estado"] = "failed"
            _reagendar(t, fim, False)
    _auditar({"evento": "disparo", "id": t.get("id"),
              "dispatch": dispatch_id, "ok": ok_acao,
              "tentativa": t["tentativa"]})
    return {"id": t.get("id"), "nome": t.get("nome"), "ok": ok_acao,
            "detalhe": motivo, "dispatch": dispatch_id,
            "idempotency_key": idem_key, "tentativa": t["tentativa"]}


def _bater_ponto(executadas):
    """Registra prova de vida do tick para o watchdog."""
    try:
        os.makedirs(RUNTIME, exist_ok=True)
        tmp = HEARTBEAT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"ultimo_tick": _iso(_agora()),
                       "executadas": len(executadas)}, f)
        os.replace(tmp, HEARTBEAT)
    except Exception:
        pass


def watchdog(janela_s=600):
    """Verifica prova de vida do tick; alerta se inativo na janela."""
    try:
        with open(HEARTBEAT, encoding="utf-8") as f:
            ponto = json.load(f)
        ultimo = _parse_iso(ponto.get("ultimo_tick") or "")
        if not ultimo:
            return _ok(alerta=True, motivo="heartbeat ilegível")
        idade = (_agora() - ultimo).total_seconds()
        if idade > janela_s:
            _auditar({"evento": "watchdog-alerta", "idade_s": int(idade)})
            return _ok(alerta=True, motivo="tick inativo há %ds" % int(idade),
                       idade_s=int(idade))
        return _ok(alerta=False, idade_s=int(idade))
    except FileNotFoundError:
        return _ok(alerta=True, motivo="nenhum tick registrado ainda")
    except Exception as e:
        return _falha(e)


def executar_vencidas(agora=None, timeout=None):
    """Executa vencidas com recovery, estados e retry (idempotente)."""
    if not _adquirir_trava():
        return _ok(executadas=[], puladas="trava ocupada")
    try:
        estado = _carregar()
        agora = agora or _agora()
        _recuperar_orfaos(estado, agora)
        _salvar(estado)
        feitas = []
        for t in estado.get("agendadas") or []:
            if not t.get("ativa") or t.get("estado") == "running":
                continue
            prox = _parse_iso(t.get("proxima") or "")
            if not prox:
                t["ativa"] = False
                t["estado"] = "failed"
                t["ultimo_motivo"] = "próxima execução inválida"
                _auditar({"evento": "desativada", "id": t.get("id"),
                          "motivo": t["ultimo_motivo"]})
                continue
            if prox > agora:
                continue
            feitas.append(_disparar(estado, t, agora, timeout=timeout))
        _salvar(estado)
        _bater_ponto(feitas)
        return _ok(executadas=feitas)
    except Exception as e:
        return _falha(e)
    finally:
        _liberar_trava()


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Agenda do ecossistema")
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("agendar")
    a.add_argument("nome")
    a.add_argument("acao", choices=list(ACOES))
    a.add_argument("--params", default="{}")
    a.add_argument("--recorrencia", default="once",
                   choices=["once", "intervalo", "janela"])
    a.add_argument("--em", default="")
    a.add_argument("--intervalo", type=int, default=0)
    a.add_argument("--hora", default="")
    sub.add_parser("listar")
    c = sub.add_parser("cancelar")
    c.add_argument("id", type=int)
    sub.add_parser("tick")
    w = sub.add_parser("watchdog")
    w.add_argument("--janela", type=int, default=600)
    args = ap.parse_args(argv)
    if args.cmd == "agendar":
        print(json.dumps(agendar(args.nome, args.acao,
                                 json.loads(args.params),
                                 args.recorrencia, args.em,
                                 args.intervalo, args.hora),
                         ensure_ascii=False, indent=2))
    elif args.cmd == "cancelar":
        print(json.dumps(cancelar(args.id), ensure_ascii=False, indent=2))
    elif args.cmd == "tick":
        print(json.dumps(executar_vencidas(), ensure_ascii=False, indent=2))
    elif args.cmd == "watchdog":
        print(json.dumps(watchdog(args.janela), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(listar(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
