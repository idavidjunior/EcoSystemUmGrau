---
tags: [bug, treinamentonavegacao]
aliases: [Cliques falhando em SPA apos navegacao]
date: 2026-07-28
---

# Bug: Cliques falhando em SPA apos navegacao

**Projeto:** treinamento_navegacao

## Causa Raiz
Stale element reference: o DOM foi substituido pelo React/Vue mas a referencia ao elemento antigo permanece

## Correcao
Re-query pelo seletor apos cada navegacao; usar waitForSelector com timeout no novo DOM em vez de manter referencia
