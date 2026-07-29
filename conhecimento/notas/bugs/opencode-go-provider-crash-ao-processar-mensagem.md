---
tags: [bug, sessaoprovidermanager]
aliases: [OpenCode Go provider crash ao processar mensagem]
date: 2026-07-29
---

# Bug: OpenCode Go provider crash ao processar mensagem

**Projeto:** sessao_providermanager

## Causa Raiz
_simulate_completion() tratava request.messages[-1] como dict sempre, mas ultima msg pode ser string

## Correcao
Adicionado isinstance(last, dict) check; se for string, usa como prompt direto
