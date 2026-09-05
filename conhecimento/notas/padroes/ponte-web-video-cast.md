---
tags: [instantbits, intent, obras, opencode, pacote, padrao]
aliases: [ponte web video cast]
date: 2026-08-09
---

# ponte web video cast

**Fonte:** opencode

Tipo: padrao

Tags: [streamumgrau, cast, web-video-cast, tv, url-launcher]

Data: 2026-08-09

Contexto: Usuario pediu ponte do catalogo do StreamUmGrau com o app Web Video Cast para assistir obras na TV.

Decisão: Implementado botao "Assistir na TV" na DetailView que delega ao Web Video Cast (InstantBits). Sem URL de video no catalogo, a ponte abre o app pelo pacote (intent://) para o usuario buscar; com videoUrl futuro, usa o scheme oficial wvc-x-callback://open. Fallback: Play Store.

Impacto: App nao embute reprodutor nem agregador de fontes; WVC faz a ponte com Chromecast/Roku/Fire TV/DLNA. url_launcher ^6.3.0 adicionado.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]