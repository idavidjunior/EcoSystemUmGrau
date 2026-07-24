#!/usr/bin/env python3
"""
Loop Engineering Runtime (LER) v1.2
Entry point unico. Inicializa kernel e executa missao.

Uso:
  python run.py "Criar um aplicativo Android"
  python run.py --status
  python run.py --resume
  python run.py --version
"""

import os
import sys
import json
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def main():
    parser = argparse.ArgumentParser(description="Loop Engineering Runtime v2.0")
    parser.add_argument("goal", nargs="?", help="The mission goal")
    parser.add_argument("--version", "-v", action="store_true", help="Show version")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    parser.add_argument("--reset", action="store_true", help="Reset all state")
    parser.add_argument("--resume", "-r", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--report", action="store_true", help="Generate final report")
    parser.add_argument("--inspect", action="store_true", help="Show architecture and governance info")

    args = parser.parse_args()

    if args.version:
        print("Loop Engineering Runtime (LER) v2.0")
        print("Plataforma de engenharia autonoma orientada por missao")
        print("Camadas: Governanca | Arquitetura | Planejamento | Execucao | "
              "Validacao | Recuperacao | Persistencia | Versionamento | Auditoria")
        return

    config_path = os.path.join(BASE_DIR, "config", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if args.inspect:
        _inspect_system()
        return

    if args.status:
        _show_status()
        return

    if args.reset:
        _reset_state()
        return

    if args.report:
        _generate_report()
        return

    goal = None
    if args.goal:
        goal = args.goal
    elif args.resume:
        goal = "__RESUME__"
    else:
        goal = input("\nMissao: ").strip()
        if not goal:
            print("Nenhuma missao fornecida. Use: python run.py \"sua missao\"")
            return

    from runtime.kernel import LERKernel
    from runtime.mission import MissionRuntime

    kernel = LERKernel()
    layers = kernel.boot()
    session = layers["session"]
    persistence = layers["persistence"]
    security = layers["security"]

    if args.resume:
        latest_cp = persistence.get_latest_checkpoint()
        if latest_cp:
            session.log(f"[LER] Resuming from checkpoint: {latest_cp}")
        else:
            session.log("[LER] No checkpoint found. Starting fresh.")
            return

    mission = MissionRuntime(session, config, persistence, security)
    result = mission.execute(goal)

    print(f"\n{'='*60}")
    print(f"MISSAO: {result.get('status', 'unknown').upper()}")
    print(f"v2.0 | Duracao: {result.get('elapsed_seconds', 0):.1f}s")
    print(f"Iteracoes: {result.get('iterations', 0)}")
    print(f"Passos: {result.get('steps', {}).get('completed', 0)}/"
          f"{result.get('steps', {}).get('total', 0)}")
    print(f"Seguranca: {'OK' if result.get('security', {}).get('safe', True) else 'VIOLACOES'}")
    print(f"{'='*60}")

    if result.get("status") == "completed":
        print("\n[OK] MISSAO CONCLUIDA - Objetivo comprovadamente atingido")
    else:
        print(f"\n[FAIL] Status: {result.get('status', 'unknown')}")

    kernel.shutdown()
    return 0 if result.get("status") == "completed" else 1


def _inspect_system():
    print("\n=== LER SYSTEM INSPECTION ===\n")

    from governance.agent_governance import AgentGovernance
    from governance.conflict_detector import ConflictDetector
    from architecture.review_engine import ArchitectureReviewEngine

    config_path = os.path.join(BASE_DIR, "config", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    from core.session import Session
    session = Session(BASE_DIR)

    print("--- Governance ---")
    gov = AgentGovernance(session, BASE_DIR)
    gov_result = gov.initialize()
    print(f"  Agentes: {gov_result.get('agents', 0)}")
    print(f"  Conflitos: {gov_result.get('conflicts', [])}")

    print("\n--- Architecture ---")
    arch = ArchitectureReviewEngine(session, config)
    arch_result = arch.validate_current()
    print(f"  Valido: {arch_result.get('valid')}")
    print(f"  Modulos: {arch_result.get('checks_performed', 0)} verif., "
          f"{arch_result.get('checks_passed', 0)} OK")

    print("\n--- Conflict Detection ---")
    cd = ConflictDetector(BASE_DIR)
    cd_result = cd.detect_all()
    print(f"  Conflitos: {len(cd_result.get('conflicts', []))}")
    print(f"  Avisos: {len(cd_result.get('warnings', []))}")
    print(f"  Seguro: {cd_result.get('safe')}")

    print(f"\n--- Layers ({config.get('version', 'N/A')}) ---")
    for rule in arch.ARCHITECTURE_RULES:
        print(f"  {rule}")


def _show_status():
    from core.session import Session
    session = Session(BASE_DIR)
    goal = session.get_goal()
    progress = session.load_progress()

    print(f"\n{'='*60}")
    print("LER v2.0 - STATUS")
    print(f"{'='*60}")
    if goal:
        print(f"\nMissao: {goal[:200]}")
    print(f"\nPassos: {len(progress.get('completed_steps', []))}/"
          f"{len(progress.get('steps', []))}")
    print(f"Completos: {progress.get('completed_steps', [])}")
    print(f"Falhos: {progress.get('failed_steps', [])}")

    from runtime.persistence import Persistence
    p = Persistence(BASE_DIR)
    cps = p.list_checkpoints()
    print(f"\nCheckpoints: {len(cps)}")


def _reset_state():
    import shutil
    for d in ["memory", "checkpoints", "reports", "logs"]:
        path = os.path.join(BASE_DIR, d)
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
    print("Estado resetado. Pronto para nova missao.")


def _generate_report():
    from agent.final_auditor import FinalAuditor
    from core.session import Session
    session = Session(BASE_DIR)
    auditor = FinalAuditor(session, BASE_DIR)
    report = auditor.generate_final_report()
    print(report[:2000])


if __name__ == "__main__":
    sys.exit(main())
