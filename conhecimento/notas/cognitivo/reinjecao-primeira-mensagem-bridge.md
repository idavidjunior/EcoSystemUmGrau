---
tags: [cognitivo, duplicada, evitar, general, injetados, resposta]
aliases: [reinjecao primeira mensagem bridge]
date: 2026-09-05
---

# reinjecao primeira mensagem bridge

**Dominio:** general

Tipo: erro

Tags: [bridge, jarvis, websocket, primeira-mensagem, progresso, reinjecao]

Data: 2026-09-05

contexto: Validação do aviso periódico de progresso ("me avise a cada minuto do progresso") falhava com timeout. Diagnóstico: a primeira mensagem da conexão era consumida por `ws.recv(timeout=3)` na classificação e descartada.

decisao: Adicionar `prim_set` + generator `_fluxo_mensagens()` que re-injeta `prim` no loop principal (`async for m in ws`), apenas quando a conexão é de voz normal (`not eh_dashboard`) — health-check e dashboard já responderam na classificação e não são re-injetados para evitar resposta duplicada.

impacto: Pedidos imediatos após conectar (tarefa ou aviso periódico) não se perdem mais. Validado E2E: histórico (92) + greeting + confirmação "Combinado... a cada 1 minuto". Ticker `_notificar_periodico` validado por unidade (3 ticks em 6,5s, para limpo no evento).
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]