---
tags: [decisao, false, kwargs, opencode, passar, pelo]
aliases: [canal voz rapida nvidia]
date: 2026-09-05
---

# canal voz rapida nvidia

**Fonte:** opencode

---
tipo: decisao
tags: [voz, bridge, nvidia, latencia, canal-voz]
data: 2026-09-04
contexto: Percurso "Envio o audio e o EcoSystemUmGrau ouve e responde" sofria 35-45s por pergunta com timeouts de 120s e quedas de conexao.
decisao: Implementar canal de voz rapido em jarvis_bridge.py (_voz_rapida) chamando NVIDIA direta com cadeia de modelos testados e thinking desligado (chat_template_kwargs thinking=False), sem passar pelo opencode serve. Cadeia: nemotron-3.5-lightning-30b-a3b (~1-3s), gpt-oss-20b (~3-5s), kimi-k3 (~5s), deepseek-v4-flash (reserva). Override via env VOZ_RAPIDA_MODELOS. Prompt minimo SISTEMA_VOZ_RAPIDA (~2KB). Fallback continua: fluxo normal via serve quando a cadeia falha inteira.
impacto: Resposta de voz caiu de ~40s para ~5s no caminho rapido (medido em pico real: gpt-oss em 4.9s). A cadeia opencode.ai (opencode/*) retorna 403 e nunca teve sucesso (ok=0 em 7 modelos) - nao usar como alternativa funcional. // ---
tipo: decisao
tags: [voz, bridge, nvidia, latencia, canal-voz]
data: 2026-09-04
contexto: Percurso "Envio o audio e o EcoSystemUmGrau ouve e responde" sofria 35-45s por pergunta com timeouts de 120s e quedas de conexao.
decisao: Implementar canal de voz rapido em jarvis_bridge.py (_voz_rapida) chamando NVIDIA direta com cadeia de modelos testados e thinking desligado (chat_template_kwargs thinking=False), sem passar pelo opencode serve. Cadeia: nemotron-3.5-lightning-30b-a3b (~1-3s), gpt-oss-20b (~3-5s), kimi-k3 (~5s), deepseek-v4-flash (reserva). Override via env VOZ_RAPIDA_MODELOS. Prompt minimo SISTEMA_VOZ_RAPIDA (~2KB). Fallback continua: fluxo normal via serve quando a cadeia falha inteira.
impacto: Resposta de voz caiu de ~40s para ~5s no caminho rapido (medido em pico real: gpt-oss em 4.9s). A cadeia opencode.ai (opencode/*) retorna 403 e nunca teve sucesso (ok=0 em 7 modelos) - nao usar como alternativa funcional.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]