---
tags: [agents, cognitivo, conseguir, general, sincronizar, voltam]
aliases: [gate hd externo e preflight repos nativos]
date: 2026-08-28
---

# gate hd externo e preflight repos nativos

**Dominio:** general

Tipo: erro

Tags: [gate, persistencia, hd-externo, preflight, powershell]

Data: 2026-08-28

contexto: Sync apos controles de narracao no widget Edge. Gate persistencia.ps1 travava espelho do HD externo e repos nativos.

decisao: Corrigir bug de continuacao de linha PowerShell no filtro $hdBloqueio (mover '-and' para o fim da linha); Invoke-PreflightGlobal passa a pular preflight quando scripts/preflight_check.py nao existe (em vez de bloquear); identidade git local configurada no repo claude-code-extra-agents.

impacto: HD externo volta a ser espelhado apos push do eco (bug fix). Repos sem harness de preflight (ler-runtime, SupermarketCalculator, claude-code-extra-agents) voltam a conseguir sincronizar.
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]