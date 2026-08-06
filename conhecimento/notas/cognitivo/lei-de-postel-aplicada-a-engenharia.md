---
tags: [architecture, cognitivo, explicitos, externos, recuperaveis, silenciosamente]
aliases: [Lei de Postel aplicada a engenharia]
date: 2026-08-06
---

# Lei de Postel aplicada a engenharia

**Dominio:** architecture

'Seja conservador no que voce envia, seja liberal no que voce aceita.' Outputs devem ser rigorosos (validacao estrita, tipos fortes, contratos explicitos). Inputs devem ser tolerantes (defaults, fallbacks, parsing flexivel). Isso cria sistemas que funcionam com peers imperfeitos sem propagar erros. Exemplo pratico: seu modulo deve falhar ruidosamente em erros internos mas silenciosamente em erros externos recuperaveis.
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]
- [[projete-para-falha-nao-para-sucesso]]
- [[state-deve-ser-explícito-nunca-implícito]]