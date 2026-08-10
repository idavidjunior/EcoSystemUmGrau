---
tags: [bug, input, projeto, tem, treinamentonavegacao, visivel]
aliases: [send_keys nao funciona em campos rich-text]
date: 2026-08-10
---

# send_keys nao funciona em campos rich-text

**Projeto:** treinamento_navegacao

## Causa Raiz
Contenteditable e iframes rich-text nao tem input visivel; eventos de teclado nao sao processados

## Correcao
Clicar no elemento, executar JS para limpar (editor.innerHTML=''), depois enviar caracteres via execCommand('insertText') ou dispatchEvent de InputEvent
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-navegacao]]
- [[css-selector-priority-ladder]]
- [[dom-element-hierarchy-mapping]]
- [[iframecontenteditable-text-entry]]
- [[spa-navigation-detection]]