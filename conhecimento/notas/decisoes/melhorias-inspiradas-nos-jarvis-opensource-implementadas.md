---
tags: [decisao, encaixam, mudança, mínima, opencode, reinventar]
aliases: [Melhorias inspiradas nos Jarvis opensource — implementadas]
date: 2026-08-30
---

# Melhorias inspiradas nos Jarvis opensource — implementadas

**Fonte:** opencode

---
titulo: Melhorias inspiradas nos Jarvis opensource implementadas
tipo: decisao
tags: [jarvis, voz, stt, whisper, eco, narracao, memoria, lgpd, contexto]
data: 2026-08-29
---

# Melhorias inspiradas nos Jarvis opensource — implementadas

## Contexto

A partir da análise de isair/jarvis, heardlabs/heard e Priler/jarvis (aprendizado 2026-08-29-jarvis-opensource-analise.md), foram implementadas 8 melhorias no ecossistema. Todas passaram no preflight técnico e ético.

## Decisões e implementações

1. **Filtros de alucinação do Whisper** (vox_audio.py): segmentos com `no_speech_prob > VOX_WHISPER_NO_SPEECH (0.5)` ou `avg_logprob < VOX_WHISPER_MIN_LOGPROB (-2.0)` são descartados. Mata transcrições fantasmas em silêncio/ruído. Configurável por env.

2. **Detecção de eco do TTS** (dialogo.py): a última fala do Jarvis é registrada (normalizada) e comparada com a transcrição ouvida via SequenceMatcher. Similaridade ≥ VOX_ECO_SIMILARIDADE (0.8) dentro de VOX_ECO_JANELA_S (8s) = eco, descartado.

3. **Juiz de intenção** (dialogo.py): LLM pequeno opcional (VOX_INTENT_LLM=1) via llm_caller com fallback determinístico sempre ativo. Classifica comando/pergunta/saudacao/interrupcao/eco. Interrupções ("para", "chega") não viram pergunta — o loop VAD responde "Entendido, parando".

4. **Redação automática de dados sensíveis** (memory_engine.py): emails, chaves (sk-/ghp/AKIA/AIza), JWT, senhas em pares, cartões, CPF/CNPJ são substituídos por marcadores antes de persistir (LGPD/GDPR). Desativável via MEMORY_REDACT=0.

5. **Modos de escuta da narração** (narracao_modo.py + widget_edge.py): copilot (default, atual), companion (briefing contínuo) e focus (só alertas). Estado em runtime/narracao_modo.json. O filtro `_deve_narrar` consulta o modo para decidir o motivo "sem relevancia".

6. **Saliência multi-agente** (agent_council.py): `escolher_saliente()` prioriza bloqueio/oposição > risco > preocupação > proposta. `narrar_saliencia()` gera texto pronto para voz: um agente em detalhe, os outros em resumo.

7. **Catch me up** (runtime_state.py + dialogo.py): `gerar_catch_up()` resume notas do histórico + pendências abertas. Injetado na saudação por voz do diálogo; CLI `python scripts/runtime_state.py catchup`.

8. **Digest passes para modelos pequenos** (runtime_context.py + jarvis_bridge.py): `digest_contexto()` condensa contexto de memória (cabeçalho + corpo enxuto + fecho). Ativa por LLM_DIGEST_ENABLED=1 ou "auto" para modelos ≤7B. Aplicado no `_montar` da bridge.

## Verificação

- `python -m py_compile` em todos os arquivos alterados: OK.
- Testes de função: redação, digest, modos, catch up, eco, juiz de intenção e saliência passaram.
- `preflight_check.py`: TODOS os testes passaram (inclui preflight ético).

## Regra aprendida

Padrões validados de projetos Jarvis maduros (filtros de alucinação, anti-eco, juiz de intenção, narração por relevância, digest de contexto) se encaixam no ecossistema com mudança mínima e configurável via env — sem reinventar.

## Possíveis melhorias futuras

- Calibrar os thresholds de alucinação com o modelo real (base) em ruído.
- Juiz de intenção por LLM ligado por padrão quando a latência permitir.
- Expor os modos de escuta no widget Edge.

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]