#!/usr/bin/env python3
"""Health Aggregator - Score unico de saude do EcoSystemUmGrau (0-100).

Agrega em um unico numero a saude das principais camadas do runtime,
reutilizando os arquivos de estado ja existentes (fail-soft: se algo
nao existir, aquela dimensao pontua neutro e nao quebra o agregado).

Camadas:
  1. PROCESSOS   - servicos criticos vivos (via maestro_estado.json / guardian)
  2. RUNTIME     - estado persistente (state.json) valido e recente
  3. MEMORIA     - memories.json saldavel (carregavel, sem corrupcao)
  4. CONHECIMENTO- knowledge_graph.json presente e valido
  5. REGRAS/GATES- preflight e aderencia (auditoria) recentes
  6. RECURSOS    - modelo (model_monitor.json) e disco saudaveis

Uso:
  python scripts/health_aggregator.py            # relatorio legivel
  python scripts/health_aggregator.py --json     # JSON completo
Importavel: from health_aggregator import health_score
"""
import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

BASE = Path(__file__).resolve().parent.parent
RUNTIME = BASE / "runtime"
DATA = BASE / "conhecimento" / "memoria"

DIMENSOES = (
    "processos", "runtime", "memoria", "conhecimento", "regras", "recursos"
)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _age_hours(ts) -> float:
    """Idade de um timestamp unix em horas; -1 se invalido/ausente."""
    if not ts:
        return -1.0
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return -1.0
    return max(0.0, (_dt.datetime.now().timestamp() - ts) / 3600.0)


def score_processos() -> Dict[str, Any]:
    """Servicos criticos registrados no maestro; % de servicos vivos."""
    estado = _load_json(RUNTIME / "maestro_estado.json")
    servicos = estado.get("servicos", {})
    total = max(1, len(servicos))
    vivos = sum(1 for s in servicos.values() if s.get("vivo"))
    pct = vivos / total * 100.0
    status = "ok" if vivos == total else ("warn" if vivos >= total / 2 else "bad")
    return {
        "score": round(pct, 1), "status": status,
        "detail": f"{vivos}/{total} servicos criticos vivos",
    }


def score_runtime() -> Dict[str, Any]:
    """State.json valido e restaurado recentemente (< 48h)."""
    st = _load_json(RUNTIME / "state.json")
    if not st:
        return {"score": 0, "status": "bad", "detail": "state.json ausente/vazio"}
    updated = st.get("updated_at")
    if isinstance(updated, str):
        return {"score": 100, "status": "ok",
                "detail": f"state.json valido (atualizado {updated})"}
    age = _age_hours(updated)
    if age < 0:
        return {"score": 50, "status": "warn", "detail": "sem timestamp"}
    score = max(0, 100 - (age / 48.0) * 100)
    return {
        "score": round(score, 1),
        "status": "ok" if score > 70 else ("warn" if score > 40 else "bad"),
        "detail": f"state.json {age:.1f}h",
    }


def score_memoria() -> Dict[str, Any]:
    """Memories.json carregavel e com registros."""
    path = DATA / "memories.json"
    if not path.exists():
        return {"score": 0, "status": "bad", "detail": "memories.json ausente"}
    dados = _load_json(path)
    # tolera dict { "memorias": [...] } ou lista
    items = dados if isinstance(dados, list) else dados.get("memorias", dados.get("memories", []))
    if isinstance(items, list) and items:
        return {"score": 100, "status": "ok", "detail": f"{len(items)} memorias saldaveis"}
    return {"score": 40, "status": "warn", "detail": "memories.json vazio ou nao-listavel"}


def _contar_grafo(dados: Any) -> int:
    if isinstance(dados, dict):
        for key in ("nodes", "vertices"):
            if isinstance(dados.get(key), list):
                return len(dados[key])
        return len(dados)
    if isinstance(dados, list):
        return len(dados)
    return 0


def score_conhecimento() -> Dict[str, Any]:
    """Knowledge graph presente e valido (ler-runtime/knowledge ou busca ampla)."""
    candidatos = [
        BASE / "ler-runtime" / "knowledge" / "knowledge_graph.json",
        BASE / "knowledge" / "knowledge_graph.json",
    ]
    candidatos += list((BASE / "conhecimento").rglob("knowledge_graph.json"))
    for cand in candidatos:
        try:
            if not cand.exists():
                continue
            dados = _load_json(cand)
        except Exception:
            continue
        n = _contar_grafo(dados)
        if dados:
            return {"score": 100, "status": "ok", "detail": f"grafo com {n} nodes"}
    return {"score": 30, "status": "warn", "detail": "graph sem contagem"}


def score_regras() -> Dict[str, Any]:
    """Gates recentes: aderencia/auditoria geradas nas ultimas 72h."""
    anchor = None
    for p in (RUNTIME / "auditoria_aderencia").rglob("*.json"):
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        age = _age_hours(mtime)
        if age >= 0 and age <= 72:
            anchor = p.name
            break
    if not anchor and (RUNTIME / "audit_result.json").exists():
        try:
            age = _age_hours((RUNTIME / "audit_result.json").stat().st_mtime)
        except OSError:
            age = -1
        if 0 <= age <= 72:
            anchor = "audit_result.json"
    if anchor:
        return {"score": 100, "status": "ok", "detail": f"gate recente ({anchor})"}
    return {"score": 50, "status": "warn", "detail": "sem gate de auditoria recente (72h)"}


def score_recursos() -> Dict[str, Any]:
    """Modelo monitorado e espaco em disco acima do minimo."""
    issues = []
    mm = _load_json(RUNTIME / "model_monitor.json")
    if not mm:
        issues.append("model_monitor.json ausente")
    # espaco em disco (mais de 5% livre)
    try:
        usage = os.statvfs(str(BASE))
        free_pct = usage.f_bavail / usage.f_blocks * 100.0
        if free_pct < 5:
            issues.append(f"disco critico ({free_pct:.0f}% livre)")
    except Exception:
        pass
    if not issues:
        return {"score": 100, "status": "ok", "detail": "modelo+disco ok"}
    return {"score": 50, "status": "warn", "detail": "; ".join(issues)}


_SCORES = {
    "processos": score_processos,
    "runtime": score_runtime,
    "memoria": score_memoria,
    "conhecimento": score_conhecimento,
    "regras": score_regras,
    "recursos": score_recursos,
}


def health_score() -> Dict[str, Any]:
    """Retorna dict com score geral (0-100) e detalhe por dimensao."""
    camadas = {}
    for nome in DIMENSOES:
        try:
            camadas[nome] = _SCORES[nome]()
        except Exception as e:  # fail-soft: dimensao nunca derruba o todo
            camadas[nome] = {"score": 50, "status": "warn",
                             "detail": f"erro: {e}"}
    geral = round(sum(c["score"] for c in camadas.values()) / len(camadas), 1)
    if geral >= 80:
        status = "SALDAVEL"
    elif geral >= 55:
        status = "DEGRADADO"
    else:
        status = "CRITICO"
    return {
        "score": geral, "status": status, "camadas": camadas,
        "gerado_em": _dt.datetime.now().isoformat(timespec="seconds"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Score de saude do ecossistema")
    ap.add_argument("--json", action="store_true", help="saida JSON")
    args = ap.parse_args()
    res = health_score()
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    print("=" * 44)
    print(f" SAUDE ECO: {res['score']}/100  [{res['status']}]")
    print("=" * 44)
    for nome in DIMENSOES:
        c = res["camadas"][nome]
        barra = "#" * int(c["score"] // 10)
        print(f" {nome:<12} {c['score']:>5.1f}  {barra:<10} {c['status']}")
    print("=" * 44)
    return 0


if __name__ == "__main__":
    sys.exit(main())
