---
id: spec-voxumgrau-exibir-imagem
versao: 0.1.0
status: proposta
componente: Projetos/VoxUmGrau (app Android) + scripts/jarvis_bridge.py (bridge)
tags: [voxumgrau, imagem, websocket, bridge, mapa-mental, base64, compose]
data: 2026-09-05
---

# Spec — Exibir Imagem no VoxUmGrau

Permite ao usuário pedir (por voz ou texto) que o Vox mostre um mapa mental,
gráfico ou outra imagem, e o app exibe essa imagem na tela.

## Objetivo

Hoje o app VoxUmGrau só processa texto e áudio via WebSocket. O usuário não tem
como ver uma figura. O objetivo é que, ao pedir algo como "mostre um mapa
mental sobre X", a bridge gere a imagem a partir do texto e o app a exiba.

## Requisitos

1. Novo tipo de mensagem da bridge para o app: `{"tipo": "imagem", "base64_png": "<...>", "legenda": "..."}`.
2. A bridge (`jarvis_bridge.py`) detecta pedidos de imagem/figura/diagrama e
   gera um PNG localmente a partir do texto (ex.: mapa mental via Graphviz ou
   Mermaid), sem depender de LLM de imagem pago.
3. O app, ao receber `tipo == "imagem"`, decodifica o base64, monta o Bitmap e
   exibe em um balão de chat novo (`MessageBubble` com composable `Image`).
4. A imagem cabe na conversa: aparece no histórico e pode ser "respondida"
   (o texto continua fluindo normalmente depois dela).
5. Fallback: se não for possível gerar a imagem, a bridge responde com texto
   descrevendo o diagrama (estado atual não regride).

## Restrições

- App Android em Kotlin + Jetpack Compose (sem AndroidX? verificar), já
  conectado via `VoxWebSocket.kt`; o envio de imagem deve entrar no pipeline
  `onMessage -> VoxViewModel -> JarvisChatScreen`.
- Bridge é Python puro (stdlib sugerido + ferramenta de grafo já disponível ou
  instalável uma única vez, ex.: `graphviz`/`matplotlib`).
- Base64 nunca corre o risco de quebrar JSON: o payload viaja como string num
  campo separado, igual ao áudio que já manda `{"audio": "<base64>"}`.
- Não quebrar os tipos existentes (`mensagem`, `editar`, `ping/pong`, `ack`,
  `historico`, `audio`).
- Não regridir grance period / heartbeat da correção §98297.

## Dependências

- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt` —
  onde os `tipo` recebidos são interpretados (processarMensagem).
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxViewModel.kt` —
  estado da conversa (fila de mensagens).
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/ui/components/MessageBubble.kt` —
  renderização de cada mensagem (adicionar variante "imagem").
- `scripts/jarvis_bridge.py` — geração do PNG + envio do novo comando.

## Premissas

- Existe uma ferramenta de grafo instalada/instalável no PC (graphviz para
  mapa mental, ou similar) — sem isso o fallback de texto cobre o caso.
- A tela do chat suporta adicionar um novo tipo de balão sem refatorar o layout.

## Entradas e Saídas

- Entrada app->bridge: texto do usuário (`{"tipo":"mensagem","texto":"mostre um mapa mental de ..."}`).
- Saída bridge->app: `{"tipo":"imagem","base64_png":"<png>","legenda":"<texto curto>"}`,
  além do áudio/legenda falada de costume.
- Efeito colateral: a imagem fica no histórico do chat da sessão.

## Casos de Borda

- Pedido de imagem durante o setup da bridge: respeitar o grace period; a imagem
  chega quando o socket estiver ativo (sem mudança no heartbeat).
- Base64 muito grande: limitar tamanho (ex.: 10 MB de PNG) e, acima disso,
  responder só com o caminho do arquivo no PC + descrição em texto.
- Geração falhou (ferramenta ausente/erro): fallback com descrição textual.
- Usuário pede imagem e depois texto: a conversa flui normalmente após a imagem.

## Critérios de Aceitação

- [arquivo:Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt] Campo `tipo=="imagem"` é tratado sem quebrar os demais canais.
- [arquivo:Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/ui/components/MessageBubble.kt] Existe variante visual "imagem" (composable Image com o Bitmap decodificado).
- [comando:python -c "import os,sys; sys.exit(0 if os.path.exists('Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt') else 1)"] App existe e a verificação executável passa.
- Critério manual: pedir "mostre um mapa mental de X" e ver a imagem na tela do Vox.
- Critério manual: connection continua estável depois de exibir uma imagem (sem meia-morte).

## Definition of Done

- [ ] Bridge gera PNG (graphviz/mermaid) a partir do texto e envia `tipo=imagem`.
- [ ] App decodifica base64, renderiza `Image` no balão e preserva o chat.
- [ ] Fallback textual quando a geração falha.
- [ ] Teste no PC (`teste_ping_periodico.py` adaptado ou novo) cobre envio de imagem.
- [ ] Instalado e validado no aparelho (installDebug) com screenshot/evidência.
- [ ] Código versionado via gate (`persistencia.ps1`).

## Riscos

- Geração de imagem depende de ferramenta externa (graphviz/matplotlib) — severidade
  média (mitigado: fallback textual que já descreve o diagrama).
- Payload grande pode pesar no WebSocket — severidade baixa (mitigado: limite de
  tamanho e fallback com caminho do arquivo).
- Mudança no MessageBubble pode afetar o histórico atual — severidade baixa
  (mitigado: variante nova, sem tocar nos tipos já renderizados).

## Testes Relacionados

- scripts/jarvis_bridge.py — teste do novo comando `imagem` (gera PNG no PC).
- Teste manual no aparelho via installDebug + pedido de mapa mental.
- `teste_ping_periodico.py` — confirmar que o envio de imagem não interfere no heartbeat/grace.