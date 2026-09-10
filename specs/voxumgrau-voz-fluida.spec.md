---
id: spec-voxumgrau-voz-fluida
versao: 0.1.0
status: proposta
componente: Projetos/VoxUmGrau
tags: [voxumgrau, voz, streaming, barge-in, turn-taking, websocket, stt, tts, compose]
data: 2026-09-09
---

# Spec — Voz Fluida no VoxUmGrau (turn-taking, streaming progressivo, barge-in)

Torna a conversa por voz do VoxUmGrau fluida: o turno de voz é fechado apenas
no resultado final do reconhecimento, o áudio começa a tocar enquanto ainda
está sendo gerado (por sentença) e o usuário pode interromper a resposta a
qualquer momento.

## Objetivo

Hoje a conversa por voz do Vox tem três limitações que degradam a fluidez:

1. Turn-taking quebrado: `VoxStt` trata transcrições parciais como resultado
   final (`onPartialResults` chama o mesmo callback de `onResults`), fechando
   o turno e enviando à bridge falas incompletas ou duplicadas.
2. Áudio não progressivo: a bridge envia `audio_chunk` para cada fatia bruta
   do edge-tts, mas o app apenas concatenada esses chunks num arquivo e toca
   tudo de uma vez no `audio_done`. O usuário não ouve nada até o final.
3. Sem barge-in: tocar/voltar a falar durante a resposta não interrompe a
   geração na bridge — apenas para o MediaPlayer local; a bridge continua
   gerando o restante do áudio.

Esta spec entrega as três correções, deixando a memória de longo prazo para
um trilho separado (fora de escopo).

## Requisitos

### 1. Turn-taking final por resultado STT

- `VoxStt` deve expor dois callbacks distintos: `onPartial` (transcrição
  parcial, apenas exibição) e `onResult` (resultado final, envio do turno).
- O turno só é fechado e enviado no `onResults`.
- O parcial deve ser exibido ao vivo na UI enquanto o usuário fala.
- O parcial NÃO pode ser enviado como turno à bridge.

### 2. Streaming progressivo por sentença

- A bridge deve gerar o áudio por sentença (usando o `SentenceChunker`
  existente, modo `chunk_for_streaming`) e enviar um `audio_chunk` por
  sentença, em ordem.
- Cada `audio_chunk` deve conter um MP3 completo e tocável (síntese da
  sentença individual), para que o app possa reproduzi-lo imediatamente.
- O app deve tocar cada sentença assim que chega, em fila, sem esperar o
  `audio_done`.
- O protocolo de mensagens não muda: mantém `audio_streaming`, `audio_chunk`
  e `audio_done`.

### 3. Barge-in

- O app deve enviar `{"tipo": "cancelar"}` à bridge quando o usuário interromper
  a resposta (toque no microfone ou botão de parar durante a fala).
- A bridge deve cancelar a resposta em andamento (task do turno corrente) e
  retomar a escuta.
- O app deve parar a fila de reprodução e voltar ao estado de escuta.

### 4. Fora de escopo

- Memória de longo prazo, entidades, proveniência e confiança — trilho
  separado.
- VAD, detecção automática de fim de fala por modelo de ML, eco cancellation —
  trilhos futuros, não desta spec.

## Restrições

- App Android em Kotlin + Jetpack Compose, sem dependência nova.
- Bridge em Python stdlib + asyncio; manter `websockets` como está.
- Não quebrar os tipos existentes do protocolo: `mensagem`, `editar`, `imagem`,
  `ping`, `pong`, `ack`, `historico`, `audio`, `quota`, `command`, `progresso`.
- Não alterar heartbeat, grace period, fila ACK-based nem a sonda de rota.
- Reutilizar `SentenceChunker` e `SpeechPipeline` existentes — não criar
  duplicação.
- Cada `audio_chunk` deve ser um MP3 válido e tocável isoladamente.
- O cancelamento não pode quebrar a conexão nem a fila de reenvio.
- Toda resposta em pt-BR (regra do ecossistema).

## Dependências

- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxStt.kt`
  — correção do parcial/final (turn-taking).
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxViewModel.kt`
  — estado `transcricaoParcial`, início/fim do turno, `interromperResposta()`.
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxAudioPlayer.kt`
  — fila progressiva de chunks.
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt`
  — comando `cancelar`.
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/JarvisChatScreen.kt`
  — exibição do parcial ao vivo e botão de interromper.
- `scripts/jarvis_bridge.py`
  — handler de `{"tipo": "cancelar"}` e resposta em task cancelável.
- `tts/speech_pipeline.py` — novo `stream_sentencas(text)` por sentença.
- `tts/sentence_chunker.py` — `chunk_for_streaming()` (já existe).
- `tts/edge_tts_engine.py` — síntese por sentença via `synthesize`.

## Premissas

- O edge-tts consegue sintetizar sentenças curtas individualmente (o
  `SentenceChunker` já a divide para isso).
- `SpeechPipeline` é a porta de entrada única de TTS; o novo método reutiliza
  o pipeline.
- A latência por sentença (fração de segundo) é aceitável para reprodução
  progressiva.
- O app tem coroutines (kotlinx-coroutines) disponíveis, já usadas no projeto.
- O usuário pode tocar para interromper em qualquer momento da resposta.

## Entradas e Saídas

### Turn-taking (app)

- Entrada: `onPartialResults(texto)` — exibição apenas.
- Entrada: `onResults(texto)` — encerra turno e envia à bridge.
- Saída: mensagem `{"tipo": "mensagem", "id": N, "texto": "<final>"}`.

### Streaming (bridge → app)

Entrada: texto da resposta (`r_tela`).

Saída:

{
  "text": "...", "corrigido": "...", "audio_streaming": true
}
{ "audio_chunk": "<base64 MP3 da sentença 1>" }
{ "audio_chunk": "<base64 MP3 da sentença 2>" }
...
{ "audio_done": true }

### Barge-in

- App → bridge: `{"tipo": "cancelar"}`.
- Bridge → app: `{"tipo": "cancelado", "text": "<confirmação curta>"}` e, se
  ainda houver stream aberto, `{"audio_done": true}`.
- Efeito: app para a fila, bridge cancela a task da resposta e volta à escuta.

## Casos de Borda

- Parcial chega após o final: ignorado (accept flag de turno fechado).
- `onResults` sem texto: não envia turno vazio.
- Cancelar sem resposta em andamento: bridge confirma e ignora (idempotente).
- Cancelar durante o próprio `audio_chunk`: a task morre no próximo `await`;
  bridge envia `audio_done` para o app não ficar preso.
- Reconexão com resposta sendo cancelada: fila ACK-based preserva mensagens
  do usuário; o cancelamento não entra na fila de reenvio.
- Sentença muito longa: `SentenceChunker` quebra em cláusulas; cada uma vira
  um `audio_chunk` próprio.
- Volume do widget: mantido no `audio_streaming` inicial (como hoje).
- `SpeechPipeline` indisponível: fallback legado por `edge_tts.Communicate`
  ainda por sentença; se falhar, resposta textual pura (comportamento atual).

## Critérios de Aceitação

- [arquivo:Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxStt.kt]
  VoxStt tem callbacks distintos para parcial e final.
- [arquivo:Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxViewModel.kt]
  ViewModel expõe `transcricaoParcial` e `interromperResposta()`.
- [arquivo:Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxAudioPlayer.kt]
  VoxAudioPlayer reproduz chunks progressivamente (fila).
- [arquivo:Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt]
  VoxWebSocket envia `{"tipo": "cancelar"}`.
- [arquivo:Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/JarvisChatScreen.kt]
  UI exibe o parcial ao vivo.
- [arquivo:scripts/jarvis_bridge.py] Bridge trata `tipo == "cancelar"`.
- [arquivo:tts/speech_pipeline.py] `stream_sentencas` existe no pipeline.
- [comando:python -c "import ast; ast.parse(open('scripts/jarvis_bridge.py',encoding='utf-8').read())"]
  Bridge sem erro de sintaxe.
- [comando:python -c "import ast; ast.parse(open('tts/speech_pipeline.py',encoding='utf-8').read())"]
  SpeechPipeline sem erro de sintaxe.
- [comando:python scripts/test_voz_fluida.py] Testes de voz fluida passam.
- Manual — parcial não fecha turno nem envia à bridge.
- Manual — áudio começa antes do final da resposta e toca por sentença.
- Manual — interromper para o áudio e a geração e volta a escutar.

## Definition of Done

- [ ] VoxStt separa parcial de final; parcial não envia turno.
- [ ] ViewModel expõe parcial ao vivo e `interromperResposta()`.
- [ ] AudioPlayer toca cada chunk imediatamente, em fila.
- [ ] WebSocket envia `cancelar`.
- [ ] UI mostra o parcial enquanto ouve.
- [ ] Bridge trata `cancelar`, cancela a task e retoma a escuta.
- [ ] Bridge gera áudio por sentença (chunks tocáveis individualmente).
- [ ] Protocolo `audio_streaming`/`audio_chunk`/`audio_done` preservado.
- [ ] Tipos existentes do protocolo intactos (mensagem, editar, imagem, ping,
  ack, historico, audio, quota, command).
- [ ] Heartbeat e grace period sem regressão (teste de ping existente, se disponível).
- [ ] `python scripts/test_voz_fluida.py` passa.
- [ ] Sintaxe bridge e pipeline válidas.
- [ ] Compilação Android (assembleDebug) ok quando SDK disponível.
- [ ] Teste manual no aparelho.
- [ ] Código versionado via gate (`persistencia.ps1`) — apenas se o usuário pedir.

## Riscos

### Atraso por síntese individual de sentenças

Severidade baixa: cada sentença adiciona latência de frações de segundo, mas a
primeira sentença toca bem antes do áudio inteiro estar pronto (ganho de
fluidez percebida).

Mitigação: sentenças curtas via `chunk_for_streaming`; fallback textual se TTS
falhar.

### Regressão no fluxo de mensagens da bridge

Severidade média: mover a resposta para uma task cancelável altera o fluxo
sequencial atual.

Mitigação: extrair a resposta em função interna que preserva comportamento
quando não há cancelamento; pin/ack continuam no loop; testes de protocolo.

### Concorrência entre task da resposta e novas mensagens

Severidade média: nova fala durante a resposta cancela a task anterior.

Mitigação: single-thread asyncio; só uma task de resposta por conexão; o
cancelamento ocorre em `await` (ponto seguro).

### Histórico órfão ao cancelar resposta em voo

Severidade baixa: cancelando no meio da LLM, o histórico pode ficar sem a
resposta reescrita.

Mitigação: a próxima tarefa usa o mesmo `c` e regenera; aceitável na V0.1.

### Player progressivo com muitos chunks

Severidade baixa: fila de MediaPlayers por sentença.

Mitigação: reutilizar um único `MediaPlayer` por vez (próximo chunk após
`onCompletion`); `stop()` cancela fila.

## Testes Relacionados

- scripts/test_voz_fluida.py
- scripts/test_vox.py