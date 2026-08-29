---
tags: [cognitivo, deveriam, errors, falados, general, recent]
aliases: [vazamento caracteres tts edge tts escapa ssml]
date: 2026-08-04
---

# vazamento caracteres tts edge tts escapa ssml

**Dominio:** general

---
tipo: erro
tags: [tts, edge-tts, ssml, ponte-de-voz, jarvis-bridge]
data: 2026-08-02
contexto: Usuário reportou que, no início das conversas, antes de falar "David", o Jarvis pronunciava caracteres que não deveriam. Investigação da saudação revelou causa na camada de TTS.
decisao: edge-tts >= 7.x removeu suporte a SSML custom. O __init__ do Communicate() aplica escape() em todo o texto, convertendo < e > em &lt; e &gt;. Assim, tags <break>, <phoneme>, <say-as> e <prosody> nunca são interpret

---
tipo: erro
tags: [tts, winerror, lock, escrita-atomica, voz]
data: 2026-08-20
contexto: O usuário reportou uma mensagem de erro no widget em quadro vermelho mostrando "falha de voz: [WinError 5] Acesso negado" na renomeação de runtime/tts_cmd.tmp para runtime/tts_cmd.json. O quadro vermelho do widget exibe erros reais lidos dos logs (função _ler_recent_errors).
decisao: Adicionar retry na escrita atômica do tts_cmd.json nos três pontos que escrevem: _enviar_tts_cmd (novo helper) em narrador_

---
tipo: erro
tags: [tts, normalizador, respiracao, numerais, ponte-voz, text-normalizer, jarvis-bridge]
data: 2026-08-29
contexto: O pipeline de TTS (V2, SpeechPipeline) passou a expandir números, datas e horas por extenso em pt-BR. O processo de respiração (vírgula em orações longas) passou a inserir vírgula DENTRO de numerais falados: "trinta, e um de julho", "quarenta, e quatro". Isso aconteceu porque o conector "e" interno dos numerais por extenso casava com o padrão de respiração CONECTOR
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]