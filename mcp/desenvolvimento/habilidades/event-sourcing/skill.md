---
name: event-sourcing
description: Armazenamento de estado como sequencia de eventos: append-only, replay, projecoes e consistencia eventual. Trigger keywords: event sourcing, eventos de dominio, replay, projecoes, append-only, event store.
---

# Event Sourcing

## Objetivo

Armazenamento de estado como sequencia de eventos: append-only, replay, projecoes e consistencia eventual.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
