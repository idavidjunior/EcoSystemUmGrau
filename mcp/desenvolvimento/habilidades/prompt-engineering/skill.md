---
name: prompt-engineering
description: Engenharia de prompts para LLMs: design de instrucoes, few-shot, chain-of-thought, contexto, formatos de saida e otimizacao de resultados. Trigger keywords: prompt, instrucao, few-shot, chain-of-thought, system prompt, engenharia de prompt.
---

# Prompt Engineering

## Objetivo

Engenharia de prompts para LLMs: design de instrucoes, few-shot, chain-of-thought, contexto, formatos de saida e otimizacao de resultados.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
