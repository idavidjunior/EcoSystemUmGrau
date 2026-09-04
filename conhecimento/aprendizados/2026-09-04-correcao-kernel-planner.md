---
tipo: erro
tags: [kernel, constituicao, mcp, planner, jsonrpc]
data: 2026-09-04
contexto: O runtime_kernel carregava zero regras e não consumia o retorno real do mcp-planner.
decisão: Tratar a Constituição como fonte normativa, aceitar seus formatos reais e centralizar o parsing MCP.
impacto: O kernel passou a carregar sete regras, criar planos HIGH e propagar falhas do planner.
---

O parser da Constituição dependia de um cabeçalho Markdown inexistente e de regras numeradas. O planner também era chamado dentro de um event loop usando asyncio.run, causando falha imediata.

Foram corrigidos o carregamento da seção normativa, o contrato de resposta MCP, a fronteira assíncrona, o sucesso falso em subprocessos, o replanejamento de steps concluídos, as dependências e o veto fail-closed.

Validação: py_compile, boot do runtime, CLI plan e cinco testes focados passaram.

## Conexoes

- [[sessao-focada-em-organizacao-de-workspace-unificacao-de-proj]]