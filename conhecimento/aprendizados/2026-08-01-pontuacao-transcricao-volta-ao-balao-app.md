# Pontuação da transcrição voltando ao balão do app (corrigido)

- **Data:** 01/08/2026
- **Sessão:** Bug — "Que horas são" transcrito sem o sinal "?"

## Problema
O usuário perguntou "Que horas são" e o balão da transcrição no app não mostrava
o "?". A pontuação JÃ era aplicada pela bridge (`fix_punctuation`), mas o app
exibia a transcrição crua do STT — a correção nunca voltava para a tela.

## Causa raiz
- App (`VoxViewModel.onSttResult`): `mensagens + Mensagem(texto, true)` exibe o
  texto cru do SpeechRecognizer e envia só esse texto à bridge.
- Bridge (`lidar`): corrigia com `fix_punctuation` e usava o texto corrigido para
  o LLM/`caminho_rapido`, mas a resposta só trazia a fala do Jarvis (`text`).

## Solução (echo do texto corrigido)
1. **Bridge** (`jarvis_bridge.py` `lidar`): toda resposta de mensagem agora
   carrega `"corrigido": <texto pós-fix_punctuation>` — nos três caminhos
   (normal, texto-sem-audio e interrupção).
2. **App** (`VoxViewModel.onMessage`): se a resposta tem `corrigido` e a última
   mensagem é do usuário (`deUsuario`), substitui o balão pela versão corrigida
   (preservando imagem/mime).

## Validação
- WebSocket real: `que horas são` â†’ `corrigido: "Que horas são?"` (com `?`);
  `toca uma musica` â†’ `corrigido: "Toca uma musica."`.
- App compilado (`build.ps1 -Install`) e instalado via ADB no Redmi Note 11.

## Padrão capturado
- Quando a ponte transforma a entrada do usuário (pontuação, normalização), a
  versão transformada precisa **voltar ao app** para a tela refletir o que o
  Jarvis entendeu — a correção que fica só no servidor não é correção visível.
- Divergência tela-vs-servidor é bug: se o texto exibido difere do processado,
  o usuário vê "erro".
