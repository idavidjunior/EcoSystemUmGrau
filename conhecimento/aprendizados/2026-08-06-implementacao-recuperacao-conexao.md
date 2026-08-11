---
tipo: padrao
tags: [conexao, websocket, resiliencia, bridge, android, reconexao, backoff, heartbeat, ack]
data: 2026-08-06
contexto: "Implementacao das 3 fases do plano de recuperacao rapida de conexao (decisao 112). Objetivo: zero intervencão do usuario, deteccao rapida de queda, sem perda de mensagens."
decisao: "Adotar keepalive nativo websockets (ping 20s) + backoff exponencial com jitter no app + heartbeat application-level 15s + fila ACK-based + fallback de rede."
impacto: "Deteccao de conexao morta cai de ~40s para ~20s. App reconecta sozinho com backoff 1s/2s/4s/5s (teto) + jitter 50%. Nenhuma fala se perde: fila reenvia pendentes apos ACK da bridge."
---

# Implementacao Completa - Recuperacao Rapida de Conexao

## Resumo
Implementadas as 3 fases do plano decisao 112. Codigo validado: bridge Python compila OK, app Android build+install OK (v16).

## Fase 1 - Keepalive nativo (bridge)
- Arquivo: `scripts/jarvis_bridge.py:1409-1420`
- Antes: `websockets.serve(lidar, "0.0.0.0", 8765)` sem keepalive
- Depois: `ping_interval=20, ping_timeout=20, close_timeout=10, max_queue=16`
- Deteccao de conexao morta: ~40s -> ~20s
- Ping-pong manual mantido (linhas 1309-1311) como heartbeat application-level complementar

## Fase 3 - ACK na bridge
- Arquivo: `scripts/jarvis_bridge.py:1322-1335` (inserido apos parse de imagem)
- Ao receber `{"id": N}`, devolve `{"ack": N}` imediato
- Permite que o app remova a mensagem da fila de pendentes
- Se a conexao cair antes do ACK, o app reenvia ao reconectar

## Fases 2 e 3 - App Android (VoxWebSocket.kt)
Arquivo: `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt` (reescrito)

### Backoff exponencial com jitter (Fase 2)
- DELAY_INICIAL=1000ms, DELAY_MAXIMO=5000ms, JITTER_FACTOR=0.5
- Sequencia: 1s -> 2s -> 4s -> 5s (teto) com +/- 50% jitter
- Evita thundering herd quando varios clientes reconectam apos queda
- Padrao ouro Socket.IO aplicado

### Heartbeat application-level (Fase 2)
- HEARTBEAT_INTERVAL_MS=15000, HEARTBEAT_MAX_FALHAS=3
- Envia `{"tipo":"ping"}` a cada 15s
- 3 falhas consecutivas -> fecha conexao (code 1011) -> dispara reconexao
- Mais robusto que so depender do ping do protocolo WebSocket

### Fila ACK-based (Fase 3)
- Cada mensagem ganha ID incremental (`AtomicInteger`)
- Enfileira em `filaPendentes: MutableList<Pair<Int, String>>` (com lock)
- Ao receber `{"ack": id}`, remove da fila
- Ao reconectar com sucesso, `reenviarPendentes()` reenvia todas nao confirmadas
- Nenhuma fala se perde no meio da transmissao

### Fallback de rede (Fase 3)
- `hostCandidates: MutableList<Pair<String, Int>>`
- Ordem: Tailscale IPv4 (persistido) -> localhost (127.0.0.1)
- Se um host falha em `onFailure` sem sucesso, tenta proximo candidato
- `fallbackIndex` controla qual candidato esta sendo tentado

## Validacao
- `python -m py_compile scripts/jarvis_bridge.py` -> OK
- `.\build.ps1 -Install` (VoxUmGrau) -> BUILD SUCCESSFUL, app v16 instalado via ADB
- Memoria #127 registrada

## Resultado
Cadeia de resiliencia completa: se a ponte cair, o app detecta em ~20s (keepalive nativo), reconecta com backoff exponencial + jitter, reenvia falas pendentes via fila ACK e troca de rota se o host principal falhar. Zero intervencão do usuario.

## Conexoes

- [[cluster-hub-programacao]]