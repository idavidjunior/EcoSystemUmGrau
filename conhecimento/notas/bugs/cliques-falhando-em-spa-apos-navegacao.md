---
tags: [bug, treinamentonavegacao]
aliases: [Cliques falhando em SPA apos navegacao]
date: 2026-08-01
---

# Cliques falhando em SPA apos navegacao

**Projeto:** treinamento_navegacao

## Causa Raiz
Stale element reference: o DOM foi substituido pelo React/Vue mas a referencia ao elemento antigo permanece

## Correcao
Re-query pelo seletor apos cada navegacao; usar waitForSelector com timeout no novo DOM em vez de manter referencia
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-navegacao]]
- [[css-selector-priority-ladder]]
- [[dom-element-hierarchy-mapping]]
- [[iframecontenteditable-text-entry]]
- [[spa-navigation-detection]]