---
tipo: erro
tags: [cognitive-core, bug, contrato, str-vs-dict, memoria, contexto]
data: 2026-09-09
contexto: Bug real encontrado ao chamar scripts.cognitive_core.process_user_input via POST /api/chat (Ciclo 4). _get_memory_context retornava str formatada, mas o fluxo esperava dict.
decisao: Normalizar o contrato em 3 pontos: (1) execute_cognitive_cycle agora envolve o contexto de memória em {"memory_context": ...} antes de .update(contexto_override); (2) _execute_conversation_flow trata cada memória como dict ou str em mem_summaries; (3) relevant em formato str vira [{"conteudo": ...}] em vez de fatiar caracteres.
impacto: process_user_input passou a responder sem AttributeError ('str' object has no attribute 'get'/'update'); validado por probe e pelos 11 checks do Ciclo 4.
---

# Bug no cognitive_core — contrato de memória string vs dict

## Sintomas

- `AttributeError: 'str' object has no attribute 'get'` em `_execute_conversation_flow` ao construir `mem_summaries` com `m.get("conteudo", "")`.
- `AttributeError: 'str' object has no attribute 'update'` em `execute_cognitive_cycle` ao fazer `base_context.update(contexto_override)`.

## Causa raiz

`_get_memory_context` delega a `memory_engine.get_context` / `memory_consolidation.get_context_hybrid`, que retornam **string multiline formatada**, enquanto os chamadores esperavam `dict` de memórias.

## Correção aplicada (scripts/cognitive_core.py)

- `execute_cognitive_cycle` (linha ~548): `base_context = {"memory_context": base_context}` quando o resultado vier como str, então usa `.update(contexto_override)` com segurança.
- `_execute_conversation_flow` (linha ~756): `mem_summaries` normaliza cada item — `m.get("conteudo", "")` se for dict, senão `str(m)`.
- `_execute_conversation_flow` (linha ~738): se `relevant` for str, `memories = [{"conteudo": relevant}]` (antes `relevant[:3]` fatiava caracteres soltos).

## Validação

Probe `process_user_input` (conversation e task) → sem erro, response e summary completos; `test_ia_chat.py` do Ciclo 4 → 11 checks OK. Bug de contrato string/dict é padrão recorrente em memória do ecossistema — conferir outros consumidores de `get_context`/`get_context_hybrid` ao integrar.