---
tags: [algumas, decisao, marcações, opencode, versões, vozes]
aliases: [# 2026-07-31 - Mecanismo de fonemas SSML reativado com fallb]
date: 2026-08-22
---

# # 2026-07-31 - Mecanismo de fonemas SSML reativado com fallback seguro

**Fonte:** opencode

# 2026-07-31 - Mecanismo de fonemas SSML reativado com fallback seguro

**Categoria:** decisao
**Fonte:** sessao_jarvis_vox
**Gravidade:** media

## Contexto

O usuário pediu para ligar o mecanismo de fonemas (`aplicar_phonemes` + SSML `<phoneme>` do edge-tts) na bridge do Jarvis.

## Verificações

1. edge-tts 7.2.8 aceita SSML `<phoneme alphabet="ipa">` sem erro (testado com áudio real).
2. `aplicar_phonemes()` já estava conectado em `gerar_audio()`, mas **sem fallback**: se o SSML falhasse, a geração de áudio quebraria.
3. O dicionário `pronuncias.json` tinha só `david`.

## Decisão

Reescrevi `gerar_audio()` com fallback em dois níveis:
- Tenta SSML com fonemas primeiro (se houver palavras no dicionário).
- Se falhar, cai para texto puro (melhorar_fala já aplicado).
- Se ambos falharem, retorna áudio vazio (em vez de exception quebrando a resposta).

## Teste

- `gerar_audio` com e sem fonemas: OK (base64 gerado).
- Ponte a ponta via WebSocket: saudação + resposta com áudio OK.
- Bridge reiniciada (PID novo) carregando o código atualizado.
- `python -m py_compile jarvis_bridge.py`: OK.

## Lição

Sempre que ativar SSML/fonemas no TTS, manter o caminho de texto puro como fallback — o edge-tts pode rejeitar marcações em algumas vozes/versões.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]