---
tags: [2026, analise, aprendizado, ativo, decisao, opencode]
aliases: [Melhorias inspiradas nos Jarvis opensource — implementadas]
date: 2026-08-30
---

# Melhorias inspiradas nos Jarvis opensource — implementadas

**Fonte:** opencode

## Contexto

A partir da análise de isair/jarvis, heardlabs/heard e Priler/jarvis (aprendizado 2026-08-29-jarvis-opensource-analise.md), foram implementadas 8 melhorias no ecossistema. Todas passaram no preflight técnico e ético.

## Decisões e implementações

1. **Filtros de alucinação do Whisper** (vox_audio.py): segmentos com `no_speech_prob > VOX_WHISPER_NO_SPEECH (0.5)` ou `avg_logprob < VOX_WHISPER_MIN_LOGPROB (-2.0)` são descartados. Mata transcrições fantasmas em silêncio/ruído. Configurável por env.

2. **Detecção de eco do TTS** (dialogo.py): a última fala do Jarvis é registrada (normalizada) e comparada com a transcrição ouvida via SequenceMatcher. Similaridade ≥ VOX_ECO_SIMILARIDADE (0.8) dentro de VOX_ECO_JANELA_S (8s) = eco, descartado.

3. **Juiz de intenção** (dialogo.py): LLM pequeno opcional (VOX_INTENT_LLM=1) via llm_caller com fallback determinístico sempre ativo. Classifica comando/pergunta/saudacao/interrupcao/eco. Interrupções ("para", "chega") não viram pergunta
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]