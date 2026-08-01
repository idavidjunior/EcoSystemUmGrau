---
tags: [bug, lerauditoria]
aliases: [Executor.results sem limite — memoria crescia indefinidament]
date: 2026-08-01
---

# Bug: Executor.results sem limite — memoria crescia indefinidamente

**Projeto:** ler_auditoria

## Causa Raiz
results dict acumulava resultados sem nunca remover entradas antigas

## Correcao
MAX_RESULTS=50, remove entrada mais velha ao estourar.
