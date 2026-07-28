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
    parser.add_argument("--audit", nargs="?", const=".", help="Scan project for code issues")
    parser.add_argument("--fix", nargs="?", const=".", help="Scan and auto-fix code issues")
    parser.add_argument("--learn", action="store_true", help="Consolidate knowledge from all sources")
    parser.add_argument("--export", action="store_true", help="Export all knowledge to a portable Markdown file")

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

    if args.learn:
        _consolidate_knowledge()
        return

    if args.export:
        _export_knowledge()
        return

    if args.audit is not None:
        _run_audit(args.audit, fix=False)
        return

    if args.fix is not None:
        _run_audit(args.fix, fix=True)
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

    # Auto-learn from every mission — enrich with session context
    try:
        from agent.knowledge_consolidator import KnowledgeConsolidator
        kc = KnowledgeConsolidator(BASE_DIR)
        kc.auto_learn(result)
        # Add session summary as cognitive pattern for future learning
        session_summary = {
            "session_summary": f"Missao: {result.get('goal_objective', 'N/A')[:200]}. "
                               f"Status: {result.get('status', 'unknown')}. "
                               f"Iteracoes: {result.get('iterations', 0)}. "
                               f"Steps: {result.get('steps', {}).get('completed', 0)}/"
                               f"{result.get('steps', {}).get('total', 0)}.",
            "tags": ["auto_learned", result.get("status", "unknown")],
        }
        kc.consolidate_from_session(session_summary)
        print(f"[KNOWLEDGE] Aprendizado consolidado apos missao.")
    except Exception as e:
        print(f"[KNOWLEDGE] Erro ao aprender: {e}")

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


def _run_audit(target_dir, fix=False):
    project_dir = os.path.abspath(target_dir)
    if not os.path.isdir(project_dir):
        print(f"ERRO: Diretorio nao encontrado: {project_dir}")
        return
    from tools.analyzer import audit
    report, path = audit(project_dir, fix=fix)
    print("\n" + "=" * 60)
    print(f"LER AUDIT: {os.path.basename(project_dir)}")
    print("=" * 60)
    print(f"Tipo: {report['type']}")
    print(f"Total de issues: {report['total_issues']}")
    print(f"Arquivos escaneados: {report['files_scanned']}")
    print(f"\nPor categoria:")
    for cat, count in sorted(report["by_category"].items()):
        print(f"  {cat}: {count}")
    if report["issues"]:
        print(f"\nIssues:")
        for issue in report["issues"][:30]:
            loc = f":{issue['line']}" if issue["line"] else ""
            cat = issue["category"].ljust(12)
            print(f"  [{cat}] {issue['file']}{loc} — {issue['message'][:100]}")
        if len(report["issues"]) > 30:
            print(f"  ... e mais {len(report['issues']) - 30} issues")
    print(f"\nRelatorio salvo: {path}")
    print("=" * 60)
    if fix:
        print("\nModo --fix: correcoes auto-aplicaveis rodadas")
    print(f"\nDica: {'ler --audit' if not fix else 'ler --fix'} para reavaliar")


def _consolidate_knowledge():
    from agent.knowledge_consolidator import consolidate
    stats = consolidate(BASE_DIR)
    print(f"\nConsolidado: {stats['patterns']} padroes, {stats['decisions']} decisoes, "
          f"{stats['bug_fixes']} bug fixes, {stats['projects']} projetos, "
          f"{stats['skills']} skills")


def _export_knowledge():
    from agent.knowledge_consolidator import KnowledgeConsolidator
    kc = KnowledgeConsolidator(BASE_DIR)
    kc.consolidate()
    g = kc.graph

    lines = []
    lines.append("# Base de Conhecimento — Exportacao Completa")
    lines.append("")
    lines.append(f"**Exportado em:** {g.get('last_updated', 'N/A')}")
    lines.append(f"**Projetos:** {len(g['projects'])}")
    lines.append(f"**Padroes Tecnicos:** {len(g['patterns'])}")
    lines.append(f"**Decisoes:** {len(g['decisions'])}")
    lines.append(f"**Bug Fixes:** {len(g['bug_fixes'])}")
    lines.append(f"**Padroes Cognitivos:** {len(g['cognitive_patterns'])}")
    lines.append(f"**Heuristicas:** {len(g['heuristics'])}")
    lines.append(f"**Frameworks:** {len(g['frameworks'])}")
    lines.append(f"**Missoes Aprendidas:** {len(g['mission_learnings'])}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Como Usar Esta Base de Conhecimento")
    lines.append("")
    lines.append("Esta base contem **conhecimento cognitivo e tecnico** acumulado entre projetos. ")
    lines.append("Ela e organizada em 3 niveis:")
    lines.append("")
    lines.append("1. **Conhecimento Tecnico** — Padroes de codigo, pipelines de build, decisoes arquiteturais, bug fixes")
    lines.append("2. **Conhecimento Cognitivo** — Heuristicas de debugging, frameworks de raciocinio, estrategias validadas")
    lines.append("3. **Meta-Conhecimento** — Como a propria base e estruturada e auto-melhorada")
    lines.append("")
    lines.append("### Para uma IA nova:")
    lines.append("- Leia os **Frameworks** primeiro — eles ensinam padroes de pensamento")
    lines.append("- Leia as **Heuristicas** — sao regras praticas que se aplicam a qualquer projeto")
    lines.append("- Leia os **Padroes Cognitivos** — mergulho profundo em estrategias de resolucao de problemas")
    lines.append("- Use **Decisoes** e **Bug Fixes** como exemplos concretos")
    lines.append("")
    lines.append("### Para estender:")
    lines.append("- Use `consolidate_from_session()` no final de cada sessao")
    lines.append("- Use `extract_from_text()` para extrair conhecimento de textos livres")
    lines.append("- A base faz merge inteligente (similaridade Jaccard) — nao se preocupe em duplicar")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Projetos")
    lines.append("")
    for proj in sorted(g['projects'].keys()):
        lines.append(f"- **{proj}**")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Padroes Tecnicos")
    lines.append("")
    lines.append("| # | Fonte | Titulo/Acao |")
    lines.append("|---|-------|-------------|")
    for i, p in enumerate(g['patterns'], 1):
        fonte = p.get("source", "?")
        titulo = p.get("title", p.get("action", p.get("description", "?")))
        lines.append(f"| {i} | {fonte} | {titulo[:120]} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Decisoes Arquiteturais")
    lines.append("")
    for d in g['decisions']:
        lines.append(f"### {d.get('decision', '?')[:100]}")
        lines.append(f"**Fonte:** {d.get('source', '?')}")
        if d.get('rationale'):
            lines.append(f"**Fundamento:** {d['rationale']}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Bug Fixes e Corrigidos")
    lines.append("")
    for b in g['bug_fixes']:
        lines.append(f"### {b.get('issue', b.get('fix', '?'))[:100]}")
        lines.append(f"**Fonte:** {b.get('source', '?')}")
        if b.get('root_cause'):
            lines.append(f"**Causa Raiz:** {b['root_cause'][:300]}")
        if b.get('fix'):
            lines.append(f"**Correcao:** {b['fix'][:300]}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Padroes Cognitivos")
    lines.append("")
    for c in g['cognitive_patterns']:
        lines.append(f"### {c.get('title', '?')[:100]}")
        lines.append(f"**Dominio:** {c.get('domain', 'general')}")
        lines.append(f"**Fonte:** {c.get('source', '?')}")
        body = c.get('body', '')
        if body:
            lines.append(f"")
            lines.append(body[:500])
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Heuristicas")
    lines.append("")
    lines.append("| # | Dominio | Titulo | Descricao |")
    lines.append("|---|--------|--------|-----------|")
    for i, h in enumerate(g['heuristics'], 1):
        dom = h.get("domain", "general")
        titulo = h.get("title", "?")
        desc = h.get("description", "")[:150]
        lines.append(f"| {i} | {dom} | {titulo} | {desc} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Frameworks")
    lines.append("")
    for fw in g['frameworks']:
        lines.append(f"### {fw.get('name', '?')[:100]}")
        lines.append(f"**Fonte:** {fw.get('source', '?')}")
        desc = fw.get('description', '')
        if desc:
            lines.append(f"**Descricao:** {desc}")
        body = fw.get('body', '')
        if body:
            lines.append("")
            lines.append(body[:500])
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Missoes e Aprendizados")
    lines.append("")
    for m in g['mission_learnings']:
        st = m.get('status', '?')
        it = m.get('iterations', '?')
        obj = m.get('goal_objective', m.get('message', ''))[:150]
        lines.append(f"- **Status:** {st} | **Iteracoes:** {it} | **Objetivo:** {obj}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Skills Referenciados")
    lines.append("")
    for s in g['skill_references']:
        lines.append(f"- **{s.get('skill', '?')}** — hash: {s.get('hash', 'N/A')[:12]}... | ultima extracao: {s.get('last_extracted', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Meta-Informacao")
    lines.append("")
    lines.append(f"**Versao do grafo:** {g.get('version', 1)}")
    lines.append(f"**Ultima atualizacao:** {g.get('last_updated', 'N/A')}")
    lines.append("**Proposito:** Base de conhecimento universal e auto-melhoravel para engenharia de software")
    lines.append("**Como e alimentada:** Toda missao LER, toda sessao com IA, toda extracao de skill")
    lines.append("**Merge:** Similaridade Jaccard > 0.55 funde entradas similares automaticamente")
    lines.append("")
    lines.append("*Fim da exportacao. Este arquivo MARKDOWN pode ser fornecido como contexto para QUALQUER IA.*")

    content = "\n".join(lines)
    export_path = os.path.join(BASE_DIR, "CONHECIMENTO.md")
    tmp = export_path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, export_path)
        print(f"\nConhecimento exportado para: {export_path}")
        print(f"Total: {len(g['patterns'])} padroes, {len(g['decisions'])} decisoes, "
              f"{len(g['bug_fixes'])} bug fixes")
        print(f"\nEste arquivo MARKDOWN pode ser:")
        print(f"  - Copiado para qualquer computador")
        print(f"  - Fornecido como contexto para QUALQUER IA")
        print(f"  - Lido por humanos")
        print(f"  - Versionado no git")
    except Exception as e:
        print(f"Erro ao exportar: {e}")


if __name__ == "__main__":
    sys.exit(main())
