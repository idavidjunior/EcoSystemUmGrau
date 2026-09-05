---
tipo: erro
tags: [voxumgrau, heartbeat, grace-period, websocket, meia-morte]
data: 2026-09-05
contexto: Correção da "meia-morte" do VoxUmGrau — reconexão em loop porque a bridge fica ~45s em setup sequencial (saudação LLM/TTS) sem ler o socket, e o app contava 3 falhas de pong e reconectava.
decisao: O grace period de 90s do heartbeat é uma janela FIXA desde conectar(). NUNCA zerar gracePeriodAteMs ao receber o primeiro pong — a bridge responde o ping inicial (via prim) e depois mergulha no setup, então o primeiro pong não significa que o setup acabou.
impacto: Com o grace zerado no 1º pong, o aparelho reconectava aos ~45-75s mesmo com o código novo instalado. Removida a linha de zeramento no handler de pong, o app tolerou 45s+ de setup sem falha nem reconexão, e os pongs voltaram a fluir (buffer de log silenciado).
evidencia: installDebug com fix + reinício; logcat: "Heartbeat: sem pong, em grace period (setup bridge) - tolerado" ×3 (às 46s, 61s, 76s do boot) e ZERO "pong nao voltou (falha X)" / ZERO "forçando reconexão"; processo vivo (pidof 14933); grace (90s, expirado às 14:58:32) superado sem falha.
