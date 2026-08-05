---
name: fine-tuning
description: Ajuste fino de modelos de linguagem: preparacao de dataset, hyperparametros, LoRA/QLoRA, avaliacao de perda de capacidade. Trigger keywords: fine-tune, fine-tuning, LoRA, QLoRA, ajustar modelo, dataset de treino.
---

# Fine-Tuning

## Objetivo

Ajuste fino de modelos de linguagem: preparacao de dataset, hyperparametros, LoRA/QLoRA, avaliacao de perda de capacidade.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
