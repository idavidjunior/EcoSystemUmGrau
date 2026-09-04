---
tipo: erro
tags: [integracao, mcp, opencode, config, placeholder, renderizacao, deploy]
data: 2026-08-13
contexto: Diagnóstico de integração completa do EcoSystemUmGrau. Todos os 13 MCPs
apareciam como "failed / Connection closed" no `opencode mcp list`, mesmo com o
preflight passando e o opencode.jsonc definindo todos os servidores.
decisao: A causa raiz era que o opencode.jsonc deployado em ~/.config/opencode
continha `{{USERPROFILE}}` literal nos caminhos (o opencode não expande esse
placeholder — quem faz a substituição é o Sync-DeployConfig do ecosystem.ps1).
O deploy estava desatualizado/copiado sem renderização. Correções aplicadas:
1) Renderizado ~/.config/opencode/opencode.jsonc substituindo {{USERPROFILE}}
pelo path real (backup .bak criado antes, cláusula de resiliência). 2) Serve
opencode 8767 reiniciado para carregar o config corrigido (o watchdog o
reinicia se cair). 3) test-ecosystem.ps1 tinha paths antigos Desktop\Codigos
(migração para Documents\Default Project) — corrigido para $PSScriptRoot e
Projetos/; 4) Junction ~/.ler -> ler-runtime criada; 5) ler.bat criado em
~/.local/bin + PATH do usuário. Resultado: 13/13 MCPs connected, suíte
test-ecosystem 32 PASS / 0 FAIL, preflight TODOS PASSARAM, bridge 8765 e
serve 8767 saudáveis.
impacto: O opencode agora enxerga e conecta todos os MCPs do ecossistema
(eco-knowledge, eco-obsidian, mcp-desenvolvimento, mcp-android, mcp-internet,
mcp-memoria, mcp-multimidia, mcp-comportamentais, mcp-compreensao-pedidos,
filesystem, search, terminal, github). Ferramentas do ecossistema voltam a
estar disponíveis para as sessões. test-ecosystem.ps1 agora reflete o estado
real do PC (sem falsos negativos por caminhos antigos).
erros_encontrados:
- [FIX] 13 MCPs offline: {{USERPROFILE}} não renderizado no opencode.jsonc deployado
- [FIX] test-ecosystem.ps1 apontava para Desktop\Codigos (inexistente) → 9 FAIL falsos
- [FIX] Junction ~/.ler ausente
- [FIX] ler.bat ausente no PATH
- [FIX] Serve 8767 rodava com config desatualizado (MCPs offline)
padrao_extraido: Após qualquer mudança em config/opencode.jsonc (template), o
deploy deve ser refeito via `ecosystem.ps1 sync` (Sync-DeployConfig renderiza
{{USERPROFILE}}). Verificar sempre com `opencode mcp list` que todos os MCPs
estão "connected", não apenas o preflight (preflight valida os servers, não o
config resolvido pelo opencode).

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
- [[auto-evolution-e-behavior-slices]]
- [[auto-evolution-gate-veto-health]]
- [[auto-evolution-maestro-radar-relatório-consolidado]]
- [[backup-de-apks-fontes-no-github]]
- [[botao-importar-unificado]]
- [[build-local-flutter-orquestrador]]
- [[calculadora-formato-consolidado-do-percentual-restaurado]]
- [[cerebro-vivo-nos-clicaveis-navegaveis]]
- [[ci-de-android-em-máquina-fraca-keystore-estável]]
- [[clausula-petrea-protecao-do-opencode-desktop-resiliencia-da-]]
- [[composio-mcp-remoto]]
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
- [[fix-narrador-triplicado-e-resiliencia-orfaos]]
- [[fix-widget-grafo-desktop]]
- [[fontes-consumidas-nas-construções-kg-memória]]
- [[gate-ponto-unico-compilador]]
- [[gate-veto-compreensao]]
- [[gate-veto-kernel]]
- [[governanca-ciclo-jurisprudencia]]
- [[grafo-movimento-organico-vis-network-usuario-pediu-refinamen]]
- [[gramática-do-português-brasileiro-guia-prático-do-dia-a-dia]]
- [[gui-desktop-desativada-edge-e-cerebro-vivo]]
- [[gui-remover-chatpanel]]
- [[habilidade-navegação-perita-internet-pc-e-celular]]
- [[idioma-padrao-pt-br]]
- [[ilhas-no-grafo-notas-com-grau-0-e-como-conecta-las]]
- [[importação-de-pasta-preservando-árvore-remoção-de-referência]]
- [[janela-flutuante-para-visuais-sem-navegador]]
- [[jarvis-do-celular-e-do-pc-um-só-cérebro-arquitetura-sincroni]]
- [[jarvis-gui-desktop-referencia]]
- [[junkscanner-benchmark-do-scan-incremental]]
- [[junkscanner-scan-incremental-cache-de-hash-memoização]]
- [[ler-specs-sdd-hook]]
- [[limpeza-disco-windows]]
- [[loop-infinito-de-push-no-vigilante-emails-do-github-a-cada-m]]
- [[melhorias-inspiradas-nos-jarvis-opensource-implementadas]]
- [[modo-auto-gate]]
- [[motor-de-criticalidade-auto-organizada-e-avalanches-neurais]]
- [[mvp-streamumgrau-flutter-supabase]]
- [[módulo-de-compreensão-de-pedidos-mcp-compreensao-pedidos]]
- [[oficializacao-narrador-edge-cerebro-vivo]]
- [[otimização-do-reindex-semântico-do-memory-engine]]
- [[padrao-de-pergunta-validacao-numerica-por-cota]]
- [[pais]]
- [[pausa-total-widget]]
- [[persistencia-completa-widget-grafo]]
- [[política-de-resposta-rápida-caminhos-rápidos-constantes-no-j]]
- [[ponte-web-video-cast]]
- [[pontes-inter-cluster-cerebro-vivo-grafo]]
- [[ponto-único-de-persistência-gate]]
- [[pontuação-da-transcrição-voltando-ao-balão-do-app-corrigido]]
- [[projeto-completo-e-ativo-a-recuperar]]
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
- [[smc-ab5-calculadora-simples]]
- [[smc-ab5-formatacao-brl]]
- [[smc-acrescimo-resultado-grande]]
- [[suggestions-hermes-itens-1-3]]
- [[supermarketcalculator-v157]]
- [[tradingagents-integrado-ao-ecossistema]]
- [[transparencia-execucao-tarefas]]
- [[triagem-scripts-legado-orgaos-movidos]]
- [[unificacao-aprendizados-adb-cluster-a]]
- [[unificacao-de-vigilantes-watchdogps1-rebaixado-a-keeper]]
- [[vault-obsidian-cerebro-vivo-grafo]]
- [[vault-obsidian-fonte-viva]]
- [[widget-desktop-frameless-persistente]]
- [[widget-desktop-grafo-tempo-real]]
- [[widget-edge-estabilizado-fonte-unica-processos]]
- [[widget-evolucao-3-niveis]]
- [[widget-jarvis-8-features-implementadas]]