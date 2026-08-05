---
name: adr
description: Registros de decisoes de arquitetura: contexto, decisao, consequencias, formato e manutencao do registro. Trigger keywords: ADR, architecture decision record, registro de decisao, contexto, consequencia, Nygard.
---

# ADR (Architecture Decision Records)

## Objetivo

Registros de decisoes de arquitetura: contexto, decisao, consequencias, formato e manutencao do registro.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
