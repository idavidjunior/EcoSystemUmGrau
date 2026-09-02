---
tipo: erro
tags: [aderencia, preflight, adherencia-audit, metrica, bug]
data: 2026-09-02
contexto: O @sync reportava @sync FAIL por metricas de aderencia baixas (inventario 15.8%, preflight 25%). Investigacao revelou bugs reais em duas metricas e um falso positivo no deploy config.
decisao: Correcao de 3 frentes para elevar o score geral de aderencia de 69.6 para 93.4/100.
impacto: @sync agora PASS (thresholds OK). Score EXCELENTE.
---

# Correção de métricas de aderência (@sync)

## 1. Bug na métrica preflight_entregas (erro crítico)

Em `scripts/adherence_audit.py`, o `parse_git_log` usava `--date=short` no git log, retornando apenas a data do commit (YYYY-MM-DD) sem hora. O parse `datetime.strptime(c['date'], '%Y-%m-%d')` criava meia-noite do dia. A comparação `p < e['date']` então exigia preflight ANTES da meia-noite do dia do commit, excluindo todos os preflights do mesmo dia.

Resultado: de 4 entregas, só 1 contava como "com preflight" (25%) mesmo com 415+ execuções reais de preflight.

Correção: usar `--date=iso` no git log e `datetime.fromisoformat` (removendo tzinfo) para capturar o timestamp completo do commit. Métrica subiu de 25% para 100% (7d) e 92.3% (30d).

## 2. Métrica de inventário (15.8% -> 100%)

O `config/inventario_estruturas.json` não refletia 82 estruturas novas no disco. Rodar `scripts/inventory_manager.py sync` detectou e registrou automaticamente (scripts core, habilidades MCP, agentes). O item `test_widget_live.py` estava listado mas inexistente no disco — removido com `inventory_manager.py remove` para manter integridade. `inventory_manager.py verify` passou com 0 erros.

## 3. Deploy config rollback — FALSO POSITIVO

A observação de "rollback de deploy config por incompatibilidade no template" era um diagnóstico incorreto. O template `config/opencode.jsonc` usa placeholders `{{USERPROFILE}}` por design (o preflight_check.py expande na linha 84-86 e valida que o deployed não contenha o placeholder não expandido na linha 339-341). A diferença entre template (com placeholder) e deployed (renderizado) é esperada, não incompatibilidade.

Ações reais tomadas: atualizado o model desatualizado no template (`deepseek-v4-flash` -> `deepseek-v4-flash-0731`) e limpos backups residuais obsoletos (`opencode.jsonc.bak2`, `.full`, `.backup`) no diretório deploy.

## Anomalia detectada no gate (registrar como observação)

No `persistencia.ps1 status`, o log mostra: `PREFLIGHT: repositorio sem scripts/preflight_check.py, preflight pulado` várias vezes. O preflight_check.py existe na raiz, mas o gate parece rodar o preflight de um cwd onde o script não é encontrado. Vale investigar o `persistencia.ps1` para garantir que o preflight do gate roda no diretório correto.

## Resultado final

Score de aderência subiu de 69.6 para 93.4/100 (EXCELENTE). @sync PASS. Inventário 100%, Preflight 100%, Gate 92.2%, Boot 100%, pt-BR 100%.

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