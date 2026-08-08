---
tags: [architecture, combinacao, heuristica, multiplos, nao, sinais]
aliases: [State deve ser explícito, nunca implícito]
date: 2026-08-08
---

# State deve ser explícito, nunca implícito

**Dominio:** architecture | **Fonte:** meta_cognition

Se um componente tem estado (ativo/inativo, conectado/desconectado, editando/visualizando), represente-o como UMA variavel booleana ou enum, nao como combinacao de multiplos sinais. State implicito (ex: 'se alpha=0 e visibility=GONE entao ta oculto') e fonte de bugs.
## Conexoes

- [[cluster-hub-cognicao]]
- [[heuristica-hub-heuristicas]]
- [[lei-de-postel-aplicada-a-engenharia]]
- [[projete-para-falha-nao-para-sucesso]]