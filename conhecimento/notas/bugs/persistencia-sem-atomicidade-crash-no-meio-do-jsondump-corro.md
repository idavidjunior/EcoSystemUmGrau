---
tags: [bug, lerauditoria]
aliases: [Persistencia sem atomicidade — crash no meio do json.dump co]
date: 2026-07-30
---

# Bug: Persistencia sem atomicidade — crash no meio do json.dump corrompia arquivo

**Projeto:** ler_auditoria

## Causa Raiz
Escrita direta com json.dump() sem arquivo temporario

## Correcao
Todas escritas usam arquivo .tmp + os.replace() (atomico em ext4/NTFS).
