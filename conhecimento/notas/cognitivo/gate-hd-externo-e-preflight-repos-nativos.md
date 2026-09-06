---
tags: [cabo, cognitivo, general, novamente, reconectar, reconhecer]
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

---
tipo: episodio
tags: [hardware, hd-externo, usb, energia, diagnostico]
data: 2026-09-03
contexto: O usuário relatou que o HD externo cai e some esporadicamente, obrigando desconectar e reconectar o cabo USB para o PC reconhecer novamente.
decisao: Diagnosticado via Get-PnpDevice, powercfg e Event Log. Causa de software corrigida: suspensão seletiva USB estava ATIVADA (AC e DC). Desabilitada via powercfg (indice 0). Causas físicas apontadas mas não resolvidas.
impacto: Redução da causa mais p
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]