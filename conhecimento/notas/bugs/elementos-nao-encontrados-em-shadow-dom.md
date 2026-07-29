---
tags: [bug, treinamentonavegacao]
aliases: [Elementos nao encontrados em Shadow DOM]
date: 2026-07-29
---

# Bug: Elementos nao encontrados em Shadow DOM

**Projeto:** treinamento_navegacao

## Causa Raiz
Shadow DOM encapsula elementos; querySelector normal nao penetra shadowRoots

## Correcao
Navegar pela arvore de shadowRoots: element.shadowRoot.querySelector(...); usar caminho completo com parent.shadowRoot.child.shadowRoot
