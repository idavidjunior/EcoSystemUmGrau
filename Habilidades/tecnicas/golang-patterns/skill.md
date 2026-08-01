---
name: golang-patterns
description: |
  Padrões Go para serviços robustos: contexto, concorrência segura, erros explícitos e organização idiomática.
  Trigger phrases: "golang", "go routines", "go patterns", "idiomatic go"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Golang Patterns — Go Idiomático para Produção

## Objetivo
Escrever Go simples, previsível e performático sem sacrificar legibilidade.

## Princípios
- Preferir clareza a abstração precoce
- Erros explícitos com contexto
- Interfaces pequenas, definidas no consumidor
- `context.Context` em fronteiras I/O

## Concorrência segura
- Goroutines com ownership claro
- `errgroup` para tarefas paralelas coordenadas
- Cancelamento propagado por context
- Evitar compartilhamento mutável sem necessidade

## Estrutura recomendada
- `cmd/` para entrypoints
- `internal/` para domínio privado
- `pkg/` apenas para API realmente reutilizável
- Separação clara entre transporte, domínio e infraestrutura

## Checklist de qualidade
- Race detector limpo?
- Timeouts em chamadas externas?
- Logs estruturados com correlação?
- Testes cobrindo erros e cancelamento?
- Lints (`go vet`, staticcheck) sem alertas críticos?

## Anti-patterns
- Panic para fluxo normal
- Interface genérica antecipada
- Context ignorado em operações bloqueantes
- Goroutine sem lifecycle controlado

## Saída esperada do agente
- Recomendações idiomáticas aplicáveis
- Ajustes de concorrência/contexto
- Checklist de confiabilidade Go
- Plano de testes e observabilidade