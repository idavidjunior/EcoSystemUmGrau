---
tags: [agente, comando, sincronizacao, git]
aliases: [Sync]
date: 2026-09-12
---

# sync — Sincronização Forçada do EcoSystemUmGrau

**Categoria:** agentes
**Fonte:** config/agents/sync.md

## Papel

Executa o protocolo de sincronização completo (@sync): boot, constituição, deploy config, preflight técnico/ético, git status, pull+push, memory sync, checkpoint.

## Gatilho

`@sync` ou `/sync`

## Responsabilidades

- `python scripts/runtime_boot.py` — bootloader
- `python scripts/sync_rules.py audit` — 3 camadas de regras
- Deploy config opencode.jsonc
- `python scripts/preflight_check.py` — técnico
- `python scripts/preflight_etica.py` — ético
- `persistencia.ps1 status` — git status
- `persistencia.ps1 sync` — pull+push via gate
- `python scripts/memory_engine.py stats` — memory sync
- `runtime_state.py checkpoint "@sync"` — checkpoint

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[persistencia-ps1]] — gate de persistência
- [[sync-rules]] — sincronização de regras
- [[preflight-tecnico]] — preflight técnico
- [[preflight-etico]] — preflight ético
- [[clausula-sync]] — cláusula @sync