---
name: compreensao-pedidos
description: "Use for ANY user request to turn it into a structured action plan before executing: extract goal, explicit actions, concepts, constraints, ambiguities, success criteria, waste risks and suggested plan. Trigger keywords: 'compreender pedido', 'entender pedido', 'analisar pedido', 'qual o objetivo', 'o que o usuário quer', 'pedido ambíguo', 'refinar entendimento', 'detectar desperdício'. Fast static analysis (stdlib, no LLM) with optional fail-soft LLM refinement."
---

# Compreensão de Pedidos

Antes de executar qualquer pedido, compreende o que o usuário realmente quer:
objetivo, ações esperadas, contexto, conceitos, restrições, ambiguidades,
critérios de sucesso, riscos de desperdício e plano sugerido.

## Quando usar

- Início de tarefa: entender o pedido antes de agir.
- Pedidos vagos, ambíguos ou com múltiplas ações.
- Antes de decidir se algo é executável ou precisa de esclarecimento.
- Para detectar desperdício (repetição, escopo creep, sem entregável claro).

## Como usar

### 1. CLI (rápido, estático, sem LLM)

```bash
python "mcp/nucleo/habilidades/compreensao-pedidos/compreensao.py" "<pedido>" --json
```

Campos retornados: `objetivo`, `acoes` (verbo/categoria/objeto em ordem),
`conceitos` (projetos/skills/scripts conhecidos + termos), `restricoes`,
`ambiguidades` (tipo/custo/msg), `criterios_sucesso`, `riscos` (tipo/nivel/msg),
`plano_sugerido`, `score_entendimento` (0-100), `julgamento`
(`CLARO` / `PARCIALMENTE_CLARO` / `AMBIGUO`).

### 2. Refino opcional com LLM (fail-soft, agnóstico)

```bash
python "mcp/nucleo/habilidades/compreensao-pedidos/compreensao.py" "<pedido>" --refinar --json
```

- Primária: a LLM padrão do opencode (mesma da sessão, via `opencode run --agent
  compreensao-refino`). Quando não responde, os backups entram em ação (resiliência):
  NVIDIA → OpenAI → Anthropic.
- Chaves de backup vêm SÓ de `scripts/.env` (nunca de `.env.example`).
- Modelo primário configurável via `COMPREENSAO_MODELO_OPENCODE` (default `opencode/big-pickle`);
  modelo NVIDIA via `COMPREENSAO_MODELO_NVIDIA`.
- Se a LLM primária e os backups falharem, retorna
  `llm_refino.usado: false` com o motivo — a compreensão estática NUNCA falha.

### 3. Via MCP server `mcp-compreensao-pedidos` (5 tools)

| tool | função |
|---|---|
| `compreender_pedido` | compreensão completa (objetivo, ações, conceitos, ambiguidades, score) |
| `avaliar_clareza` | score 0-100 + julgamento + ambiguidades |
| `refinar_entendimento` | compreensão completa + UMA chamada de LLM (fail-soft) |
| `resolver_conceitos` | resolve termos contra memória/skills/projetos/scripts |
| `detectar_desperdicio` | repetição de tarefa + escopo creep + sem entregável |

## Regras de uso

1. **Se `julgamento == AMBIGUO` ou `score < 60`:** pergunte/esclareça antes de
   executar, citando as `ambiguidades` e seu custo. Nunca "adivinhar".
2. **Se `detectar_desperdicio.repeticao.possivel`:** confira se a tarefa já foi
   feita (memória/state) antes de refazer.
3. **Se `riscos` listar `ESCOPO_CREEP` ou `SEM_ENTREGAVEL_CLARO`:** combine o
   escopo com o usuário antes de ampliar.
4. **Use `criterios_sucesso` e `plano_sugerido`** como contrato da execução —
   são o que o Kernel valida na saída.
5. O núcleo é 100% stdlib e instantâneo; o refino LLM é sempre opcional e nunca
   bloqueia. Não espere LLM para entender pedidos simples.
