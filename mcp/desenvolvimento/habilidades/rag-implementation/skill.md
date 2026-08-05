---
name: rag-implementation
description: Implementacao de Retrieval-Augmented Generation: indexacao, chunks, recuperacao, rerank, injecao de contexto e citacao de fontes. Trigger keywords: RAG, retrieval-augmented, injetar contexto, recuperacao, chunks, rerank.
---

# RAG Implementation

## Objetivo

Implementacao de Retrieval-Augmented Generation: indexacao, chunks, recuperacao, rerank, injecao de contexto e citacao de fontes.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
