# Planner Agent — MCP Server

## Como usar
Servidor MCP que coordena tarefas complexas: decompose, executa via outros MCPs, faz replan em falhas.

```bash
# Testar servidor
python mcp/nucleo/habilidades/planner/server.py
# → espera JSON-RPC no stdio
```

## Tools disponíveis

| Tool | Descrição |
|------|-----------|
| `create_plan` | Recebe goal + contexto, retorna plano JSON com subtasks, dependências, agentes sugeridos |
| `execute_plan` | Executa plano chamando MCPs apropriados para cada subtask (simulado) |
| `replan_on_failure` | Atualiza plano quando step falha: adiciona recovery step + ajusta dependências |

## Integração no opencode.jsonc

```jsonc
{
  "mcp": {
    "servers": {
      "planner": {
        "command": "python",
        "args": ["mcp/nucleo/habilidades/planner/server.py"],
        "env": {}
      }
    }
  }
}
```

## Fluxo de uso

1. **Kernel detecta complexidade HIGH** → chama `mcp-planner:create_plan`
2. **Planner retorna JSON** com steps ordenados topologicamente:
   ```json
   {
     "goal": "pesquise startups IA SP, salve CSV, faça gráfico",
     "steps": [
       {"id": "1", "agent": "BrowserAgent", "task": "Pesquisar startups IA SP 2024", "need": null, "mcp_suggested": "mcp-internet"},
       {"id": "2", "agent": "FileAgent", "task": "Salvar em startups.json", "need": ["1"], "mcp_suggested": "mcp-desenvolvimento"},
       {"id": "3", "agent": "CoderAgent", "task": "Gerar CSV + gráfico matplotlib", "need": ["2"], "mcp_suggested": "mcp-desenvolvimento"}
     ]
   }
   ```
3. **Kernel/Orquestrador** executa steps em ordem, passando resultados via `need`
4. **Se step falha** → chama `replan_on_failure` → adiciona step de retry + ajusta dependências

## Estrutura do Plano

```json
{
  "goal": "string",
  "steps": [
    {
      "id": "string",
      "agent": "BrowserAgent|CoderAgent|FileAgent|CasualAgent",
      "task": "descrição clara da subtask",
      "need": ["id_step_anterior"] | null,
      "mcp_suggested": "mcp-internet|mcp-desenvolvimento|mcp-comportamentais",
      "status": "pending|running|done|failed",
      "is_recovery": false
    }
  ],
  "metadata": {"total_steps": 3, "created_by": "mcp-planner"}
}
```

## Exemplo via MCP

```json
// Criar plano
{"method": "tools/call", "params": {"name": "create_plan", "arguments": {
  "goal": "Pesquisar startups de IA em São Paulo, salvar em CSV, fazer gráfico",
  "context": "Usuário quer dados atuais 2024",
  "constraints": "Apenas fontes públicas, sem API key",
  "success_criteria": "CSV válido + gráfico PNG"
}}}

// Replanar após falha
{"method": "tools/call", "params": {"name": "replan_on_failure", "arguments": {
  "plan": {...},
  "failed_step_id": "2",
  "error": "Permission denied writing startups.json",
  "partial_results": {"1": {...}}
}})
```

## Dependências
- Python stdlib + `scripts/runtime_kernel` (complexity_classifier)
- `scripts/llm_router` para chamada LLM (fallback template se indisponível)
- `scripts/tool_orchestrator` para execução real (futuro)

## Integração no Kernel

O `runtime_kernel.py` usa automaticamente:
- `complexity_classifier.classify(goal)` → LOW/HIGH
- Se HIGH → `kernel._call_planner()` via MCP stdio
- Roteamento: `DIRECT` (LOW) vs `PLANNER_AGENT` (HIGH)