---
tipo: decisao
tags: [kernel, direct, tool-orchestrator, cognitive-core]
data: 2026-09-04
contexto: Tarefas LOW eram apenas marcadas como não implementadas.
decisão: Executar DIRECT somente quando a intenção exigir ferramenta e houver mapeamento MCP conhecido; pedidos informativos retornam needs_response.
impacto: Ações simples de arquivo passam pelo Tool Orchestrator com retry, timeout e rastreabilidade, sem declarar sucesso para pedidos sem execução.
---

O executor DIRECT reutiliza o mapeamento existente do planner e não cria um segundo registro de ferramentas. A raiz do repositório é adicionada ao sys.path para compatibilidade com o cognitive_core quando o kernel é executado pela CLI.

Validação: oito testes focados, execução informativa com status needs_response e listagem real de arquivos com mcp-dev-tools.list_files.
