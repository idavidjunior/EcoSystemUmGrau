---
tipo: erro
tags: [saudacao, autoapresentacao, clausula-petrea, boot, primeira-mensagem]
data: 2026-08-23
contexto: "Cláusula pétrea de autoapresentação automática na primeira mensagem de cada sessão (AGENTS.md e Constituição) exige saudação curta (máx 3-4 linhas), espontânea, variando o tom a cada sessão, informando que EcoSystemUmGrau está ativo e operante, com leve contexto (projeto ativo, memória, pendências)."
decisao: "Registrar erro e definir implementação: criar mecanismo de detecção de primeira mensagem + emissão automática de saudação no ciclo de resposta inicial."
impacto: "Sem a saudação, o usuário não recebe confirmação visual/operacional de que o ecossistema bootou corretamente. Viola cláusula pétrea."
---

## Problema

A cláusula pétrea **AUTOAPRESENTAÇÃO AUTOMÁTICA NA PRIMEIRA MENSAGEM DE CADA SESSÃO** não está sendo cumprida. O fluxo atual:

1. Usuário abre nova sessão
2. Agente responde direto ao pedido
3. **FALTA**: saudação espontânea curta confirmando operacionalidade

## Requisito da Cláusula

> Fluxo obrigatório na primeira mensagem de qualquer sessão (antes de atender o pedido):
> 1. Executar silenciosamente: `python scripts/runtime_boot.py --check`
> 2. Se integridade OK: iniciar a resposta com uma confirmação **CURTA e ESPONTÂNEA (máximo 3-4 linhas)**, variando o tom a cada sessão, informando que o EcoSystemUmGrau está ativo e operante. Incluir leve contexto (projeto ativo, memória, pendências) quando disponível.
> 3. Se houver problema de integridade: informar brevemente o que falhou e o que foi corrigido antes de atender o pedido.
> 4. Depois da confirmação curta, atender o pedido normalmente.

## Implementação Necessária

Criar hook/mecanismo que:
1. Detecte primeira mensagem da sessão (flag em `runtime/state.json` ou variável de sessão)
2. Execute `python scripts/runtime_boot.py --check` silenciosamente
3. Se OK: gere saudação curta variada (ex: 3-4 templates rotativos) com contexto leve do `state.json`
4. Marque sessão como "iniciada" para não repetir
5. Integre no ciclo de resposta do agente (kernel → response)

## Exemplos de Saudações Variadas

- "EcoSystem no ar. JunkScanner v2.1 build OK no MIUI. 5 pendências técnicas carregadas."
- "Sistema operante. Projeto JunkScanner ativo — scan 3220 itens, gaps: SQLite incremental, Shizuku opcional."
- "Runtime restaurado. Memória: 396 entradas, última tarefa: modo AUTO gate validado. Pendências: 5 abertas."