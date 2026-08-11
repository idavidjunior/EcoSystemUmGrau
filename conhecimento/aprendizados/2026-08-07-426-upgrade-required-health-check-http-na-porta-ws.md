---
tipo: erro
tags: [bridge, websocket, 426, universal_bridge, health-check, resilience]
data: 2026-08-07
contexto: Relatório do sistema de voz revelou erros recorrentes 'connection rejected (426 Upgrade Required)' no log da bridge (1/minuto). Investigação apontou o universal_bridge fazendo health-check HTTP na porta 8765, que é WebSocket.
decisao: Criado checker ws_health em connectivity/bridge/core.py (handshake WebSocket REAL via websockets.sync.client, não apenas TCP check). Endpoint api_local trocado de type=http para type=ws_health com url ws://127.0.0.1:8765, tanto no config em disco (configs/bridge_config.json) quanto no template versionável (deployment/bridge_config.example.json).
impacto: api_local agora healthy=true com handshake ok. Último 426 às 11:14:22 (daemon antigo); nenhum 426 desde o reinício com config corrigido (~90s+ de monitoramento). Antes era 1/minuto constante. O health check da bridge agora é por significado (handshake real) e não gera ruído. Causa raiz: endpoint api_local apontava http:// para porta WS.
status: resolvido

## Conexoes

- [[cluster-hub-programacao]]