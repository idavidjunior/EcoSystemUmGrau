---
tags: [bug, crash, json, lerauditoria, meio, projeto]
aliases: [Persistencia sem atomicidade — crash no meio do json.dump co]
date: 2026-07-28
---

# Persistencia sem atomicidade — crash no meio do json.dump corrompia arquivo

**Projeto:** ler_auditoria

## Causa Raiz
Escrita direta com json.dump() sem arquivo temporario

## Correcao
Todas escritas usam arquivo .tmp + os.replace() (atomico em ext4/NTFS).
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ler]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]
- [[nao-havia-feedback-loop-do-usuario-ler-terminava-mesmo-se-ob]]
- [[score-threshold-mas-sem-failedsteps-ia-direto-para-successve]]