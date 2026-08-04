---
name: multi-modal-ai
description: |
  Soluções multimodais com texto, imagem, áudio e vídeo: ingestão, roteamento, segurança e avaliação de qualidade.
  Trigger phrases: "multimodal", "vision", "speech", "whisper", "image analysis"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Multi-Modal AI — Orquestração de Modalidades com Qualidade

## Objetivo
Combinar modalidades de entrada/saída para resolver tarefas que texto puro não cobre bem.

## Pipeline típico
1. Ingestão (imagem/áudio/vídeo/documento)
2. Pré-processamento (normalização, chunking, limpeza)
3. Inferência por modalidade
4. Fusão de evidências
5. Resposta final com confiança e rastreabilidade

## Padrões recomendados
- Roteamento por tipo de tarefa/modalidade
- Fallback para texto quando mídia falhar
- Armazenar artefatos e metadados separadamente
- Guardrails para conteúdo sensível

## Avaliação
- Métricas por modalidade (WER, precisão visual, factualidade)
- Taxa de inconsistência entre modalidades
- Latência e custo por fluxo
- Revisão humana para casos de alto impacto

## Segurança e privacidade
- Redação de PII em áudio/imagem quando possível
- Política de retenção de mídia
- Controles de acesso por sensibilidade
- Filtro de conteúdo indevido

## Anti-patterns
- Tratar todas modalidades com mesmo prompt/fluxo
- Não versionar modelos por modalidade
- Ignorar qualidade da captura de entrada
- Sem fallback em falha de codec/upload

## Saída esperada do agente
- Arquitetura multimodal por etapa
- Estratégia de avaliação por modalidade
- Guardrails de segurança e privacidade
- Plano de rollout com custo/latência