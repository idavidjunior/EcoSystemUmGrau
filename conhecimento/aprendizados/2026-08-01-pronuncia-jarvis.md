# PronÃºncia "JÃ¡rvis" (escrita sem acento, fala com acento)

- **Data:** 01/08/2026
- **SessÃ£o:** Pedido direto do usuÃ¡rio sobre pronÃºncia do nome do assistente

## Regra permanente
- **Escrita:** sempre "Jarvis", **sem acento**.
- **PronÃºncia (fala/TTS):** "JÃ¡rvis" â€” acento tÃ´nico no primeiro A (JA-rvis, fonÃ©tico: /ËˆÊ’aÊ.vis/).
- Nunca pronunciar "JÃ¡r-vis" com o segundo A fechado nem com acento na Ãºltima sÃ­laba ("JarvÃ­s").

## ImplementaÃ§Ã£o
- Registrado em `scripts/pronuncias.json`:
  `"jarvis": {"ipa": "/ËˆÊ’aÊ.vis/"}`
- O `gerar_audio` (jarvis_bridge.py) aplica SSML `<phoneme alphabet="ipa" ph="/ËˆÊ’aÊ.vis/">Jarvis</phoneme>`
  quando a palavra aparece no texto â€” a escrita permanece "Jarvis" (sem acento) e sÃ³ a fala usa a pronÃºncia com acento.

## ValidaÃ§Ã£o
- `aplicar_phonemes('Jarvis, ...')` â†’ `'<phoneme alphabet="ipa" ph="/ËˆÊ’aÊ.vis/">Jarvis</phoneme>'` âœ“
- Ãudio real gerado e tocado com a pronÃºncia correta âœ“

## Mecanismo `fala` â€” pronÃºncia garantida (01/08/2026)
- O edge-tts **ignora** SSML `<phoneme>` em alguns casos (ex.: "GitHub" continuava com som de J).
- Para esses casos, registrar `"palavra": {"fala": "GuitirrÃ£bi"}` em `pronuncias.json`.
- `aplicar_phonemes` substitui a palavra pela grafia falada **sÃ³ no Ã¡udio**; a tela mostra a ortografia correta.
- Ã‰ a tÃ©cnica definitiva para nomes prÃ³prios e termos estrangeiros (GitHub, OpenAI, WhatsApp, NVIDIA...).

## Aprendizado contÃ­nuo de pronÃºncia (regra permanente)
1. **OuÃ§a e compare** â€” sempre que houver dÃºvida, gere o Ã¡udio e compare com a pronÃºncia natural.
2. **Consulte outras fontes e LLMs** â€” dicionÃ¡rios, wikis, referÃªncias fonÃ©ticas e outras LLMs para a pronÃºncia mais natural.
3. **Seja curioso e proativo** â€” nomes, marcas, termos tÃ©cnicos e topÃ´nimos novos devem ter pronÃºncia verificada antes de falar.
4. **Prefira a pronÃºncia natural do PB** â€” termos estrangeiros no contexto brasileiro como um nativo diria (ex.: GitHub â†’ GuitirrÃ£bi).
5. **Registre sempre** â€” toda pronÃºncia corrigida vai para `pronuncias.json` (`fala` ou `ipa`) e vale no prÃ³ximo Ã¡udio.
6. **Nunca deforme a escrita** â€” a substituiÃ§Ã£o Ã© sÃ³ na fala.

## Conexoes

- [[cluster-hub-programacao]]