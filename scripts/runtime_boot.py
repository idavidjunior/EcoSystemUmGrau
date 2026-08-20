"""Bootloader do Ecossistema: inicializa o Runtime em toda sessão.

Uso:
  python scripts/runtime_boot.py                # boot completo + relatório
  python scripts/runtime_boot.py --status       # só status (sem restaurar)
  python scripts/runtime_boot.py --check        # só verificação de integridade
  python scripts/runtime_boot.py --report       # relatório final (resumo)

Fluxo (usuário -> Bootloader):
  1. Verifica integridade do ecossistema (arquivos-chave existem, imports OK)
  2. Restaura o estado persistente do Runtime (runtime/state.json)
  3. Carrega memória relevante + preferências via memory_engine
  4. Injeta contexto de sessão (memories.json recentes)
  5. Ativa modo operacional e imprime relatório de boot
"""

import argparse
import json
import os
import subprocess
import sys
import importlib.util

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

CONSTITUICAO = os.path.join(BASE, 'config', 'agents', '00-system-rules.md')
AGENTS_MD = os.path.join(BASE, 'AGENTS.md')
MEMORIES_FILE = os.path.join(BASE, 'conhecimento', 'memoria', 'memories.json')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
CHECKPOINTS_DIR = os.path.join(RUNTIME_DIR, 'checkpoints')

CHECK_ITEMS = [
    ('Constituição', CONSTITUICAO),
    ('AGENTS.md', AGENTS_MD),
    ('Memória persistente', MEMORIES_FILE),
    ('Diretório Runtime', RUNTIME_DIR),
    ('Checkpoints', CHECKPOINTS_DIR),
]


def _exists(path):
    return os.path.exists(path)


def check_language_integrity():
    """Verifica se a Constituição e AGENTS.md estão em pt-BR.
    Retorna (ok, detalhes).
    """
    try:
        from validar_idioma import validar_idioma
    except ImportError:
        # Se o módulo não estiver disponível, pular verificação
        return True, [('Validação de idioma', True, 'módulo não disponível, pulado')]

    details = []
    all_ok = True

    # Verificar Constituição (threshold mais baixo porque contém termos técnicos)
    try:
        with open(CONSTITUICAO, encoding='utf-8') as f:
            conteudo = f.read()
        resultado = validar_idioma(conteudo, threshold=15)
        ok = resultado['ok']
        all_ok = all_ok and ok
        details.append(('Constituição (idioma)', ok,
                       f"score={resultado['score']}, idioma={resultado['idioma']}"))
    except Exception as e:
        all_ok = False
        details.append(('Constituição (idioma)', False, f'ERRO: {e}'))

    # Verificar AGENTS.md (threshold mais baixo porque contém termos técnicos)
    try:
        with open(AGENTS_MD, encoding='utf-8') as f:
            conteudo = f.read()
        resultado = validar_idioma(conteudo, threshold=15)
        ok = resultado['ok']
        all_ok = all_ok and ok
        details.append(('AGENTS.md (idioma)', ok,
                       f"score={resultado['score']}, idioma={resultado['idioma']}"))
    except Exception as e:
        all_ok = False
        details.append(('AGENTS.md (idioma)', False, f'ERRO: {e}'))

    # Verificar se cláusula PT-BR está no topo da Constituição
    try:
        with open(CONSTITUICAO, encoding='utf-8') as f:
            linhas = f.readlines()
        # Procurar pela cláusula de idioma nas primeiras 50 linhas
        ptbr_no_topo = False
        for i, linha in enumerate(linhas[:50]):
            if 'IDIOMA' in linha.upper() and 'PT-BR' in linha.upper():
                ptbr_no_topo = True
                break
        details.append(('Cláusula PT-BR no topo', ptbr_no_topo,
                       'Constituição' if ptbr_no_topo else 'Cláusula não encontrada no topo'))
        all_ok = all_ok and ptbr_no_topo
    except Exception as e:
        details.append(('Cláusula PT-BR no topo', False, f'ERRO: {e}'))

    return all_ok, details


def check_data_integrity():
    """Verifica integridade dos dados JSON (mojibake/truncamento) via integrity_guard.
    Retorna (ok, detalhes).
    """
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, 'integrity_guard.py'), '--check'],
            capture_output=True, text=True, timeout=60, cwd=BASE)
        out = (r.stdout + r.stderr).strip()
        if r.returncode == 0:
            return True, [('Integridade de dados', True, 'nenhuma corrupção')]
        # extrai os arquivos corrompidos do relatório
        corrompidos = [l.split()[1] for l in out.splitlines() if l.strip().startswith('[')]
        return False, [('Integridade de dados', False,
                       f'{len(corrompidos)} arquivo(s) com corrupção: {", ".join(corrompidos)}')]
    except Exception as e:
        return False, [('Integridade de dados', False, f'ERRO: {e}')]


def check_integrity():
    """Verifica integridade do ecossistema. Retorna (ok, detalhes)."""
    details = []
    all_ok = True
    for label, path in CHECK_ITEMS:
        ok = _exists(path)
        all_ok = all_ok and ok
        details.append((label, ok, path))
    # Verificação de idioma
    lang_ok, lang_details = check_language_integrity()
    all_ok = all_ok and lang_ok
    details.extend(lang_details)
    # Verificação de integridade dos dados (mojibake/truncamento)
    data_ok, data_details = check_data_integrity()
    all_ok = all_ok and data_ok
    details.extend(data_details)
    # runtime_state importável?
    try:
        from runtime_state import load_state
        load_state()
        details.append(('Runtime State (módulo)', True, 'scripts/runtime_state.py'))
    except Exception as e:
        all_ok = False
        details.append(('Runtime State (módulo)', False, f'ERRO: {e}'))
    # memory_engine importável?
    try:
        import memory_engine
        details.append(('Memory Engine (módulo)', True, 'scripts/memory_engine.py'))
    except Exception as e:
        all_ok = False
        details.append(('Memory Engine (módulo)', False, f'ERRO: {e}'))
    # módulos da camada 3?
    for mod in ('runtime_kernel', 'runtime_context', 'runtime_auditor', 'tool_orchestrator', 'llm_router', 'knowledge_graph', 'agent_council', 'mission_planner', 'security_engine', 'audit_engine', 'learning_engine'):
        try:
            __import__(mod)
            details.append((f'{mod} (módulo)', True, f'scripts/{mod}.py'))
        except Exception as e:
            all_ok = False
            details.append((f'{mod} (módulo)', False, f'ERRO: {e}'))
    return all_ok, details


def load_session_context(limit=5):
    """Carrega memórias relevantes e preferências para a sessão."""
    try:
        import memory_engine
        mems = memory_engine.query(limit=limit)
        context = []
        for m in mems:
            context.append({
                'id': m['id'],
                'kind': m['kind'],
                'task': m['task'],
                'summary': m['summary'][:140],
            })
        prefs = memory_engine.query(kind='preferencia', limit=3)
        return context, prefs
    except Exception:
        return [], []


def load_runtime_state():
    """Restaura o estado persistente do Runtime."""
    from runtime_state import load_state
    return load_state()


def render_report(state, integrity_ok, integrity_details, memories, prefs):
    lines = []
    lines.append('=== BOOTLOADER ECOSYSTEM ===')
    lines.append(f"Data/hora:    {state.get('updated_at')}")
    lines.append(f"Integridade:  {'OK' if integrity_ok else 'FALHOU'}")
    for label, ok, path in integrity_details:
        lines.append(f"  {'[OK]' if ok else '[X]'} {label} -> {path}")
    lines.append('')
    lines.append('--- KERNEL (autoridade máxima) ---')
    try:
        from runtime_kernel import Kernel
        kernel = Kernel()
        for r in kernel.rules:
            lines.append(f"  • {r}")
    except Exception as e:
        lines.append(f"  (kernel indisponível: {e})")
    lines.append('')
    lines.append('--- ESTADO RESTAURADO ---')
    if state.get('active_project'):
        lines.append(f"Projeto ativo:  {state['active_project']}")
    if state.get('objective'):
        lines.append(f"Objetivo:       {state['objective']}")
    if state.get('last_task'):
        lines.append(f"Última tarefa:  {state['last_task']}")
    if state.get('operational_context'):
        lines.append(f"Contexto:       {state['operational_context']}")
    agents = state.get('active_agents') or []
    if agents:
        lines.append(f"Agentes ativos: {', '.join(agents)}")
    pending = [p for p in state.get('pending', []) if not p.get('done')]
    if pending:
        lines.append('Pendências:')
        for p in pending:
            lines.append(f"  [#{p['id']}] {p['text']}")
    if state.get('last_checkpoint'):
        lines.append(f"Checkpoint:     {state['last_checkpoint']}")
    lines.append('')
    lines.append('--- MEMÓRIA CARREGADA PARA A SESSÃO ---')
    if memories:
        for m in memories:
            lines.append(f"  [{m['kind']}] {m['task'][:70]}")
    else:
        lines.append('  (sem memórias relevantes)')
    if prefs:
        lines.append('Preferências:')
        for p in prefs:
            lines.append(f"  - {p['task'][:80]}")
    lines.append('')
    lines.append('--- MODO OPERACIONAL ---')
    lines.append('  Runtime ativo. Estado restaurado automaticamente.')
    lines.append('  Fluxo: Usuário -> Bootloader -> Kernel -> Memory -> Context -> '
                 'Conselho (se necessário) -> LER (se complexo) -> Validador -> '
                 'Resposta -> Auditor.')
    lines.append('')
    lines.append('--- IDIOMA ---')
    lines.append('  PT-BR: REGRAS DE IDIOMA ATIVAS (cláusula pétreia no topo)')
    lines.append('  Todas as respostas DEVEM ser em Português do Brasil.')
    lines.append('')
    lines.append('--- MÓDULOS DISPONÍVEIS ---')
    lines.append('  context loader: python scripts/runtime_context.py "<assunto>"')
    lines.append('  auditor:        python scripts/runtime_auditor.py <objetivo> '
                 '--resposta "<texto>"')
    lines.append('  kernel:         python scripts/runtime_kernel.py check "<texto>"')
    lines.append('  validador idioma: python scripts/validar_idioma.py "texto"')
    lines.append('  Nenhuma conversa é sessão isolada: todas compartilham este estado.')
    return '\n'.join(lines)


def run_boot(status_only=False):
    from runtime_state import load_state, render_status, _ensure_dirs
    _ensure_dirs()
    state = load_state()
    integrity_ok, details = check_integrity()
    if status_only:
        print(render_status(state))
        return 0 if integrity_ok else 1
    memories, prefs = load_session_context()
    print(render_report(state, integrity_ok, details, memories, prefs))
    return 0 if integrity_ok else 1


def main():
    parser = argparse.ArgumentParser(description='Bootloader do Ecossistema')
    parser.add_argument('--status', action='store_true', help='só status, sem carregar memória')
    parser.add_argument('--check', action='store_true', help='só verificação de integridade')
    parser.add_argument('--report', action='store_true', help='relatório final compacto')
    args = parser.parse_args()

    if args.check:
        ok, details = check_integrity()
        for label, ok_, path in details:
            print(f"{'[OK]' if ok_ else '[X]'} {label}: {path}")
        print('INTEGRIDADE:', 'OK' if ok else 'FALHOU')
        return 0 if ok else 1

    code = run_boot(status_only=args.status)
    # auto-conectar ADB ao celular via Tailscale se necessário
    import subprocess
    subprocess.run([sys.executable, os.path.join(SCRIPTS, 'adb_auto_connect.py')], check=False)
    return code


if __name__ == '__main__':
    sys.exit(main())
