---
name: api-design
description: |
  Design de APIs HTTP/REST com contratos consistentes, versionamento, erros previsíveis e foco em evolutividade.
  Trigger phrases: "API design", "REST", "endpoint contract", "versioning"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# API Design — Contratos Claros e Evolutivos

## Objetivo
Criar APIs fáceis de consumir, difíceis de quebrar e simples de operar.

## Princípios de contrato
- Recursos nomeados por domínio (`/orders`, `/invoices`)
- Semântica HTTP coerente (GET/POST/PATCH/DELETE)
- Esquemas de request/response versionados
- Erros padronizados com código, mensagem e contexto

## Boas práticas
- Paginação consistente (cursor preferível para alta escala)
- Idempotency keys em operações críticas
- Campos opcionais com defaults explícitos
- Filtros e ordenação documentados

## Versionamento e compatibilidade
- Evitar breaking changes silenciosas
- Deprecar com prazo e comunicação
- Backward compatibility como padrão
- Contract tests entre producer/consumer

## Segurança e operação
- Autenticação/autorização por escopo
- Rate limit por cliente/rota
- Observabilidade por endpoint (latência, erro, saturação)
- Trace ID propagado ponta a ponta

## Anti-patterns
- Endpoint "faz tudo" sem coesão
- Erros ambíguos sem ação para cliente
- Mudança de contrato sem versionar
- Falta de limites em payload/query

## Saída esperada do agente
- Especificação de endpoint (input/output/errors)
- Regras de versionamento e depreciação
- Checklist de segurança e observabilidade
- Plano de testes de contrato