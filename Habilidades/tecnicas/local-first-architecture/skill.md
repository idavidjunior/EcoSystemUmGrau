---
name: local-first-architecture
description: |
  Arquiteturas local-first/offline-first com sincronização, resolução de conflitos e UX resiliente.
  Trigger phrases: "local first", "offline first", "sync", "CRDT"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Local-First Architecture — Produto Funciona Mesmo Offline

## Objetivo
Priorizar experiência instantânea local com sincronização confiável quando houver conectividade.

## Princípios
- Escrita local imediata
- Sync assíncrono e robusto
- Resolução de conflito explícita
- Transparência de estado online/offline

## Estratégias de sincronização
- Last-write-wins apenas para casos simples
- CRDT/OT para colaboração concorrente
- Filas de operações com retry idempotente
- Version vectors quando necessário

## UX essencial
- Indicador de status de sync
- Feedback de conflito com opção de merge
- Persistência local durável
- Recuperação após reconexão

## Checklist
- App mantém valor funcional offline?
- Conflitos são detectados e explicados?
- Sync evita duplicidade/corrupção?
- Criptografia local cobre dados sensíveis?

## Anti-patterns
- Bloquear escrita sem internet
- Resolver conflito silenciosamente sem auditabilidade
- Estado local efêmero sem backup
- Sync sem limites/retry controlado

## Saída esperada do agente
- Modelo de dados local + sync
- Política de conflito por entidade
- Métricas de consistência e sucesso de sync
- Plano de testes offline/reconexão