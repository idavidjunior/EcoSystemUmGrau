---
tags: [bug, treinamentonavegacao]
aliases: [send_keys nao funciona em campos rich-text]
date: 2026-07-28
---

# Bug: send_keys nao funciona em campos rich-text

**Projeto:** treinamento_navegacao

## Causa Raiz
Contenteditable e iframes rich-text nao tem input visivel; eventos de teclado nao sao processados

## Correcao
Clicar no elemento, executar JS para limpar (editor.innerHTML=''), depois enviar caracteres via execCommand('insertText') ou dispatchEvent de InputEvent
