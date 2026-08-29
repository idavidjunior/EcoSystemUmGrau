---
tipo: padrao
tags: [terminal, logs, edge, websocket, tail, bridge]
data: 2026-08-29
contexto: Implementação do TerminalWidget de logs em tempo real no Edge. Necessidade de canal WS na bridge 8765 + fallback HTTP 8766, abas de terminal vanilla JS e expansão de janela via logs_toggle.
decisao: Criar allowlist LOGS_ECO (bridge, narrador, edge, dialogo, preflight) com tail incremental por offset (LOCK asyncio), snapshot das últimas 120 linhas via _log_snapshot, stream de linhas novas via _ler_linhas_novas com _tail_decodificar (retrocede até 4 bytes p/ multibyte). Rota WS /logs roteada no topo de lidar via ws.request.path (websockets 17 aceita), rota HTTP GET /api/logs. Front em Vanilla JS no www/terminal_widget.js + CSS, buffer 120, backoff WS e polling HTTP como fallback. widget_edge.py ganhou logs_toggle persistindo logs_aberto em widget_state.json, resize(360, 480|300) ancorando a base da janela.
impacto: Terminal de logs funcional no Edge sem infra nova; reutiliza bridge e pywebview existentes. Corrigido bug inicial de offsets iniciando em 0 (relia o arquivo inteiro) — inicializar no tamanho atual após snapshot. Linhas CRLF requintadas com rstrip(\r). Registrado widget_edge.py no inventário de estruturas. Preflight técnico aprovado.
---
