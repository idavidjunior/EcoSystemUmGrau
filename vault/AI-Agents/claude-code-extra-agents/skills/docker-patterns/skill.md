---
name: docker-patterns
description: |
  Padrões Docker para build reproduzível, imagem mínima, segurança e deploy previsível.
  Trigger phrases: "Dockerfile", "containerizar", "imagem", "multi-stage"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Docker Patterns — Build Seguro e Reproduzível

## Objetivo
Criar imagens pequenas, seguras e determinísticas para dev, CI e produção.

## Práticas essenciais
- Multi-stage build com separação `build`/`runtime`
- Base image enxuta e atualizada
- Usuário não-root no runtime
- `.dockerignore` rigoroso
- Dependências travadas por versão/hash

## Dockerfile checklist
- Ordem otimizada para cache?
- Não copia segredos para camada?
- Healthcheck definido?
- Entry point explícito?
- Porta/documentação coerentes?

## Segurança
- Scan de vulnerabilidades no CI
- Assinatura e provenance quando possível
- Evitar `latest` em produção
- Menor superfície: remover tools de build da imagem final

## Operação
- Logs em stdout/stderr
- Config via env vars (12-factor)
- Limits de CPU/memória documentados
- Estratégia de graceful shutdown

## Anti-patterns
- Um container com múltiplos processos críticos
- Copiar repositório inteiro sem necessidade
- Rodar como root por padrão
- Build não reprodutível por dependências flutuantes

## Saída esperada do agente
- Dockerfile revisado com racional
- Lista de hardenings aplicáveis
- Regras de CI para build/scan/publish
- Guia de execução local e produção