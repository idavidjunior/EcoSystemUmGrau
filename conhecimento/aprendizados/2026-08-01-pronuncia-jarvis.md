# Pronúncia "Járvis" (escrita sem acento, fala com acento)

- **Data:** 01/08/2026
- **Sessão:** Pedido direto do usuário sobre pronúncia do nome do assistente

## Regra permanente
- **Escrita:** sempre "Jarvis", **sem acento**.
- **Pronúncia (fala/TTS):** "Járvis" — acento tônico no primeiro A (JA-rvis, fonético: /ËˆÊ’aÊ.vis/).
- Nunca pronunciar "Jár-vis" com o segundo A fechado nem com acento na última sílaba ("Jarvís").

## Implementação
- Registrado em `scripts/pronuncias.json`:
  `"jarvis": {"ipa": "/ËˆÊ’aÊ.vis/"}`
- O `gerar_audio` (jarvis_bridge.py) aplica SSML `<phoneme alphabet="ipa" ph="/ËˆÊ’aÊ.vis/">Jarvis</phoneme>`
  quando a palavra aparece no texto — a escrita permanece "Jarvis" (sem acento) e só a fala usa a pronúncia com acento.

## Validação
- `aplicar_phonemes('Jarvis, ...')` â†’ `'<phoneme alphabet="ipa" ph="/ËˆÊ’aÊ.vis/">Jarvis</phoneme>'` âœ“
- Ãudio real gerado e tocado com a pronúncia correta âœ“

## Mecanismo `fala` — pronúncia garantida (01/08/2026)
- O edge-tts **ignora** SSML `<phoneme>` em alguns casos (ex.: "GitHub" continuava com som de J).
- Para esses casos, registrar `"palavra": {"fala": "Guitirrãbi"}` em `pronuncias.json`.
- `aplicar_phonemes` substitui a palavra pela grafia falada **só no áudio**; a tela mostra a ortografia correta.
- É a técnica definitiva para nomes próprios e termos estrangeiros (GitHub, OpenAI, WhatsApp, NVIDIA...).

## Aprendizado contínuo de pronúncia (regra permanente)
1. **Ouça e compare** — sempre que houver dúvida, gere o áudio e compare com a pronúncia natural.
2. **Consulte outras fontes e LLMs** — dicionários, wikis, referências fonéticas e outras LLMs para a pronúncia mais natural.
3. **Seja curioso e proativo** — nomes, marcas, termos técnicos e topônimos novos devem ter pronúncia verificada antes de falar.
4. **Prefira a pronúncia natural do PB** — termos estrangeiros no contexto brasileiro como um nativo diria (ex.: GitHub â†’ Guitirrãbi).
5. **Registre sempre** — toda pronúncia corrigida vai para `pronuncias.json` (`fala` ou `ipa`) e vale no próximo áudio.
6. **Nunca deforme a escrita** — a substituição é só na fala.
