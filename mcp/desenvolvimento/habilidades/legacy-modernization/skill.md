---
name: legacy-modernization
description: Modernizacao de sistemas legados: estrtatira, modulo a modulo, estrangulamento, lift-and-shift e migracao segura. Trigger keywords: legacy, legado, modernizacao, estrangulamento, strangler fig, migracao, lift-and-shift.
---

# Legacy Modernization

## Objetivo

Modernizacao de sistemas legados: estrtatira, modulo a modulo, estrangulamento, lift-and-shift e migracao segura.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
