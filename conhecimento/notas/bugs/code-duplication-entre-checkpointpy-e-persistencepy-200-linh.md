---
tags: [bug, identica, json, lerauditoria, logica, read]
aliases: [Code duplication entre checkpoint.py e persistence.py (~200 ]
date: 2026-08-20
---

# Code duplication entre checkpoint.py e persistence.py (~200 linhas duplicadas)

**Projeto:** ler_auditoria

## Causa Raiz
Duas implementacoes paralelas de save/load JSON com logica identica

## Correcao
Unificado via atomic_write_json()/atomic_read_json() em checkpoint.py, persistence.py delega.
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ler]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]
- [[nao-havia-feedback-loop-do-usuario-ler-terminava-mesmo-se-ob]]
- [[score-threshold-mas-sem-failedsteps-ia-direto-para-successve]]