---
tipo: erro
tags: [watchdog, powershell, bug, resiliencia]
data: 2026-08-06
contexto: Certificacao forense de processos no watchdog.ps1 (Test-ForensicoLixo / Invoke-KillCertificado)
decisao: Renomear parametro [int]Pid para [int]ProcessId nas funcoes forenses
impacto: Evita que o watchdog mate o proprio processo (variavel automatica PID read-only)
---

# Bug: parametro Pid e variavel automatica do PowerShell

## Sintoma
A funcao `Test-ForensicoLixo` e `Invoke-KillCertificado` declaravam `[int]$Pid` como
parametro. No PowerShell, `$PID` e uma variavel AUTOMATICA read-only que contem o PID
do processo atual. Com `$ErrorActionPreference = "SilentlyContinue"`, a atribuicao do
parametro falhava em silencio e `$Pid` dentro da funcao referenciava o PID do proprio
watchdog.

## Risco real
O watchdog poderia certificar e matar a SI MESMO (ou o PID errado), quebrando a
resiliencia que deveria proteger.

## Correcao aplicada
- Parametros renomeados para `$ProcessId` em `Test-ForensicoLixo` e `Invoke-KillCertificado`.
- Todas as chamadas no loop atualizadas (`-ProcessId`).
- Tambem corrigido `Write-Log "..." + (array)` que virava argumentos posicionais
  descartados — perdendo a auditoria dos motivos. Agora usa interpolacao.

## Validacao
- Sintaxe: SINTAXE OK (PSParser).
- Teste seco: explorer fingindo ser python -> BLOQUEADO com motivos auditaveis.
- Teste seco: processo supervisionado (pai vivo) -> BLOQUEADO (comportamento conservador).
- Watchdog reiniciado (PID 2172), health-checks bridge/serve OK, desktop intocado (8 procs).
- Teste de resiliencia: serve derrubado -> detectado e reiniciado pelo watchdog em <60s.

## Licao
Em PowerShell, NAO usar `$Pid`/`$PID` como nome de variavel propria: e reservada.
Sempre auditar logs de auditoria em Write-Log com interpolacao, nao concatenacao "+".

## Memorias relacionadas
- #130 (padrao): Watchdog resiliente com lock de PID e protecao do desktop.
- #134 (padrao): Certificacao forense de processos + boot via Startup (usa estas funcoes).

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