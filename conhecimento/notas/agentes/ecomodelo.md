---
tags: [agente, comando, modelo, llm]
aliases: [EcoModelo]
date: 2026-09-12
---

# ecomodelo — Modelo/LLM do Ecossistema

**Categoria:** agentes
**Fonte:** config/agents/ecomodelo.md

## Papel

Gerencia fallback de modelos LLM (NVIDIA → OpenAI → Anthropic) e seleção de modelo por tarefa.

## Gatilho

Uso interno / configuração de fallback

## Responsabilidades

- Roteamento por modelo (cost-aware)
- Fallback inteligente (primário → backups)
- Cache semântico de respostas
- Budget de tokens por tarefa

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[cost-aware-llm-pipeline]] — pipeline custo-consciente
- [[llm-router]] — roteador de LLM
- [[nvidia-api]] — chave NVIDIA
- [[opencode-model-fallback]] — config de fallback