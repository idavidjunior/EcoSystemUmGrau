# Pronúncia "Járvis" (escrita sem acento, fala com acento)

- **Data:** 01/08/2026
- **Sessão:** Pedido direto do usuário sobre pronúncia do nome do assistente

## Regra permanente
- **Escrita:** sempre "Jarvis", **sem acento**.
- **Pronúncia (fala/TTS):** "Járvis" — acento tônico no primeiro A (JA-rvis, fonético: /ˈʒaʁ.vis/).
- Nunca pronunciar "Jár-vis" com o segundo A fechado nem com acento na última sílaba ("Jarvís").

## Implementação
- Registrado em `scripts/pronuncias.json`:
  `"jarvis": {"ipa": "/ˈʒaʁ.vis/"}`
- O `gerar_audio` (jarvis_bridge.py) aplica SSML `<phoneme alphabet="ipa" ph="/ˈʒaʁ.vis/">Jarvis</phoneme>`
  quando a palavra aparece no texto — a escrita permanece "Jarvis" (sem acento) e só a fala usa a pronúncia com acento.

## Validação
- `aplicar_phonemes('Jarvis, ...')` → `'<phoneme alphabet="ipa" ph="/ˈʒaʁ.vis/">Jarvis</phoneme>'` ✓
- Áudio real gerado e tocado com a pronúncia correta ✓
