---
tags: [antigas, bug, entradas, estourar, lerauditoria, remover]
aliases: [Executor.results sem limite — memoria crescia indefinidament]
date: 2026-08-21
---

# Executor.results sem limite — memoria crescia indefinidamente

**Projeto:** ler_auditoria

## Causa Raiz
results dict acumulava resultados sem nunca remover entradas antigas

## Correcao
MAX_RESULTS=50, remove entrada mais velha ao estourar.
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ler]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]
- [[nao-havia-feedback-loop-do-usuario-ler-terminava-mesmo-se-ob]]
- [[score-threshold-mas-sem-failedsteps-ia-direto-para-successve]]