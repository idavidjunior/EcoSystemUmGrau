---
tipo: padrao
tags: [conexao, websocket, reconexao, resiliencia, bridge, android]
data: 2026-08-06
contexto: "Usuario relatou quedas frequentes de conexao. Pedido: pesquisar solucoes online para recuperacao rapida sem perda de contexto/consistencia e evoluir algoritmo de reconnect."
decisao: "Estudar e adotar padroes maduros de reconexao (Socket.IO exponential backoff + jitter, websockets ping/pong keepalive, heartbeat) na bridge Jarvis."
impacto: "Permite que o ecossistema se recupere automaticamente de quedas sem intervencao manual, mantendo contexto via conversa_unica.json."
---

# Recuperacao Rapida de Conexao — Pesquisa e Evolucao

## Problema relatado
O servidor (ponte de voz) cai frequentemente. Quedas causam:
- Perda de audio em andamento
- Usuario precisa esperar watchdog reiniciar (~20s)
- App Android perde conexao ate reconectar manualmente

## O que ja existe na bridge (jarvis_bridge.py)
1. **Ping-pong manual** (linha 1309): app manda `{"tipo":"ping"}`, bridge responde `pong`. So detecta conexao morta quando o ping-pong falha.
2. **Janela de conversa ativa** (linha 1258): se ultima fala < JANELA_CONVERSA_MIN, suprime saudacao na reconexao. Mantem contexto.
3. **Watchdog externo** (watchdog.ps1): monitora a cada 20s, reinicia a bridge se cair. So atua no nivel do processo, nao da conexao.
4. **conversa_unica.json**: historico persistente (ate 500 pares) retomado a cada reconexao.

## O que falta (lacunas identificadas)
1. **Sem keepalive nativo WebSocket**: nao usa ping_interval/ping_timeout do websockets.serve(). Deteccao de conexao morta lenta.
2. **Sem backoff exponencial no cliente Android**: Socket.IO tem reconnectionDelay=1000ms, reconnectionDelayMax=5000ms, randomizationFactor=0.5. App atual nao tem isso.
3. **Sem fila de reenvio**: se a conexao cai no meio de uma fala, a mensagem se perde. Socket.IO tem `retries` + `ackTimeout`.
4. **Sem deteccao de rede**: o ADB do celular nem sempre encontra o PC pelo IPv4 do Tailscale quando troca de rede (memoria #72).
5. **Sem heartbeat bidirecional proativo**: so detecta morte quando tenta enviar/na proxima iteracao do for.

## Padroes maduros encontrados (research online)

### 1. Socket.IO — exponential backoff com jitter (padrao ouro)
- `reconnection: true` (auto-reconectar)
- `reconnectionAttempts: Infinity` (nao desiste)
- `reconnectionDelay: 1000` (delay inicial 1s)
- `reconnectionDelayMax: 5000` (teto 5s)
- `randomizationFactor: 0.5` (+/- 50% de jitter para evitar thundering herd)
- Sequencia: 1s -> 2s -> 4s -> 5s -> 5s (teto)
- Jitter evita que todos os clientes reconectem simultaneamente apos queda do servidor

### 2. websockets (Python lib) — keepalive automatico
- `ping_interval=20` — envia ping a cada 20s
- `ping_timeout=20` — se nao receber pong em 20s, fecha conexao
- `close_timeout=10` — tempo para handshake de fechamento
- Deteccao automatica de conexao morta sem codigo manual
- `max_queue=16` — flow control para nao estourar memoria

### 3. Heartbeat application-level (alem do WebSocket ping)
- App manda `{"tipo":"ping"}` a cada 15s
- Bridge responde `{"tipo":"pong"}`
- Se 3 pings sem pong, app assume conexao morta e reconecta
- Mais robusto que so depender do ping do protocolo

### 4. Fila de reenvio (message queue) no cliente
- App mantem fila de mensagens nao-confirmadas
- Cada mensagem tem ID unico
- Bridge confirma com `{"ack": msg_id}`
- Se reconectar, app reenvia todas pendentes
- Evita perder falas no meio da transmissao

### 5. Reconnect com Tailscale fallback
- App tenta primeiro IPv4 do Tailscale (100.91.141.101)
- Se falhar, tenta hostname Tailscale (se DNS resolver)
- Se falhar, tenta IP local (192.168.x.x) descoberto via ADB
- Detecta troca de rede automaticamente

## Evolucao proposta (3 fases)

### Fase 1 — Keepalive nativo + deteccao rapida (bridge)
- Ativar `ping_interval=20, ping_timeout=20` em `websockets.serve()`
- Remover ping-pong manual (redundante com o nativo)
- Adicionar log de conexao-morta para debug
- Tempo de deteccao: ~40s -> ~20s

### Fase 2 — Backoff exponencial + heartbeat (app Android)
- Implementar exponential backoff: 1s, 2s, 4s, 5s (teto) com jitter 50%
- Heartbeat application-level a cada 15s (3 falhas = reconectar)
- Notificar usuario em audio: "Reconectando..." quando detecta queda

### Fase 3 — Fila de reenvio + fallback Tailscale (app Android)
- Fila de mensagens nao-confirmadas no app
- Cada fala tem ID, bridge manda `ack` ao receber
- Reconectar reenvia pendentes
- Fallback de rede: Tailscale IPv4 -> hostname -> IP local

## Referencias consultadas
- RFC 6455 (WebSocket Protocol) — secao 7.4 (close codes: 1001 going away, 1011 server error)
- Socket.IO v4 docs — client-options (reconnection, reconnectionDelay, randomizationFactor)
- websockets lib Python — server serve() com ping_interval/ping_timeout nativos
- Memoria #72: ADB do celular nao conecta sempre pelo IPv4 do Tailscale

## Conexoes

- [[cluster-hub-programacao]]