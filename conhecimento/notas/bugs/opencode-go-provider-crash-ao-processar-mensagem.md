---
tags: [bug, check, mensagem, pode, projeto, sessaoprovidermanager]
aliases: [OpenCode Go provider crash ao processar mensagem]
date: 2026-08-20
---

# OpenCode Go provider crash ao processar mensagem

**Projeto:** sessao_providermanager

## Causa Raiz
_simulate_completion() tratava request.messages[-1] como dict sempre, mas ultima msg pode ser string

## Correcao
Adicionado isinstance(last, dict) check; se for string, usa como prompt direto
## Conexoes

- [[bug-hub-bugs]]
- [[cadeia-de-provedores-com-failover-inteligente]]
- [[cluster-hub-ecossistema]]
- [[mcp-server-handshake-obrigatorio]]
- [[mcp-server-nao-respondia-nenhum-comando]]
- [[server-failover-com-auto-return]]