---
tags: [cognitivo, fim, general, hdbloqueio, linha, mover]
aliases: [gate hd externo e preflight repos nativos]
date: 2026-08-28
---

# gate hd externo e preflight repos nativos

**Dominio:** general

---
tipo: erro
tags: [gate, persistencia, hd-externo, preflight, powershell]
data: 2026-08-28
contexto: Sync apos controles de narracao no widget Edge. Gate persistencia.ps1 travava espelho do HD externo e repos nativos.
decisao: Corrigir bug de continuacao de linha PowerShell no filtro $hdBloqueio (mover '-and' para o fim da linha); Invoke-PreflightGlobal passa a pular preflight quando scripts/preflight_check.py nao existe (em vez de bloquear); identidade git local configurada no repo claude-co
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]