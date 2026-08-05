---
name: agent-orchestration
description: Orquestracao de agentes de IA: planejamento, execucao paralela, memoria entre passos, ferramentas, loops autonomos e composicao. Trigger keywords: orquestrar agentes, multi-agente, planner, loop autonomo, coordenador de agentes.
---

# Agent Orchestration

## Objetivo

Orquestracao de agentes de IA: planejamento, execucao paralela, memoria entre passos, ferramentas, loops autonomos e composicao.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
