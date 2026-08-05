---
tags: [cognitivo, david, deveriam, general, não, pronunciava]
aliases: [vazamento caracteres tts edge tts escapa ssml]
date: 2026-08-05
---

# vazamento caracteres tts edge tts escapa ssml

**Dominio:** general

---
tipo: erro
tags: [tts, edge-tts, ssml, ponte-de-voz, jarvis-bridge]
data: 2026-08-02
contexto: Usuário reportou que, no início das conversas, antes de falar "David", o Jarvis pronunciava caracteres que não deveriam. Investigação da saudação revelou causa na camada de TTS.
decisao: edge-tts >= 7.x removeu suporte a SSML custom. O __init__ do Communicate() aplica escape() em todo o texto, convertendo < e > em &lt; e &gt;. Assim, tags <break>, <phoneme>, <say-as> e <prosody> nunca são interpret
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]