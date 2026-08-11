---
tipo: erro
tags: [runtime, unicode, windows, cp1252, runtime_context]
data: 2026-08-08
contexto: Verificação de preflight + busca de erro no runtime (pedido do módulo de compreensão de pedidos).
decisao: Adicionar sys.stdout.reconfigure(encoding='utf-8', errors='replace') em scripts/runtime_context.py, mesmo padrão já usado em scripts/lg_pair_tv.py.
impacto: Context Loader voltou a renderizar contexto sem crash; caracteres como ↔ (U+2194) presentes na memória (@sync) agora imprimem corretamente.
---

# Erro: UnicodeEncodeError no runtime_context (cp1252)

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
  memórias relevantes (incluindo a de @sync com `↔`) sem erro.
- Preflight continua passando.

## Conexoes

- [[cluster-hub-programacao]]