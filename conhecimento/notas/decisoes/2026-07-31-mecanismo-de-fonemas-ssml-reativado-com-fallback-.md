---
tags: [algumas, decisao, marcaã, opencode, versã, vozes]
aliases: [# 2026-07-31 - Mecanismo de fonemas SSML reativado com fallb]
date: 2026-08-10
---

# # 2026-07-31 - Mecanismo de fonemas SSML reativado com fallback seguro

**Fonte:** opencode

# 2026-07-31 - Mecanismo de fonemas SSML reativado com fallback seguro

**Categoria:** decisao
**Fonte:** sessao_jarvis_vox
**Gravidade:** media

## Contexto

O usuÃ¡rio pediu para ligar o mecanismo de fonemas (`aplicar_phonemes` + SSML `<phoneme>` do edge-tts) na bridge do Jarvis.

## VerificaÃ§Ãµes

1. edge-tts 7.2.8 aceita SSML `<phoneme alphabet="ipa">` sem erro (testado com Ã¡udio real).
2. `aplicar_phonemes()` jÃ¡ estava conectado em `gerar_audio()`, mas **sem fallback**: se o SSML falhasse, a geraÃ§Ã£o de Ã¡udio quebraria.
3. O dicionÃ¡rio `pronuncias.json` tinha sÃ³ `david`.

## DecisÃ£o

Reescrevi `gerar_audio()` com fallback em dois nÃ­veis:
- Tenta SSML com fonemas primeiro (se houver palavras no dicionÃ¡rio).
- Se falhar, cai para texto puro (melhorar_fala jÃ¡ aplicado).
- Se ambos falharem, retorna Ã¡udio vazio (em vez de exception quebrando a resposta).

## Teste

- `gerar_audio` com e sem fonemas: OK (base64 gerado).
- Ponte a ponta via WebSocket: saudaÃ§Ã£o + resposta com Ã¡udio OK.
- Bridge reiniciada (PID novo) carregando o cÃ³digo atualizado.
- `python -m py_compile jarvis_bridge.py`: OK.

## LiÃ§Ã£o

Sempre que ativar SSML/fonemas no TTS, manter o caminho de texto puro como fallback â€” o edge-tts pode rejeitar marcaÃ§Ãµes em algumas vozes/versÃµes.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]