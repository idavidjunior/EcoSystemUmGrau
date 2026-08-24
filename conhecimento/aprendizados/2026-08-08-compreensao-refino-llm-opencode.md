---
tipo: padrao
tags: [compreensao, llm, opencode, resiliencia, mcp]
data: 2026-08-08
contexto: Modulo compreensao-pedidos refinava via NVIDIA/OpenAI/Anthropic (lentas/indisponiveis). Usuario pediu conectar a LLM padrao do opencode como primaria e manter NVIDIA como backup.
decisao: Refino usa `opencode run --agent compreensao-refino -m <modelo> --format json` (LLM da sessao, sem chave extra). Backup: NVIDIA -> OpenAI -> Anthropic. Fail-soft preservado.
impacto: Refino estruturado em ~20-26s (antes: timeout NVIDIA). Resiliencia em cadeia: se a primaria nao responde, o backup entra; se tudo falha, `llm_refino.usado:false` e a compreensao estatica nunca quebra.
---

# Compreensao de pedidos: refino com a LLM do opencode (primaria) + backups

## Problema
O refino opcional do modulo `compreensao-pedidos` chamava NVIDIA via litellm.
NVIDIA dava timeout (30/60s) e o refino ficava inutil na pratica.

## Solucao implementada
1. **`_refinar_via_opencode`** em `compreensao.py`: chama `opencode run --agent
   compreensao-refino -m {COMPREENSAO_MODELO_OPENCODE|LLM_MODEL|opencode/big-pickle}
   --format json "<prompt>"` e extrai os eventos `type=text` do stream.
2. **Agente `compreensao-refino`** no config (template + deployed): `permission: {"*": "deny"}`
   (texto puro, sem ferramentas) + `prompt` de sistema que forca JSON unico
   `{"objetivo_corrigido", "lacunas", "melhorias", "observacao"}`.
3. **Cadeia em `refinar_com_llm`**: opencode (primaria) -> NVIDIA -> OpenAI -> Anthropic.
4. **`sys.stdout.reconfigure(encoding='utf-8')`** no CLI: respostas do opencode contem
   emoji/unicode e quebravam o print cp1252 (`UnicodeEncodeError`).

## Descobertas tecnicas (lições)
- **`opencode run` headless com prompt longo NAO trava por recursao, mas o agente usa
  ferramentas** (carrega AGENTS.md/Constituicao via `instructions` e "executa" a tarefa:
  rodou preflight, buscou runtime...). Com `permission:*:deny` o agente responde texto
  direto (~15-20s vs 65s+ com tools).
- **`{{LLM_MODEL}}` nao resolvido em `opencode run` headless** -> `Model not found:
  {{LLM_MODEL}}/.`. Sempre passar `-m <modelo>` explicito.
- **`COMPREENSAO_EM_REFINO=1`** como guarda anti-recursao (se o agente headless chamasse
  a propria tool `refinar_entendimento`).
- **cwd neutro** (`runtime/refino`, gitignored) evita AGENTS.md do projeto na sessao aninhada.
- Start-Process + `2>$null` + `Out-File` no PS 5.1 pode engolir/corromper saida JSON;
  preferir RedirectStandardOutput para arquivo e parsear com Python.

## Validacao
- `compreensao.py "<pedido>" --refinar --json` -> `llm_refino.usado:true, provedor:opencode`,
  critica estruturada (objetivo_corrigido + 4 lacunas + 3 melhorias), ~26s.
- Failover: `COMPREENSAO_MODELO_OPENCODE=opencode/modelo-inexistente` -> caiu para NVIDIA,
  timeout, `usado:false` com motivo (fail-soft) — resiliencia comprovada.
- `preflight_check.py`: TODOS TESTES PASSARAM. `sync_rules.py update`: 3 camadas OK (13 regras).

## Conexoes

- [[2026-07-27-4-teste-do-ciclo-de-polling-verificar-se-o-vigila]]
- [[2026-07-27-5-teste-final-do-vigilante-em-processo-real-verif]]
- [[2026-07-27-fallback-automático-de-modelo-llm-com-bun-razrooo]]
- [[2026-07-27-scan-proativo-biblia]]
- [[2026-07-27-scan-proativo-cellcleaner]]
- [[2026-07-27-scan-proativo-mp3player]]
- [[2026-07-27-scan-proativo-supermarketcalculator]]
- [[2026-07-27-sistema-automático-de-captura-de-conhecimento-do-]]
- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]
- [[2026-07-27-unificacao-completa-do-ecossistema]]
- [[2026-07-28-cláusula-pétrea-toda-alteração-no-ecossistema-dev]]
- [[2026-07-28-formato-correto-do-mcp-no-opencode-1187-ao-adicio]]
- [[2026-07-28-scan-proativo-biblia]]
- [[2026-07-28-scan-proativo-cellcleaner]]
- [[2026-07-28-scan-proativo-mp3player]]
- [[2026-07-28-scan-proativo-supermarketcalculator]]
- [[2026-07-29-integração-de-clima-via-openweathermap]]
- [[2026-07-29-mcp-integration]]
- [[2026-07-29-scan-proativo-biblia]]
- [[2026-07-29-scan-proativo-cellcleaner]]
- [[2026-07-29-scan-proativo-mp3player]]
- [[2026-07-29-scan-proativo-supermarketcalculator]]
- [[2026-07-30-scan-proativo-biblia]]
- [[2026-07-30-scan-proativo-cellcleaner]]
- [[2026-07-30-scan-proativo-mp3player]]
- [[2026-07-30-scan-proativo-supermarketcalculator]]
- [[2026-07-31-mecanismo-de-fonemas-ssml-reativado-com-fallback-]]
- [[2026-08-01-cláusula-pétrea-comunicação-contínua-em-áudio]]
- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[2026-08-02-feedback-contínuo-em-tarefas-longas]]
- [[2026-08-02-regras-do-ecossistema-garantia-de-obediência-pelo]]
- [[2026-08-02-regras-em-3-camadas-com-sincronização-e-detecção-]]
- [[2026-08-03-build-android-lento-travava-por-falta-de-ram-buil]]
- [[2026-08-03-scan-proativo-bibliaestudocompleta]]
- [[2026-08-03-scan-proativo-cellcleaner]]
- [[2026-08-03-scan-proativo-compiladorapk]]
- [[2026-08-03-scan-proativo-ecosystemumgrau]]
- [[2026-08-03-scan-proativo-mp3player]]
- [[2026-08-03-scan-proativo-orquestradorapk-flutter]]
- [[2026-08-03-scan-proativo-supermarketcalculator]]
- [[2026-08-03-scan-proativo-windowsmaintenancesuitev3]]
- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]
- [[2026-08-04-jarvis-do-celular-conectado-ao-bridge-via-tailsca]]
- [[2026-08-04-labels-ocultas-por-padrão-botão-de-ocultar-menus-]]
- [[2026-08-04-malha-viva-onda-viajante-de-profundidade-giro-3d-]]
- [[2026-08-04-pseudo-3d-vivo-profundidade-sem-webgl-pedido-para]]
- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[2026-08-05-scan-proativo-ecosystemumgrau]]
- [[2026-08-06-scan-proativo-ecosystemumgrau]]
- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]
- [[aprendizado-2026-07-31-reorg-catálogo-único-habilidades-cami]]
- [[aprendizado-controle-eco-d-eco-da-narração]]
- [[aprendizado-debugging-expertise-skill]]
- [[aprendizado-narrador-de-voz-do-jarvis-no-opencode-desktop]]
- [[aprendizado-regra-de-fala-resumida-do-jarvis]]
- [[aprendizado-skill-auditoria-de-codigo-viva-com-evolução-gate]]
- [[atualização-ecosystemumgrau-auto-carregamento-gatilho-único-]]
- [[backup-de-apks-fontes-no-github]]
- [[botao-importar-unificado]]
- [[build-local-flutter-orquestrador]]
- [[ci-de-android-em-máquina-fraca-keystore-estável]]
- [[clausula-petrea-protecao-do-opencode-desktop-resiliencia-da-]]
- [[cluster-hub-ecossistema]]
- [[compressão-semântica-hierárquica-lições-da-implementação]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[confirmação-em-áudio-regra-permanente-01082026]]
- [[contagem-subpastas-arquivos-pastas]]
- [[context-engine-manifesto-domínios-multimídiacomportamentais]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[controle-de-tv-lg-01082026]]
- [[decisão-aprendizado-automático-permanente]]
- [[decisão-arquitetura-jarvis-app]]
- [[desativar-bridge-android]]
- [[engenheiro-criterioso]]
- [[estilo-de-comunicação-simples-e-direto]]
- [[estilo-por-pedido-power-bi-implementado]]
- [[etapa24-interface-jarvis]]
- [[evolução-do-tts-jarvis-naturalidade-via-ssml]]
- [[fase-a-concluída-catálogo-real-no-supabase-64-obras-via-tmdb]]
- [[fase3-rotina-automatica-de-tiragem-organizacional]]
- [[fix-widget-grafo-desktop]]
- [[grafo-movimento-organico-vis-network-usuario-pediu-refinamen]]
- [[gramática-do-português-brasileiro-guia-prático-do-dia-a-dia]]
- [[habilidade-navegação-perita-internet-pc-e-celular]]
- [[idioma-padrao-pt-br]]
- [[ilhas-no-grafo-notas-com-grau-0-e-como-conecta-las]]
- [[importação-de-pasta-preservando-árvore-remoção-de-referência]]
- [[janela-flutuante-para-visuais-sem-navegador]]
- [[jarvis-do-celular-e-do-pc-um-só-cérebro-arquitetura-sincroni]]
- [[junkscanner-benchmark-do-scan-incremental]]
- [[junkscanner-scan-incremental-cache-de-hash-memoização]]
- [[ler-specs-sdd-hook]]
- [[loop-infinito-de-push-no-vigilante-emails-do-github-a-cada-m]]
- [[modo-auto-gate]]
- [[motor-de-criticalidade-auto-organizada-e-avalanches-neurais]]
- [[mvp-streamumgrau-flutter-supabase]]
- [[módulo-de-compreensão-de-pedidos-mcp-compreensao-pedidos]]
- [[otimização-do-reindex-semântico-do-memory-engine]]
- [[padrao-de-pergunta-validacao-numerica-por-cota]]
- [[pais]]
- [[persistencia-completa-widget-grafo]]
- [[política-de-resposta-rápida-caminhos-rápidos-constantes-no-j]]
- [[ponte-web-video-cast]]
- [[pontes-inter-cluster-cerebro-vivo-grafo]]
- [[ponto-único-de-persistência-gate]]
- [[pontuação-da-transcrição-voltando-ao-balão-do-app-corrigido]]
- [[pronúncia-járvis-escrita-sem-acento-fala-com-acento]]
- [[protocolo-higiene-repo-streamumgrau]]
- [[quiet-period-commits-do-vigilante]]
- [[regra-do-usuário-buildinstalatestavalida-antes-de-commitar-e]]
- [[relatório-eco-estático-lições]]
- [[reorganização-habilidades-dentro-de-mcp-por-domínio]]
- [[resiliência-de-logs-encoding-detectado-na-leitura-não-presum]]
- [[restauracao-unified-bridge]]
- [[saudacao-auto-evolutiva-jarvis]]
- [[saudacao-dinamica-jarvis]]
- [[saudacao-espontanea-implementada]]
- [[saudacao-jarvis-estilo-filme]]
- [[saudacao-llm-nvidia-api]]
- [[secrets-guard-no-preflightcheck]]
- [[separação-de-estados-editar-vs-salvar-despesas]]
- [[sessao-de-configuracao-do-opencode-com-failover-de-servidor-]]
- [[sistema-de-análise-financeira]]
- [[tradingagents-integrado-ao-ecossistema]]
- [[transparencia-execucao-tarefas]]
- [[triagem-scripts-legado-orgaos-movidos]]
- [[vault-obsidian-cerebro-vivo-grafo]]
- [[vault-obsidian-fonte-viva]]
- [[widget-desktop-frameless-persistente]]
- [[widget-desktop-grafo-tempo-real]]
- [[widget-edge-estabilizado-fonte-unica-processos]]
- [[widget-evolucao-3-niveis]]
- [[widget-jarvis-8-features-implementadas]]