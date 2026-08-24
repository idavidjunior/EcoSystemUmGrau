---
tipo: padrao
tags: [auditoria, bug, debugging, fluxo, ferramentas-autoritativas, auto-evolucao, skill]
data: 2026-08-09
contexto: "Auditoria do painel StreamUmGrau revelou que a leitura linear de arquivos (display) corrompe, trunca e duplica conteúdo, gerando conclusões erradas. Bugs reais (controle #mastodon-login invisível, crashes) só foram encontrados escaneando o fluxo de dados e validando com ferramentas autoritativas."
decisao: "Criada skill auditoria-de-codigo (auto-evolutiva) em mcp/desenvolvimento/habilidades/auditoria-de-codigo/ com pipeline de 5 fases: (1) escanear por fluxo com matrizes de localStorage/eventos/funções; (2) verificar com ferramentas autoritativas (py_compile, node --check por bloco isolado, bytes hex); (3) corrigir no fonte, nunca no artefato gerado; (4) rastrear dado vs código (mojibake em dados do vault não é bug do gerador); (5) pensar efeitos colaterais (restore vs init, reset vs defaults, toggle vs layout, !important vs inline). Espelhada em ~/.claude/skills/auditoria-de-codigo/ para o opencode carregar."
impacto: "Skill carregável pelo opencode que auto-evolui: ao final de cada auditoria registra aprendizado (memory_engine + conhecimento/aprendizados) e append em evolucao.md; a partir de 3 aprendizados novos revisa o próprio SKILL.md dobrando padrões no checklist de armadilhas. Cobre o padrão mestre: 'quando o usuário aponta um controle de UI, há um bug ali'."
---

# Aprendizado: Skill auditoria-de-codigo (auto-evolutiva)

## Resumo

Criada skill declarativa de auditoria de código com auto-evolução, espelhada no
deploy do opencode.

## Padrões consolidados

1. **Bugs são encontrados pelo fluxo, não pela leitura** — mapear matrizes
   `chave → grava → lê → status` (localStorage), `gatilho → handler → efeito`
   (eventos), `origem → destino` (funções).
2. **Ferramentas autoritativas** — `py_compile`, `node --check` por bloco
   isolado, contagens regex e bytes hex; nunca confiar no display de arquivos.
3. **Corrigir no fonte** — editar o gerador, rebuild, revalidar; artefato gerado
   é sombra.
4. **Dado vs código** — sintoma persistente pode ser dado ruim de fonte externa
   (vault/notas), não bug do gerador; separar e reportar.
5. **Efeitos colaterais** — cada correção contra o resto (restore vs init,
   reset vs defaults, toggle vs layout, `!important` vs inline, timing de
   animações).

## Mecanismo de auto-evolução

- Ao fim de cada auditoria: `memory_engine.py add`, arquivo em
  `conhecimento/aprendizados/`, append em `evolucao.md`.
- Revisão do próprio SKILL.md quando 3+ aprendizados acumulam ou fase falha.

## Próximos passos

- Revisar o SKILL.md conforme auditorias reais forem registrando aprendizados.
- Manter espelho `~/.claude/skills/auditoria-de-codigo/SKILL.md` em sincronia
  com o canônico no repo.

## Conexoes

- [[acoustid-always-fails]]
- [[album-art-not-found]]
- [[artist-shows-desconhecido]]
- [[audio-stops-eq-not-audible]]
- [[authjson-com-entradas-de-chave-nvidia-disfarcadas-de-outros-]]
- [[cliques-em-coordenadas-erram-alvo-em-resolutions-diferentes]]
- [[cliques-falhando-em-spa-apos-navegacao]]
- [[code-duplication-entre-checkpointpy-e-persistencepy-200-linh]]
- [[debugging-em-cascata-reversa]]
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