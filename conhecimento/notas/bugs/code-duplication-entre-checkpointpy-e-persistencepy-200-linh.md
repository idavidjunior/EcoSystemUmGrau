---
tags: [bug, lerauditoria]
aliases: [Code duplication entre checkpoint.py e persistence.py (~200 ]
date: 2026-07-27
---

# Bug: Code duplication entre checkpoint.py e persistence.py (~200 linhas duplicadas)

**Projeto:** ler_auditoria

## Causa Raiz
Duas implementacoes paralelas de save/load JSON com logica identica

## Correcao
Unificado via atomic_write_json()/atomic_read_json() em checkpoint.py, persistence.py delega.
