---
tags: [heuristica, architecture]
aliases: [State deve ser explícito, nunca implícito]
date: 2026-07-29
---

# State deve ser explícito, nunca implícito

**Dominio:** architecture | **Fonte:** meta_cognition

Se um componente tem estado (ativo/inativo, conectado/desconectado, editando/visualizando), represente-o como UMA variavel booleana ou enum, nao como combinacao de multiplos sinais. State implicito (ex: 'se alpha=0 e visibility=GONE entao ta oculto') e fonte de bugs.
