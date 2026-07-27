---
name: autonomous-loops
description: |
  Loops autônomos para agentes: planejar, executar, verificar, corrigir e encerrar com critérios explícitos.
  Trigger phrases: "autonomous loop", "agent loop", "self-correct", "iterative agent"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Autonomous Loops — Agentes com Critério de Parada

## Objetivo
Executar ciclos de trabalho autônomos sem deriva infinita, mantendo segurança e qualidade.

## Ciclo base (PEVA)
1. Plan: decompor objetivo em etapas verificáveis
2. Execute: agir em escopo controlado
3. Verify: validar saída com critérios objetivos
4. Adjust: corrigir lacunas e repetir

## Critérios de parada
- Objetivo atingido com validação positiva
- Limite de iterações atingido
- Risco alto detectado (segurança/custo)
- Dependência externa bloqueante

## Guardrails
- Budget de tempo/tokens por ciclo
- Escopo de escrita limitado
- Lista de ações proibidas por política
- Registro de decisões por iteração

## Verificação de qualidade
- Resultado atende critérios de aceitação?
- Há evidência (teste/log/artefato)?
- Introduziu regressão em área sensível?
- Próximo passo reduz incerteza real?

## Anti-patterns
- Loop sem condição de término
- Ajustar plano sem validar hipótese anterior
- Escalar custo sem melhorar qualidade
- Executar ações destrutivas sem checkpoint

## Saída esperada do agente
- Plano iterativo com checkpoints
- Log resumido por iteração
- Motivo de encerramento do loop
- Riscos residuais e próximos passos