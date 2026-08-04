---
name: state-machine-patterns
description: |
  Modelagem robusta com statecharts (XState/alternativas) para fluxos complexos.
  Inclui critérios de adoção, desenho de estados, guards/actions, observabilidade e testes.
  Trigger phrases: "state machine", "XState", "statechart", "estado finito"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# State Machine Patterns — Modelagem com XState e Statecharts

## Objetivo
Transformar fluxos implícitos e frágeis em modelos explícitos, testáveis e previsíveis.

## Quando usar
- Fluxos com muitas regras de transição (auth, checkout, onboarding)
- UI com múltiplos estados concorrentes (upload + validação + progresso)
- Bugs recorrentes de "estado impossível"
- Necessidade de auditoria de comportamento

## Fluxo de trabalho
1. Liste eventos do domínio (`LOGIN_SUBMITTED`, `TOKEN_EXPIRED`, `RETRY`).
2. Liste estados válidos e proibidos.
3. Defina transições explícitas por evento.
4. Adicione `guards` para regras de negócio.
5. Separe `actions` puras de efeitos colaterais.
6. Cubra com testes de transição e casos de erro.

## Padrões recomendados
- Estado inicial explícito e único
- Submáquinas para domínios internos (ex.: pagamento)
- Estado `failure` com estratégia de recuperação
- Eventos nomeados no passado/presente de domínio
- Contexto mínimo necessário (evite "estado global dentro da máquina")

## Checklist de qualidade
- Todo estado tem caminho de entrada e saída?
- Existem transições impossíveis não tratadas?
- Guards são determinísticos e testáveis?
- Há timeout/cancelamento para estados assíncronos?
- O diagrama reflete o comportamento real em produção?

## Testes mínimos
- Transições felizes por evento principal
- Transições inválidas (evento ignorado ou erro esperado)
- Guards true/false
- Reentrada/retry e cancelamento
- Recuperação após falha externa

## Anti-patterns
- Multiplicar booleans (`isLoading`, `isDone`, `hasError`)
- Colocar lógica de domínio dentro de componentes de UI
- Actions com side effects escondidos e não idempotentes
- Não versionar a máquina quando regras mudam

## Saída esperada do agente
- Diagrama textual de estados/transições
- Tabela `estado x evento -> próximo estado`
- Lista de guards/actions com responsabilidades
- Plano de testes de transição