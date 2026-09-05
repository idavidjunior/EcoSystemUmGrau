---
tags: [cognitivo, conteúdo, general, generate, memória, notes]
aliases: [erro]
date: 2026-09-05
---

# erro

**Dominio:** general

Tipo: erro

Tags: [teste, pipeline]

Data: 2026-08-02

Contexto: Teste funcional do pipeline de tags semanticas ponta a ponta

# Teste de integração do pipeline de tags semânticas

Este é um arquivo de teste temporário para validar que as tags semânticas
fluem da origem até o grafo do widget.

## Decisão

Integrar extração RAKE leve no knowledge_consolidator, generate-obsidian-notes
e memory_engine para enriquecer as sinapses do grafo Obsidian.

## Impacto

O grafo do widget deve mostrar ma

tipo: erro
tags: [teste, pipeline]
data: 2026-08-02
contexto: Teste funcional do pipeline de tags semanticas ponta a ponta
---
# Teste de integração do pipeline de tags semânticas

Este é um arquivo de teste temporário para validar que as tags semânticas
fluem da origem até o grafo do widget.

## Decisão

Integrar extração RAKE leve no knowledge_consolidator, generate-obsidian-notes
e memory_engine para enriquecer as sinapses do grafo Obsidian.

## Impacto

O grafo do widget deve mostrar ma

## Sintoma
`python scripts/runtime_context.py "<assunto>"` crashava com:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2194'
in position 616: character maps to <undefined>
```

No Windows, o stdout usa cp1252 por padrão. Memórias contendo caracteres fora de
cp1252 — como a seta `↔` da cláusula @sync ("Local PC ↔ GitHub") em
`conhecimento/memoria/memories.json:3116` — quebravam o print.

## Causa raiz
O Context Loader é o único módulo de runtime que imprime conteúdo da memória
sem sanitização. O preflight não detecta porque não exercita o loader com
memórias que contêm símbolos não-cp1252.

## Correção
Em `scripts/runtime_context.py`, logo após os imports:

```python
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
```

Padrão já consolidado no ecossistema (ver `scripts/lg_pair_tv.py:15`).

## Validação
- `python scripts/runtime_context.py "preflight runtime erro"` → renderiza as 5
  memórias relevantes (incluindo a de @
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]