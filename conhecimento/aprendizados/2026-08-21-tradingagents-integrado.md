---
tipo: padrao
tags: [tradingagents, nvidia, multi-agente, financas, tool-calling]
data: 2026-08-21
---

# TradingAgents integrado ao ecossistema

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
2. system_guardian: mata o maior processo python quando a RAM livre cai abaixo de
   ~450MB — derrubava a análise no meio (exit code 15 silencioso). Pausar com
   guardian_manager.ps1 stop antes de rodar e start ao final.
3. pip install interrompido morre sem log claro; conferir sempre com pip show.

## Impacto
Análise multi-agente completa de qualquer ticker do Yahoo Finance rodando de graça
com a chave NVIDIA existente. Primeira execução: PETR4.SA → decisão Hold.

## Limitação honesta
Modelos gratuitos da NVIDIA alucinam nas tabelas anuais dos relatórios textuais
(os dados vindos das tools yfinance são reais; a síntese textual pode fabricar números).
Tratar saída como pesquisa estruturada, nunca como dado auditado.
