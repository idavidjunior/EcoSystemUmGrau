---
name: threat-modeling
description: Modelagem de ameacas: identificar ativos, adversarios, superficies de ataque e mitigacoes (STRIDE). Trigger keywords: threat modeling, modelagem de ameaca, STRIDE, adversario, superficie de ataque, DREAD.
---

# Threat Modeling

## Objetivo

Modelagem de ameacas: identificar ativos, adversarios, superficies de ataque e mitigacoes (STRIDE).

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
