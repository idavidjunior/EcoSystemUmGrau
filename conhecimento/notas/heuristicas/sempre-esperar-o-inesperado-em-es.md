---
tags: [heuristica, systemdesign]
aliases: [Sempre esperar o inesperado em E/S]
date: 2026-07-27
---

# Sempre esperar o inesperado em E/S

**Dominio:** system_design | **Fonte:** meta_cognition

Toda operacao de E/S (rede, disco, banco) pode falhar. Sempre tenha: timeout, retry com backoff, fallback, e log do erro. Nao existe excecao 'que nunca acontece' em E/S.
