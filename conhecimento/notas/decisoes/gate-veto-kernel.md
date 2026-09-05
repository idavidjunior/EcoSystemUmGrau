---
tags: [aprovada, decisao, frankestein, mcp, opencode, tool]
aliases: [gate veto kernel]
date: 2026-09-02
---

# gate veto kernel

**Fonte:** opencode

Tipo: decisao

Tags: [gate, veto, kernel, governanca, roteamento, compreensao-pedidos]

Data: 2026-09-02

contexto: Fase 2 do mecanismo de governanca — integrar o gate de veto no roteamento do kernel, apos a Fase 1 (gerar_checklist + tool MCP veto_pedido) aprovada.

decisao: Adicionar o metodo gate_veto ao kernel (scripts/runtime_kernel.py) e chamar no route_task, logo apos authorize. Pedidos que disparam regra de veto retornam route BLOQUEADO antes de rotear. execute_plan trata BLOQUEADO sem crash. Reutiliza gerar_checklist do modulo compreensao via importlib (mesmo padrao que o kernel ja usava para compreender) — sem duplicar a logica de vetos (anti-Frankestein).

impacto: Pedidos destrutivos (DESTRUICAO) ou de sincronizacao de git sem o gate (SINCRONIZAR_GIT) sao bloqueados no roteamento. Toda chamada a route_task (CLI route, execute-plan, integracoes) passa pelo gate. Fail-soft: se o modulo de compreensao estiver indisponivel, o pedido segue APROVADO (nao trava a execucao).
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]