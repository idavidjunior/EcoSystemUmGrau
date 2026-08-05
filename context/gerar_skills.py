"""Gera skill.md declarativas para os dominios tecnicos do plano.

Formato de cada item em lista_skills: (id, dominio_mcp, titulo, descricao_com_triggers)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lista_skills import SKILLS

ROOT = Path(__file__).resolve().parent.parent
MCP = ROOT / 'mcp'


def split_triggers(desc):
    """Separa a descricao dos triggers ('Trigger keywords: ...' final)."""
    m = re.search(r'(?:Trigger keywords?|Trigger):?\s+(.+)$', desc, re.I)
    if m:
        body = desc[:m.start()].strip()
        trig = m.group(1).strip()
        return body, trig
    return desc, ''


criados = 0
for sk_id, dominio, titulo, desc in SKILLS:
    d = MCP / dominio / 'habilidades' / sk_id
    d.mkdir(parents=True, exist_ok=True)
    body, trig = split_triggers(desc)
    md = f"""---
name: {sk_id}
description: {body} Trigger keywords: {trig}
---

# {titulo}

## Objetivo

{body}

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
"""
    (d / 'skill.md').write_text(md, encoding='utf-8')
    criados += 1

print(f'criadas {criados} skill.md em mcp/*/habilidades/')
