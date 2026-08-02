---
tags: [heuristica, persistence]
aliases: [Escrita atomica sempre]
date: 2026-08-01
---

# Escrita atomica sempre

**Dominio:** persistence | **Fonte:** meta_cognition

Qualquer escrita em arquivo que importa: tmp + rename atomico. Nao importa o quao trivial parece. Um crash no meio do json.dump corrompe o arquivo e voce perde tudo.
## Conexoes

- [[cluster-hub-cognicao]]
- [[heuristica-hub-heuristicas]]