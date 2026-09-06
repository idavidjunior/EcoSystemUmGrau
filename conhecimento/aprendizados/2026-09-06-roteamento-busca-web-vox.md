---
tipo: erro
tags: [jarvis, vox, roteamento, busca-web, voz-rapida, opencode-serve]
data: 2026-09-06
contexto: Usuário perguntou ao Vox sobre a promoção "tixan ypê" e o assistente respondeu "Desculpe, não tenho informações" e "Não tenho acesso a novas pesquisas online". O usuário apontou que deveria pesquisar na web, com razão.
decisao: Roteamento por intenção de busca no fluxo lidar(ws) do jarvis_bridge.py. Pedidos que exigem dado atual/online (promoção, preço, notícia, cotação, clima, etc.) agora pulam o canal voz rápida (NVIDIA puro sem ferramentas) e vão direto ao opencode serve (que tem MCP internet/browser + websearch). Adicionado reino _requer_busca_web() com regex ampla e instrução no _SISTEMA_VOZ_RAPIDA para não negar capacidade de pesquisa.
impacto: Vox agora pesquisa de verdade para pedidos de dado online. Teste ao vivo no serve confirmou que ele achou a promoção correta ("Meu Ypê Premiado 2026") via webfetch, após contornar bloqueio do Google. Latência é maior ("Entendendo sua solicitação" no lugar de "Respondendo rápido"), mas a resposta é correta. Ajuste adicional: timeout do POST /session/{id}/message elevado de 120s para 300s (jarvis_bridge.py perguntar), pois o serve com contexto pesado (~160k tokens) frequentemente estourava os 120s e matava a resposta de busca web (2a tentativa no log: início 00:20:19, timeout exato 120s depois).

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]