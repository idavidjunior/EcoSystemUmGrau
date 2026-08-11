# PontuaÃ§Ã£o da transcriÃ§Ã£o voltando ao balÃ£o do app (corrigido)

- **Data:** 01/08/2026
- **SessÃ£o:** Bug â€” "Que horas sÃ£o" transcrito sem o sinal "?"

## Problema
O usuÃ¡rio perguntou "Que horas sÃ£o" e o balÃ£o da transcriÃ§Ã£o no app nÃ£o mostrava
o "?". A pontuaÃ§Ã£o JÃ era aplicada pela bridge (`fix_punctuation`), mas o app
exibia a transcriÃ§Ã£o crua do STT â€” a correÃ§Ã£o nunca voltava para a tela.

## Causa raiz
- App (`VoxViewModel.onSttResult`): `mensagens + Mensagem(texto, true)` exibe o
  texto cru do SpeechRecognizer e envia sÃ³ esse texto Ã  bridge.
- Bridge (`lidar`): corrigia com `fix_punctuation` e usava o texto corrigido para
  o LLM/`caminho_rapido`, mas a resposta sÃ³ trazia a fala do Jarvis (`text`).

## SoluÃ§Ã£o (echo do texto corrigido)
1. **Bridge** (`jarvis_bridge.py` `lidar`): toda resposta de mensagem agora
   carrega `"corrigido": <texto pÃ³s-fix_punctuation>` â€” nos trÃªs caminhos
   (normal, texto-sem-audio e interrupÃ§Ã£o).
2. **App** (`VoxViewModel.onMessage`): se a resposta tem `corrigido` e a Ãºltima
   mensagem Ã© do usuÃ¡rio (`deUsuario`), substitui o balÃ£o pela versÃ£o corrigida
   (preservando imagem/mime).

## ValidaÃ§Ã£o
- WebSocket real: `que horas sÃ£o` â†’ `corrigido: "Que horas sÃ£o?"` (com `?`);
  `toca uma musica` â†’ `corrigido: "Toca uma musica."`.
- App compilado (`build.ps1 -Install`) e instalado via ADB no Redmi Note 11.

## PadrÃ£o capturado
- Quando a ponte transforma a entrada do usuÃ¡rio (pontuaÃ§Ã£o, normalizaÃ§Ã£o), a
  versÃ£o transformada precisa **voltar ao app** para a tela refletir o que o
  Jarvis entendeu â€” a correÃ§Ã£o que fica sÃ³ no servidor nÃ£o Ã© correÃ§Ã£o visÃ­vel.
- DivergÃªncia tela-vs-servidor Ã© bug: se o texto exibido difere do processado,
  o usuÃ¡rio vÃª "erro".

## Conexoes

- [[cluster-hub-programacao]]