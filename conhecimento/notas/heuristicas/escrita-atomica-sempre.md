---
tags: [heuristica, persistence]
aliases: [Escrita atomica sempre]
date: 2026-07-27
---

# Escrita atomica sempre

**Dominio:** persistence | **Fonte:** meta_cognition

Qualquer escrita em arquivo que importa: tmp + rename atomico. Nao importa o quao trivial parece. Um crash no meio do json.dump corrompe o arquivo e voce perde tudo.
