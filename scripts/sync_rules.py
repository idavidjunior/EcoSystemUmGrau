"""sync_rules.py — Sincroniza as 3 camadas de regras do ecossistema.

Fonte unica:  config/agents/00-system-rules.md  (Constituicao)
Camada 1:     AGENTS.md (raiz, auto-carregado pelo opencode) — blocos regenerados
Camada 2:     config/opencode.jsonc -> instructions (referencia AGENTS.md + Constituicao)
Camada 3:     config/agents/00-system-rules.md (deployed para ~/.config/opencode/agents/)

Uso:
  python scripts/sync_rules.py check    # verifica consistencia das 3 camadas
  python scripts/sync_rules.py update   # regenera blocos do AGENTS.md a partir da Constituicao
  python scripts/sync_rules.py audit    # check + update + report

Exit: 0 = consistente, 1 = divergencia encontrada (check).
"""
import os
import re
import sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
CONSTITUICAO = os.path.join(BASE, 'config', 'agents', '00-system-rules.md')
AGENTS_MD = os.path.join(BASE, 'AGENTS.md')
OPENCODE_JSONC = os.path.join(BASE, 'config', 'opencode.jsonc')
USERPROFILE = str(Path.home()).replace('\\', '/')
DEPLOYED_AGENT = os.path.join(USERPROFILE, '.config', 'opencode', 'agents', '00-system-rules.md')

RULES_START = '<!-- RULES:START -->'
RULES_END = '<!-- RULES:END -->'
SOURCES_START = '<!-- SOURCES:START -->'
SOURCES_END = '<!-- SOURCES:END -->'

# Titulos que contam como "regra obrigatoria" na Constituicao
RULE_HEADING_PATTERNS = [
    re.compile(r'^#\s+CLÁUSULA PÉTREA\b', re.IGNORECASE),
    re.compile(r'^#\s+CLÁUSULA PETREA\b', re.IGNORECASE),
    re.compile(r'^#\s+REGRA DE OURO\b', re.IGNORECASE),
    re.compile(r'^#\s+REGRAS DE OURO\b', re.IGNORECASE),
]


def extract_rules_from_constitution():
    """Extrai secoes de regras obrigatorias (Clausulas Petreas + Regras de Ouro)
    da Constituicao, preservando o texto completo de cada secao.

    Divide a Constituicao por TODOS os headings de nivel 1 e mantem apenas as
    secoes cujo titulo e uma regra obrigatoria (CLÁUSULA PÉTREA / REGRA DE OURO).
    """
    with open(CONSTITUICAO, encoding='utf-8') as f:
        lines = f.readlines()

    # Indices de todos os headings de nivel 1 (# titulo)
    h1_idx = [i for i, line in enumerate(lines) if re.match(r'^#\s+\S', line.strip())]

    if not h1_idx:
        return []

    sections = []
    for idx, start in enumerate(h1_idx):
        end = h1_idx[idx + 1] if idx + 1 < len(h1_idx) else len(lines)
        block = ''.join(lines[start:end]).strip()
        title = block.split('\n')[0].strip()
        if any(p.match(title) for p in RULE_HEADING_PATTERNS):
            sections.append(block)

    return sections


def render_rules_block(sections):
    """Monta o bloco RULES a partir das secoes extraidas."""
    if not sections:
        return f'{RULES_START}\n\n<!-- NENHUMA REGRA DETECTADA NA CONSTITUICAO -->\n\n{RULES_END}'
    body = '\n\n'.join(sections)
    return f'{RULES_START}\n\n{body}\n\n{RULES_END}'


def render_sources_block():
    return (
        f'{SOURCES_START}\n'
        '- Constituicao completa: `config/agents/00-system-rules.md`\n'
        '- Regras LER: `ler-runtime/config/agent_rules.json`\n'
        '- Regras de ouro: `README.md` -> "Regras de Ouro"\n'
        f'{SOURCES_END}'
    )


def replace_block(content, start_marker, end_marker, new_block):
    """Substitui o bloco delimitado por start/end markers."""
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    if start_idx == -1 or end_idx == -1:
        return None
    end_idx += len(end_marker)
    return content[:start_idx] + new_block + content[end_idx:]


def ensure_blocks(agents_content):
    """Garante que os delimitadores existam no AGENTS.md."""
    if RULES_START not in agents_content:
        return None
    if SOURCES_START not in agents_content:
        return None
    return True


def update_agents_md(sections):
    """Regenera os blocos RULES e SOURCES no AGENTS.md. Retorna (alterado, novo_conteudo)."""
    with open(AGENTS_MD, encoding='utf-8') as f:
        content = f.read()

    if ensure_blocks(content) is None:
        return False, None

    rules_block = render_rules_block(sections)
    sources_block = render_sources_block()

    new_content = replace_block(content, RULES_START, RULES_END, rules_block)
    if new_content is None:
        return False, None
    new_content = replace_block(new_content, SOURCES_START, SOURCES_END, sources_block)
    if new_content is None:
        return False, None

    changed = new_content != content
    return changed, new_content


def check_instructions_reference():
    """Verifica se opencode.jsonc instructions referencia AGENTS.md e a Constituicao."""
    with open(OPENCODE_JSONC, encoding='utf-8') as f:
        content = f.read()
    ok_agents = 'AGENTS.md' in content
    ok_const = '00-system-rules.md' in content
    return ok_agents, ok_const


def check_deployed():
    """Verifica se a Constituicao deployada e identica a do repo (fonte unica)."""
    if not os.path.exists(DEPLOYED_AGENT):
        return False, 'nao existe'
    try:
        with open(CONSTITUICAO, encoding='utf-8') as f:
            a = f.read()
        with open(DEPLOYED_AGENT, encoding='utf-8') as f:
            b = f.read()
        if a == b:
            return True, 'identica'
        return False, 'divergente'
    except Exception as e:
        return False, str(e)


def cmd_check():
    """Verifica consistencia e reporta. Exit 1 se divergir."""
    errors = []
    if not os.path.exists(CONSTITUICAO):
        print(f'[FAIL] Constituicao nao encontrada: {CONSTITUICAO}')
        return 1
    if not os.path.exists(AGENTS_MD):
        print(f'[FAIL] AGENTS.md nao encontrado: {AGENTS_MD}')
        return 1

    sections = extract_rules_from_constitution()
    print(f'[INFO] {len(sections)} regra(s) na Constituicao')

    # 1. AGENTS.md contem todos os titulos de regra?
    with open(AGENTS_MD, encoding='utf-8') as f:
        agents = f.read()
    for sec in sections:
        title = sec.split('\n')[0].strip()
        title_short = title.replace('# ', '')
        if title_short not in agents:
            errors.append(f'AGENTS.md nao contem: {title_short}')

    # 2. opencode.jsonc references
    ok_agents, ok_const = check_instructions_reference()
    if not ok_agents:
        errors.append('opencode.jsonc instructions nao referencia AGENTS.md')
    if not ok_const:
        errors.append('opencode.jsonc instructions nao referencia 00-system-rules.md')

    # 3. Deployed identico ao repo
    ok_dep, detail = check_deployed()
    if not ok_dep:
        errors.append(f'Constituicao deployada {detail}')

    for e in errors:
        print(f'[DIVERGENCIA] {e}')
    if errors:
        print(f'RESULTADO: {len(errors)} divergencia(s). Rode: python scripts/sync_rules.py update')
        return 1
    print('RESULTADO: 3 camadas consistentes')
    return 0


def cmd_update():
    sections = extract_rules_from_constitution()
    if not sections:
        print('[FAIL] Nenhuma regra detectada na Constituicao')
        return 1
    changed, new_content = update_agents_md(sections)
    if new_content is None:
        print('[FAIL] AGENTS.md sem delimitadores RULES/SOURCES. Edite-o adicionando os marcadores.')
        return 1
    if changed:
        with open(AGENTS_MD, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'[OK] AGENTS.md atualizado ({len(sections)} regra(s) sincronizada(s))')
    else:
        print('[OK] AGENTS.md ja consistente, nada a atualizar')
    return 0


def cmd_audit():
    rc = cmd_check()
    if rc != 0:
        print('\n--- Tentando atualizar ---')
        rc2 = cmd_update()
        rc = 0 if rc2 == 0 else 1
        if rc == 0:
            rc = cmd_check()
    return rc


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    rc = {'check': cmd_check, 'update': cmd_update, 'audit': cmd_audit}.get(cmd, cmd_check)()
    sys.exit(rc)
