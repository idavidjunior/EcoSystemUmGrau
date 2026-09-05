---
tags: [decisao, nele, opencode, operar, pedir, tenha]
aliases: [Atualização: EcoSystemUmGrau Auto-Carregamento + Gatilho Úni]
date: 2026-08-08
---

# Atualização: EcoSystemUmGrau Auto-Carregamento + Gatilho Único "Eco"

**Fonte:** opencode

## Pedido do usuário

1. **Auto-carregamento total:** "A cada nova sessão que eu abrir, você pode carregar sozinho, automaticamente e imediatamente o EcoSystemUmGrau e operar nele sem que eu tenha que pedir?"
2. **Gatilho simplificado:** "A cada nova sessão que eu falar ou digitar Eco, imediatamente o protocolo de operação será ativado."

## Implementação

### 1. Carregamento automático total (nova sessão)

Adicionada à Constituição a seção **"CARREGAMENTO AUTOMÁTICO TOTAL — ECO SYSTEM"** dentro da cláusula pétrea. Todo agente, ao iniciar qualquer sessão, deve:

1. **Boot via `runtime_boot.py`** — verifica integridade, restaura estado, carrega memória
2. **Estado persistente** de `runtime/state.json` (projeto ativo, objetivo, última tarefa, pendências)
3. **Memória episódica** via `memory_engine` (memórias consolidadas relevantes)
4. **Kernel permanente** (7 regras absolutas, pipeline 9 etapas)
5. **Context Loader** (`runtime_context.py`) — BM25 semântico, carrega apenas o relevante
6.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]