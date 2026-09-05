---
tags: [apache, numa, opencode, padrao, resposta, trava]
aliases: [TradingAgents integrado ao ecossistema]
date: 2026-08-22
---

# TradingAgents integrado ao ecossistema

**Fonte:** opencode

## Contexto
Usuário indicou o framework TauricResearch/TradingAgents (99 mil estrelas, Apache-2.0)
para análise financeira multi-agente. Objetivo: usar com as chaves que o ecossistema
já possui, sem custo novo.

## Decisão
Clonado em Projetos/TradingAgents com venv próprio (Python 3.12). Uso do provedor
nativo "nvidia" (endpoint integrate.api.nvidia.com/v1) com NVIDIA_API_KEY existente.
Modelos: meta/llama-3.1-8b-instruct (quick) e meta/llama-3.1-70b-instruct (deep).
Runner run_eco.py: benchmark ^BVSP para tickers .SA, output_language Portuguese,
checkpoint_enabled True.

## Armadilhas resolvidas
1. Multi tool-calls: endpoints NVIDIA NIM geram várias chamadas numa resposta e depois
   recusam o replay ("This model only supports single tool-calls at once"). O parâmetro
   parallel_tool_calls=False não é honrado e ainda trava o endpoint. Solução estável:
   monkeypatch no BaseChatOpenAI._generate mantendo apenas o primeiro tool_call.
2. system_guardian: mata o maior processo python quand
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]