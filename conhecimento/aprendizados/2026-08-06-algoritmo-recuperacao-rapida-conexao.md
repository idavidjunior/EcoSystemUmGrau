---
tipo: padrao
tags: [conexao, websocket, resiliencia, recuperacao, checkpoint, backoff, heartbeat, bridge]
data: 2026-08-06
contexto: |
  Usuario pediu algoritmo de recuperacao rapida de conexao sem perda de contexto,
  inspirado em solucoes online. Bridge atual so faz ping/pong passivo e loga "fim"
  no ConnectionClosed. Zero reconexao, zero checkpoint de sessao.
decisao: |
  Adotar 5 padroes consolidados (sem reinventar):
  1. Backoff exponencial com jitter — base 500ms, max 30s, 10 tentativas, jitter ate 1s.
  2. Heartbeat ping/pong ativo — 5s intervalo, 30s timeout para detectar socket zumbi.
  3. Fila de mensagens em transito — fala do usuario durante queda entra em fila local.
  4. Checkpoint por evento append-only — estado derivado dos eventos, checkpoint apos
     cada tool_call, sobrevive a queda de processo.
  5. Retomada de contexto ao reconectar — bridge le conversa_unica.json, identifica
     ultima pergunta sem resposta, responde e avisa "Voltei, senhor, estavamos em X".
  
  Implementacao em 3 camadas:
  - Camada 1: scripts/conn_recovery.py (classe ReconnectingBridge) — separa da bridge.
  - Camada 2: ReconnectingWebSocket no app Kotlin — backoff identico do lado do cliente.
  - Camada 3: integrar checkpoint de eventos no runtime_state.py (reaproveita infra).
  
  Evolucao continua = medir 3 metricas por queda: tempo ate deteccao, tempo ate
  reconexao, mensagens perdidas. Ajustar parametros do backoff com base em dados
  reais, nao achismo.
impacto: |
  - Quedas deixam de exigir intervencao humana para reconectar.
  - Contexto nunca se perde (retomada automatica via historico unificado).
  - Mensagens em transito nao se perdem (fila local).
  - Socket zumbi detectado em 30s em vez de indefinidamente.
  - Metricas permitem ajuste empirico dos parametros ao longo do tempo.
fontes:
  - https://dev.to/hexshift/robust-websocket-reconnection-strategies-in-javascript-with-exponential-backoff-40n1
  - https://understandingdata.com/posts/agent-memory-patterns/
  - https://websocket.org/guides/reconnection/ (State Sync and Recovery Guide)
  - https://code.claude.com/docs/en/checkpointing (padrao checkpoint/resume)
  - https://agentpatterns.ai/patterns/agent-design/selective-checkpoint-restore/
pendente:
  - Implementar camada 1 (conn_recovery.py) quando o usuario aprovar.
  - Validar com test_vox.py existente.
  - Sincronizar no git apos validacao.
---

# Algoritmo de Recuperacao Rapida de Conexao

## Resumo

Pesquisa online concluida em 06/08/2026 sobre padroes comprovados de resiliencia
WebSocket e checkpoint de agentes. Diagnostico da bridge atual identificou gaps
criticos. Proposta concreta de 3 camadas de implementacao, sem reinventar solucao.

## Diagnostico da Bridge Atual

`scripts/jarvis_bridge.py:1394-1395`:

```python
except websockets.exceptions.ConnectionClosed:
    logger.info("fim")
```

- So loga "fim" — zero reconexao.
- Ping/pong passivo (linha 1309-1312): so responde ping do app, nao inicia heartbeat.
- Sem checkpoint de sessao — se a queda ocorrer no meio de uma resposta, perde-se.
- Sem aviso ao usuario em audio quando a conexao volta.
- Continuidade depende exclusivamente do app Android reconectar manualmente.

## Cinco Padroes Consolidados (consenso na engenharia)

### 1. Backoff Exponencial com Jitter

```
delay = min(base * 2^attempt + jitter_aleatorio, max_delay)
base = 500ms
max = 30000ms (30s)
max_attempts = 10
jitter = random(0, 1000ms)
```

- Evita "thundering herd" — nenhum cliente martela o servidor.
- Reconecta rapido nas primeiras quedas, desiste graciosamente apos 10 tentativas.

### 2. Heartbeat Ping/Pong Ativo

- A bridge envia ping a cada 5s.
- Se pong nao volta em 30s, fecha o socket e dispara reconexao.
- Detecta socket zumbi (TCP conectado mas peer morto) em 30s, em vez de esperar
  infinitamente pelo keepalive do SO.

### 3. Fila de Mensagens em Transito

- Se o usuario fala durante a queda, a mensagem entra numa fila local (deque).
- Quando a reconexao sucede, a fila e drenada em ordem.
- O usuario nunca percebe que houve queda — a fala chega como se nada tivesse acontecido.

### 4. Checkpoint por Evento Append-Only

- Log append-only de eventos: `pergunta_recebida`, `resposta_enviada`,
  `audio_gerado`, `erro`, `queda_reconhecida`, `reconectado`.
- Estado derivado dos eventos, nunca guardado direto (evita inconsistencia).
- Checkpoint apos cada tool_call — sobrevive a queda de processo sem perder progresso.
- Baseado no padrao event-sourcing (12 Factor Agents, Factors 5 e 6).

### 5. Retomada de Contexto ao Reconectar

- Ao reconectar, a bridge le `conversa_unica.json` (raiz do ecossistema).
- Identifica a ultima pergunta do usuario sem resposta no historico.
- Responde ela em audio e avisa "Voltei, senhor, estavamos em X, vamos continuar."
- Implementacao tecnica da clausula petrea de Continuidade de Contexto (04/08/2026).

## Implementacao Proposta — 3 Camadas

### Camada 1: `scripts/conn_recovery.py`

Nova classe `ReconnectingBridge` que encapsula:
- Backoff com jitter
- Heartbeat ativo
- Fila de mensagens em transito
- Checkpoint por evento (delegando ao `runtime_state.py`)

Mantem `jarvis_bridge.py` limpo — a logica de resiliencia fica separada.

### Camada 2: `ReconnectingWebSocket` no app Kotlin

- Mesmo algoritmo do lado do cliente (backoff identico).
- Se a bridge cai e o app detecta, ele reconecta sem intervencao humana.
- Usa `okhttp3.WebSocket` com listener de `onClosed`/`onFailure`.

### Camada 3: Integrar checkpoint no `runtime_state.py`

- O `runtime_state.py` ja faz checkpoints de missao LER.
- Reaproveitar a mesma infraestrutura para checkpoints de sessao de conversa.
- Novo metodo `checkpoint_conversa(evento)` appenda ao log de eventos.

## Evolucao Continua (sem achismo)

Medir 3 metricas por queda:
1. **Tempo ate deteccao** — quanto tempo entre a queda real e o heartbeat detectar.
2. **Tempo ate reconexao** — quanto tempo entre deteccao e reconexao sucedida.
3. **Mensagens perdidas** — quantas mensagens ficaram na fila e nao foram entregues.

Com essas 3 metricas no log, ajustar:
- Se deteccao demora: reduzir intervalo de heartbeat (5s -> 3s).
- Se reconexao falha: aumentar max_attempts ou revisar rede Tailscale.
- Se mensagens se perdem: a fila esta descartando em vez de enfileirar.

## O que NAO propor (para nao delirar)

- IA para prever quedas — nao ha dados suficientes e nao e o gargalo.
- Protocolo novo de transporte — TCP/WebSocket e o padrao, nao tem nada melhor.
- Replicacao multi-region — singleton na propria casa do usuario.
- Reinvencao do checkpoint — o `runtime_state.py` ja faz isso para missoes.

## Status

- Pesquisa concluida: 06/08/2026 14:40
- Aprendizado registrado na memoria: #111 (padrao)
- Implementacao: pendente aprovacao do usuario para comecar pela camada 1.

## Conexoes

- [[cluster-hub-programacao]]