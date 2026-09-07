#!/usr/bin/env python3
"""Dashboard de Autonomia — EcoSystemUmGrau

Mostra métricas do loop autônomo de melhoria contínua.
"""

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RUNTIME = BASE / "runtime"
AUTONOMIA_DIR = RUNTIME / "autonomia"
AUTONOMIA_STATE = AUTONOMIA_DIR / "state.json"
AUTONOMIA_LOG = AUTONOMIA_DIR / "autonomo.log"


def _carregar_estado():
    if AUTONOMIA_STATE.exists():
        try:
            with open(AUTONOMIA_STATE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _ler_log(ultimas=20):
    eventos = []
    if AUTONOMIA_LOG.exists():
        try:
            with open(AUTONOMIA_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        eventos.append(json.loads(line))
        except Exception:
            pass
    return eventos[-ultimas:]


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Dashboard de Autonomia")
    ap.add_argument("--json", action="store_true", help="Saída em JSON")
    args = ap.parse_args()
    
    estado = _carregar_estado()
    log = _ler_log(50)
    
    if args.json:
        print(json.dumps({"estado": estado, "log_recente": log}, ensure_ascii=False, indent=2))
        return 0
    
    # Output formatado
    print("=" * 60)
    print("DASHBOARD DE AUTONOMIA - EcoSystemUmGrau")
    print("=" * 60)
    
    est = estado.get("estatisticas", {})
    print(f"\nESTATÍSTICAS GERAIS:")
    print(f"  Ciclos executados:     {est.get('ciclos_total', 0)}")
    print(f"  Ações totais:          {est.get('acoes_total', 0)}")
    print(f"  Sucessos:              {est.get('sucessos', 0)}")
    print(f"  Falhas:                {est.get('falhas', 0)}")
    
    taxa = 0
    if est.get('acoes_total', 0) > 0:
        taxa = (est.get('sucessos', 0) / est.get('acoes_total', 1)) * 100
    print(f"  Taxa de sucesso:       {taxa:.1f}%")
    
    print(f"\nÚLTIMO CICLO: {estado.get('ultimo_ciclo', 'N/A')}")
    
    skills = estado.get("skills_criadas", [])
    print(f"\nSKILLS CRIADAS ({len(skills)}):")
    for s in skills:
        print(f"  - {s.get('nome', 'N/A')} (padrão: {s.get('padrao_origem', 'N/A')})")
        print(f"    {s.get('timestamp', 'N/A')} | {len(s.get('memorias_base', []))} memórias base")
    
    padroes = estado.get("padroes_detectados", {})
    print(f"\nPADRÕES MONITORADOS ({len(padroes)}):")
    for p, ts in list(padroes.items())[:10]:
        print(f"  - {p}: último em {ts}")
    
    print(f"\nLOG RECENTE ({len(log)} eventos):")
    for e in log[-10:]:
        ts = e.get("timestamp", "N/A")
        evt = e.get("evento", "N/A")
        dados = e.get("dados", {})
        det = ""
        if isinstance(dados, dict):
            if "padrao" in dados:
                det = f" | padrão: {dados['padrao']}"
            elif "nome" in dados:
                det = f" | skill: {dados['nome']}"
            elif "motivo" in dados:
                det = f" | {dados['motivo'][:50]}"
        print(f"  {ts} | {evt}{det}")
    
    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())