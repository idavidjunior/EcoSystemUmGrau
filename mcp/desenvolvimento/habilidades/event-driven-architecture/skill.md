---
name: event-driven-architecture
description: Arquitetura dirigida a eventos: eventos de dominio, streams, consumidores, saga, idempotencia e consistencia. Trigger keywords: event-driven, arquitetura de eventos, streams, consumidor, saga, idempotencia, pub-sub.
---

# Event-Driven Architecture

## Objetivo

Arquitetura dirigida a eventos: eventos de dominio, streams, consumidores, saga, idempotencia e consistencia.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
