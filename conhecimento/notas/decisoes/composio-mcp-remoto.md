---
tags: [decisao, gateway, opencode, streamable, uak, uso]
aliases: [composio mcp remoto]
date: 2026-08-28
---

# composio mcp remoto

**Fonte:** opencode

Tipo: decisao

Tags: [composio, mcp, opencode, remote, preflight]

Data: 2026-08-28

contexto: Integrar o Composio ao EcoSystemUmGrau via endpoint MCP remoto (streamable HTTP) com a chave de consumer do gateway.

decisao: Adicionar servidor MCP remoto "composio" no config/opencode.jsonc apontando para https://connect.composio.dev/mcp com header x-consumer-api-key usando interpolacao {env:COMPOSIO_API_KEY}. Persistir a chave via setx (HKCU Environment) e scripts/.env. Adaptar preflight_check.py para suportar type=remote.

impacto: Servidor MCP remoto valido no schema do opencode; preflight agora testa MCP remoto via urllib resolvendo {env:VAR} em headers; auth 401 do CLI (chave ck_) nao bloqueia o uso via endpoint MCP. // ---
tipo: decisao
tags: [composio, mcp, opencode, remote, preflight]
data: 2026-08-28
contexto: Integrar o Composio ao EcoSystemUmGrau via endpoint MCP remoto (streamable HTTP) com a chave de consumer do gateway.
decisao: Adicionar servidor MCP remoto "composio" no config/opencode.jsonc apontando para https://connect.composio.dev/mcp com header x-consumer-api-key usando interpolacao {env:COMPOSIO_API_KEY}. Persistir a chave via setx (HKCU Environment) e scripts/.env. Adaptar preflight_check.py para suportar type=remote.
impacto: Servidor MCP remoto valido no schema do opencode; preflight agora testa MCP remoto via urllib resolvendo {env:VAR} em headers; auth 401 do CLI (chave ck_) nao bloqueia o uso via endpoint MCP.
notas:
- Chave de consumer (ck_) NAO serve como user API key do CLI (espera uak_); usar endpoint MCP com header x-consumer-api-key.
- Endpoint exige Accept: application/json, text/event-stream + Content-Type: application/json (initialize/tools/list validados).
- Preflight: // ---
tipo: decisao
tags: [composio, mcp, opencode, remote, preflight]
data: 2026-08-28
contexto: Integrar o Composio ao EcoSystemUmGrau via endpoint MCP remoto (streamable HTTP) com a chave de consumer do gateway.
decisao: Adicionar servidor MCP remoto "composio" no config/opencode.jsonc apontando para https://connect.composio.dev/mcp com header x-consumer-api-key usando interpolacao {env:COMPOSIO_API_KEY}. Persistir a chave via setx (HKCU Environment) e scripts/.env. Adaptar preflight_check.py para suportar type=remote.
impacto: Servidor MCP remoto valido no schema do opencode; preflight agora testa MCP remoto via urllib resolvendo {env:VAR} em headers; auth 401 do CLI (chave ck_) nao bloqueia o uso via endpoint MCP.
notas:
- Chave de consumer (ck_) NAO serve como user API key do CLI (espera uak_); usar endpoint MCP com header x-consumer-api-key.
- Endpoint exige Accept: application/json, text/event-stream + Content-Type: application/json (initialize/tools/list validados).
- Preflight:
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]