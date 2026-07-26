---
name: cost-aware-llm-pipeline
description: |
  Pipeline de LLM orientado a custo: roteamento por modelo, caching semântico, limites de tokens e observabilidade financeira.
  Trigger phrases: "LLM cost", "token budget", "model routing", "optimize inference"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Cost-Aware LLM Pipeline — Custo sem Perder Qualidade

## Objetivo
Maximizar qualidade por dólar com arquitetura de inferência escalonada e mensurável.

## Estratégia em camadas
1. Pré-filtro com regras simples/heurísticas
2. Modelo barato para classificação/triagem
3. Escalada para modelo premium só quando necessário
4. Pós-processamento determinístico para validação

## Técnicas-chave
- Prompt compression e deduplicação de contexto
- Caching por embedding + invalidação por versão
- Budget de tokens por request e por sessão
- Batching assíncrono quando latência permite
- Limites por cliente, endpoint e feature

## Métricas obrigatórias
- Custo por request
- Custo por usuário ativo
- Taxa de fallback para modelo caro
- Latência p95 por rota
- Taxa de retrabalho humano pós-resposta

## Guardrails
- Hard cap de tokens e timeout
- Kill-switch por feature cara
- Alertas de desvio de custo diário
- Testes de regressão de qualidade por mudança de prompt

## Anti-patterns
- Usar modelo topo para todo tráfego
- Não versionar prompts/modelos
- Otimizar custo sem monitorar qualidade
- Misturar dados de tenants no cache

## Saída esperada do agente
- Desenho de roteamento por classe de tarefa
- Orçamento de custo por ambiente
- Regras de fallback/degradação
- Dashboard mínimo de FinOps para LLM