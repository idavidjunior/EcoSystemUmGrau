---
tags: [heuristica, efficiency]
aliases: [30s regra de timeout maximo]
date: 2026-07-27
---

# 30s regra de timeout maximo

**Dominio:** efficiency | **Fonte:** session

Nenhuma operacao de navegacao deve esperar mais que 30s. Se algo demora mais que isso, algo esta quebrado (rede, servidor, loop infinito). Fail fast, nao espere
