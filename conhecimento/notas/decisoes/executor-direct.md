---
tags: [arquivos, decisao, dev, opencode, sucesso, tools]
aliases: [executor direct]
date: 2026-09-04
---

# executor direct

**Fonte:** opencode

---
tipo: decisao
tags: [kernel, direct, tool-orchestrator, cognitive-core]
data: 2026-09-04
contexto: Tarefas LOW eram apenas marcadas como não implementadas.
decisão: Executar DIRECT somente quando a intenção exigir ferramenta e houver mapeamento MCP conhecido; pedidos informativos retornam needs_response.
impacto: Ações simples de arquivo passam pelo Tool Orchestrator com retry, timeout e rastreabilidade, sem declarar sucesso para pedidos sem execução.
---

O executor DIRECT reutiliza o mapeamento existente do planner e não cria um segundo registro de ferramentas. A raiz do repositório é adicionada ao sys.path para compatibilidade com o cognitive_core quando o kernel é executado pela CLI.

Validação: oito testes focados, execução informativa com status needs_response e listagem real de arquivos com mcp-dev-tools.list_files. // ---
tipo: decisao
tags: [kernel, direct, tool-orchestrator, cognitive-core]
data: 2026-09-04
contexto: Tarefas LOW eram apenas marcadas como não implementadas.
decisão: Executar DIRECT somente quando a intenção exigir ferramenta e houver mapeamento MCP conhecido; pedidos informativos retornam needs_response.
impacto: Ações simples de arquivo passam pelo Tool Orchestrator com retry, timeout e rastreabilidade, sem declarar sucesso para pedidos sem execução.
---

O executor DIRECT reutiliza o mapeamento existente do planner e não cria um segundo registro de ferramentas. A raiz do repositório é adicionada ao sys.path para compatibilidade com o cognitive_core quando o kernel é executado pela CLI.

Validação: oito testes focados, execução informativa com status needs_response e listagem real de arquivos com mcp-dev-tools.list_files.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]