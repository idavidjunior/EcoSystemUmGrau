---
tipo: erro
tags: [calculadora, supermarket, precedencia, bug, idempotencia-igual, android, puresdk]
data: 2026-09-03
contexto: Reescrevi a tab Calculadora Simples (setupSimpleCalc da MainActivity.java do SupermarketCalculator, pure SDK) para aceitar expressão completa com precedência matemática e corrigir o bug do botão = que recalculava ao apertar repetidamente.
decisao: Avalei a expressão tokenizada com precedência ×÷ antes de +− (esquerda-direita) via BigDecimal. O handler op, no caso pós-=, monta a base a partir do resultado mas precisa zerar o flag scLastWasEquals, senão o próximo dígito dispara resetCalc() e perde toda a expressão.
impacto: Exemplo validado no dispositivo real: 5+8+4+8÷4×2 = 21 (precedência correta). = repetido é idempotente (não recalcula). Novo número após = inicia conta nova. Operador após = continua a partir do resultado (21+3=24). Todos os critérios de aceitação do usuário verificados via ADB (toques + uiautomator dump).
---

## Bug do botão = que recalculava

A calculadora simples (tab Simples da MainActivity.java) foi reescrita para aceitar expressão completa, com visor mostrando a equação e o resultado em tempo real com precedência matemática.

## Causa raiz

No handler `op` (operador), o bloco `if (scLastWasEquals)` montava os tokens com a base (`scTokens.add(scCurNum)`), mas não zerava `scLastWasEquals`. Com o flag ainda true, ao digitar o próximo número o handler `num` (`if (scLastWasEquals) resetCalc()`) resetava tudo, perdendo a expressão. Ex.: 21 = + 3 mostrava só "3" em vez de "21 + 3 = 24".

## Correção

Adicionar `scLastWasEquals = false;` dentro do bloco `if (scLastWasEquals)` do handler `op`, após montar a base e o operador.

## Validação no dispositivo (ADB)

- Expressão `5 + 8 + 4 + 8 ÷ 4 × 2` → resultado em tempo real 21 (precedência correta).
- `=` repetido é idempotente (mantém 21, não recalcula).
- Novo número após `=` inicia conta nova.
- Operador após `=` continua a partir do resultado: 21 + 3 = 24.

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