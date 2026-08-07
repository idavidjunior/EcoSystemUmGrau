---
tags: [banco, erro, falhar, heuristica, pode, systemdesign]
aliases: [Sempre esperar o inesperado em E/S]
date: 2026-08-07
---

# Sempre esperar o inesperado em E/S

**Dominio:** system_design | **Fonte:** meta_cognition

Toda operacao de E/S (rede, disco, banco) pode falhar. Sempre tenha: timeout, retry com backoff, fallback, e log do erro. Nao existe excecao 'que nunca acontece' em E/S.
## Conexoes

- [[cache-de-decisoes-caras]]
- [[cluster-hub-cognicao]]
- [[estrategia-de-fallback-em-cadeia-chain-of-responsibility]]
- [[estrategia-de-loop-autonomo-planejar-executar-verificar-corr]]
- [[heuristica-hub-heuristicas]]
- [[padrao-de-escrita-atomica-para-persistencia]]