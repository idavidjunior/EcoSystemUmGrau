---
tags: [cognitivo, compreensão, general, módulo, pedido, pedidos]
aliases: [Erro: UnicodeEncodeError no runtime_context (cp1252)]
date: 2026-08-23
---

# Erro: UnicodeEncodeError no runtime_context (cp1252)

**Dominio:** general

---
tipo: erro
tags: [runtime, unicode, windows, cp1252, runtime_context]
data: 2026-08-08
contexto: Verificação de preflight + busca de erro no runtime (pedido do módulo de compreensão de pedidos).
decisao: Adicionar sys.stdout.reconfigure(encoding='utf-8', errors='replace') em scripts/runtime_context.py, mesmo padrão já usado em scripts/lg_pair_tv.py.
impacto: Context Loader voltou a renderizar contexto sem crash; caracteres como ↔ (U+2194) presentes na memória (@sync) agora imprimem corretame
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]