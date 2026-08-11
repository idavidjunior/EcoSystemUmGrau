---
tipo: padrao
tags: [streamumgrau, cast, web-video-cast, tv, url-launcher]
data: 2026-08-09
contexto: Usuario pediu ponte do catalogo do StreamUmGrau com o app Web Video Cast para assistir obras na TV.
decisao: Implementado botao "Assistir na TV" na DetailView que delega ao Web Video Cast (InstantBits). Sem URL de video no catalogo, a ponte abre o app pelo pacote (intent://) para o usuario buscar; com videoUrl futuro, usa o scheme oficial wvc-x-callback://open. Fallback: Play Store.
impacto: App nao embute reprodutor nem agregador de fontes; WVC faz a ponte com Chromecast/Roku/Fire TV/DLNA. url_launcher ^6.3.0 adicionado.
validacao: flutter analyze limpo; 5 testes passando (novos: botao presente na DetailView + botao dispara intent do pacote com.instantbits.cast.webvideo); APK debug instalado no Redmi (mock local), WVC ja instalado no aparelho.
detalhes: Package com.instantbits.cast.webvideo. Intent oficial: ACTION_VIEW + video/* + setPackage. Scheme: wvc-x-callback://open?url=<encoded>. Play Store fallback: https://play.google.com/store/apps/details?id=com.instantbits.cast.webvideo. O modelo Midia nao ganhou campo video_url (nao ha URL no catalogo); o bridge aceita videoUrl opcional para uso futuro.

## Conexoes

- [[cluster-hub-programacao]]