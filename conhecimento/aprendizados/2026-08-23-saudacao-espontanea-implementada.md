---
tipo: decisao
tags: [saudacao, autoapresentacao, clausula-petrea, boot, primeira-mensagem, implementado]
data: 2026-08-23
contexto: "Cláusula pétrea de autoapresentação automática na primeira mensagem de cada sessão (AGENTS.md e Constituição) exige saudação curta (máx 3-4 linhas), espontânea, variando o tom a cada sessão, informando que EcoSystemUmGrau está ativo e operante, com leve contexto (projeto ativo, memória, pendências)."
decisao: "Implementado mecanismo de saudação espontânea automática em scripts/runtime_state.py: campo session_greeted no state.json, função generate_spontaneous_greeting() com 4 templates variados, CLI greeting/reset-greeting. Integração no ciclo de resposta: agente chama runtime_state.py greeting na primeira mensagem."
impacto: "Cumpre cláusula pétrea. Saudação variada a cada sessão com contexto real do estado restaurado."
---

## Implementação Concluída

### Alterações em `scripts/runtime_state.py`:

1. **Campo novo no estado**: `session_greeted: false` no `DEFAULT_STATE`
2. **Função `generate_spontaneous_greeting(state)`**: Gera saudação curta (3-4 linhas) com 4 templates variados:
   - Template 1: "EcoSystem no ar. {projeto} ativo — build OK no {device}. {pendencias} pendências técnicas carregadas."
   - Template 2: "Sistema operante. {projeto} rodando — {contexto}. Gaps: {gaps}."
   - Template 3: "Runtime restaurado. Memória: {mem_count} entradas, última tarefa: {last_task}. Pendências: {pendencias} abertas."
   - Template 4: "EcoSystemUmGrau ativo. {projeto} v{versao} no {device}. Checkpoint: {checkpoint}. {pendencias} itens pendentes."
3. **Função `mark_session_greeted()`**: Marca `session_greeted = true` após emitir saudação
4. **Função `reset_session_greeting()`**: Reseta para `false` (útil para testes/nova sessão)
5. **CLI novo**: `python scripts/runtime_state.py greeting` e `python scripts/runtime_state.py reset-greeting`

### Exemplos de saída (variam a cada sessão):

```
EcoSystemUmGrau ativo. JunkScanner v2.1 no MIUI. Checkpoint: 20260822_225138. 5 itens pendentes.
```

```
Sistema operante. JunkScanner rodando — scan ativo. Gaps: SQLite incremental, scan por data, exportação.
```

```
Runtime restaurado. Memória: 1 entradas, última tarefa: Modo AUTO do gate validado com testes adversariais; limpeza pos-push; resgate do ler-runtime com repo novo no GitHub. Pendências: 5 abertas.
```

### Integração no Ciclo de Resposta do Agente

O agente deve, na **primeira mensagem de cada sessão**:
1. Executar silenciosamente: `python scripts/runtime_state.py greeting`
2. Se retornar saudação (não `[INFO] sessão já saudada`), **iniciar a resposta com essa saudação**
3. Depois da saudação, atender o pedido normalmente

Isso cumpre o fluxo obrigatório da cláusula pétrea:
> 1. Executar silenciosamente: `python scripts/runtime_boot.py --check`
> 2. Se integridade OK: iniciar a resposta com uma confirmação **CURTA e ESPONTÂNEA (máximo 3-4 linhas)**, variando o tom a cada sessão...
> 3. Depois da confirmação curta, atender o pedido normalmente
