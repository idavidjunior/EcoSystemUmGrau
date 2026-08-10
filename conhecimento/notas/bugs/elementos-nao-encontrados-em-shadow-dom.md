---
tags: [bug, encontrados, penetra, projeto, shadowroots, treinamentonavegacao]
aliases: [Elementos nao encontrados em Shadow DOM]
date: 2026-08-10
---

# Elementos nao encontrados em Shadow DOM

**Projeto:** treinamento_navegacao

## Causa Raiz
Shadow DOM encapsula elementos; querySelector normal nao penetra shadowRoots

## Correcao
Navegar pela arvore de shadowRoots: element.shadowRoot.querySelector(...); usar caminho completo com parent.shadowRoot.child.shadowRoot
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-navegacao]]
- [[css-selector-priority-ladder]]
- [[dom-element-hierarchy-mapping]]
- [[iframecontenteditable-text-entry]]
- [[spa-navigation-detection]]