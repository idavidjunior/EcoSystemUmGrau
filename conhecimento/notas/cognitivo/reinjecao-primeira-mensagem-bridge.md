---
tags: [async, cognitivo, general, normal, principal, voz]
aliases: [reinjecao primeira mensagem bridge]
date: 2026-09-05
---

# reinjecao primeira mensagem bridge

**Dominio:** general

---
tipo: erro
tags: [bridge, jarvis, websocket, primeira-mensagem, progresso, reinjecao]
data: 2026-09-05
contexto: Validação do aviso periódico de progresso ("me avise a cada minuto do progresso") falhava com timeout. Diagnóstico: a primeira mensagem da conexão era consumida por `ws.recv(timeout=3)` na classificação e descartada.
decisao: Adicionar `prim_set` + generator `_fluxo_mensagens()` que re-injeta `prim` no loop principal (`async for m in ws`), apenas quando a conexão é de voz normal (
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]