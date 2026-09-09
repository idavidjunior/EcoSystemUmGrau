---
tipo: erro
tags: [cognitive-core, bug, contrato, str-vs-dict, memoria, contexto]
data: 2026-09-09
contexto: Bug real encontrado ao chamar scripts.cognitive_core.process_user_input via POST /api/chat (Ciclo 4). _get_memory_context retornava str formatada, mas o fluxo esperava dict.
decisao: Normalizar o contrato em 3 pontos: (1) execute_cognitive_cycle agora envolve o contexto de memória em {"memory_context": ...} antes de .update(contexto_override); (2) _execute_conversation_flow trata cada memória como dict ou str em mem_summaries; (3) relevant em formato str vira [{"conteudo": ...}] em vez de fatiar caracteres.
impacto: process_user_input passou a responder sem AttributeError ('str' object has no attribute 'get'/'update'); validado por probe e pelos 11 checks do Ciclo 4.
---

# Bug no cognitive_core — contrato de memória string vs dict

## Sintomas

- `AttributeError: 'str' object has no attribute 'get'` em `_execute_conversation_flow` ao construir `mem_summaries` com `m.get("conteudo", "")`.
- `AttributeError: 'str' object has no attribute 'update'` em `execute_cognitive_cycle` ao fazer `base_context.update(contexto_override)`.

## Causa raiz

`_get_memory_context` delega a `memory_engine.get_context` / `memory_consolidation.get_context_hybrid`, que retornam **string multiline formatada**, enquanto os chamadores esperavam `dict` de memórias.

## Correção aplicada (scripts/cognitive_core.py)

- `execute_cognitive_cycle` (linha ~548): `base_context = {"memory_context": base_context}` quando o resultado vier como str, então usa `.update(contexto_override)` com segurança.
- `_execute_conversation_flow` (linha ~756): `mem_summaries` normaliza cada item — `m.get("conteudo", "")` se for dict, senão `str(m)`.
- `_execute_conversation_flow` (linha ~738): se `relevant` for str, `memories = [{"conteudo": relevant}]` (antes `relevant[:3]` fatiava caracteres soltos).

## Validação

Probe `process_user_input` (conversation e task) → sem erro, response e summary completos; `test_ia_chat.py` do Ciclo 4 → 11 checks OK. Bug de contrato string/dict é padrão recorrente em memória do ecossistema — conferir outros consumidores de `get_context`/`get_context_hybrid` ao integrar.

## Conexoes

- [[acoustid-always-fails]]
- [[album-art-not-found]]
- [[artist-shows-desconhecido]]
- [[audio-stops-eq-not-audible]]
- [[authjson-com-entradas-de-chave-nvidia-disfarcadas-de-outros-]]
- [[cliques-em-coordenadas-erram-alvo-em-resolutions-diferentes]]
- [[cliques-falhando-em-spa-apos-navegacao]]
- [[code-duplication-entre-checkpointpy-e-persistencepy-200-linh]]
- [[dropdownselect-nao-responde-a-sendkeys-ou-click]]
- [[duplicate-mini-player-on-some-screens]]
- [[elementos-nao-encontrados-em-shadow-dom]]
- [[ensureserve-spawns-opencode-serve-without-passing-env-contex]]
- [[eq-deactivates-on-song-change]]
- [[eq-distorts-audio-at-boost-settings]]
- [[eq-only-applies-after-opening-fragment]]
- [[eq-state-not-persisted]]
- [[eq-still-distorts-at-high-boost]]
- [[eq-toggle-button-not-visible]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[executorresults-sem-limite-memoria-crescia-indefinidamente]]
- [[filename-ambiguity]]
- [[first-search-returns-nothing]]
- [[geraraudio-blocks-until-full-tts-generation-no-streaming]]
- [[http-401-unauthorized-on-session-and-globalsessions]]
- [[logs-dont-appear]]
- [[logs-sem-rotacao-logs-cresciam-indefinidamente]]
- [[loop-infinito-de-push-no-vigilante-emails-do-github-a-cada-m]]
- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]
- [[mcp-server-failed-to-get-tools-no-opencode]]
- [[mcp-server-nao-respondia-a-toolscall]]
- [[mcp-server-nao-respondia-nenhum-comando]]
- [[nao-havia-feedback-loop-do-usuario-ler-terminava-mesmo-se-ob]]
- [[no-eq-onoff-button]]
- [[no-most-played-tracking]]
- [[no-visual-limiting-feedback]]
- [[opencode-go-provider-crash-ao-processar-mensagem]]
- [[permission-dialogs-do-miui-bloqueiam-instalacao-de-apk]]
- [[persistencia-sem-atomicidade-crash-no-meio-do-jsondump-corro]]
- [[preamp-not-audible]]
- [[preamp-volume-irreversible-and-cumulative]]
- [[preset-data-corrupted-on-ptbr-locale]]
- [[preset-not-persisting-across-sessions]]
- [[score-threshold-mas-sem-failedsteps-ia-direto-para-successve]]
- [[search-returns-wrong-artist]]
- [[sendkeys-nao-funciona-em-campos-rich-text]]
- [[stt-no-partialstreaming-results]]
- [[track-the-best-score-across-all-results-and-only-return-if-m]]
- [[use-explicit-redirect-following-in-download-function-manual-]]
- [[user-sees-wrongshort-results]]
- [[voxaudioplayer-temp-file-leak-on-exception]]