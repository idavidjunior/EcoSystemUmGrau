---
tipo: decisao
tags: [resiliencia, watchdog, opencode, desktop, bridge, clausula-petrea, android]
data: 2026-08-06
contexto: "Usuario exigiu que nenhum processo automatico possa fechar o OpenCode desktop — apenas o usuario manualmente. Testes de resiliencia do bridge (que morria sem log) revelaram que o watchdog podia derrubar o desktop por erro de filtro."
decisao: "Corrigir watchdog.ps1 com protecao absoluta do desktop (clausula petrea) e robustez de instancia unica via lock de PID. Reestruturar saudacoes do bridge com estado persistente."
impacto: "Bridge e serve se auto-recuperam em <60s apos queda. Desktop OpenCode jamais e fechado automaticamente. Saudações variam entre primeira vez e reconexao."
---

# Clausula Petrea: protecao do OpenCode desktop + resiliencia da bridge

## Regra imutavel (clausula petrea)
**Em hipotese alguma, o Windows ou qualquer outro processo automatico pode fechar o
OpenCode desktop. Somente o usuario pode, manualmente.**

- O desktop roda como `OpenCode.exe` em `@opencode-aidesktop`.
- O CLI roda como `opencode.exe` (serve na porta 8767, run em sessoes).

## Bug critico encontrado
O filtro antigo de orfaos do watchdog matava qualquer `opencode.exe` cujo comando
NAO contivesse " serve":
```powershell
$cmd -match "opencode\.exe run" -or ($cmd -match "opencode\.exe" -and $cmd -notmatch " serve")
```
O desktop (`OpenCode.exe`) casa no segundo criterio (nao tem " serve" no comando),
entao o proprio watchdog poderia derrubar o desktop. **Corrigido** com protecao
explicita por caminho (`opencode-aidesktop`) e filtro restrito a `opencode run`.

## Melhorias no watchdog.ps1
1. **Instancia unica via lock de PID** (`watchdog.lock`): substitui o Mutex nomeado,
   que no Windows fica "abandoned" quando o processo dono e morto e NAO e re-adquirido
   — o que travava qualquer restart do watchdog.
2. **Health-check do bridge** (`Test-BridgeAlive`): verifica porta LISTENING + processo
   dono vivo. Detecta socket orfao (porta ocupada por processo morto) e limpa.
3. **Serve com health HTTP** (`/global/health` + Basic Auth): so considera saudavel se
   responde, nao apenas se a porta escuta.
4. **Log com limite de 2MB**: ao estourar, descarta a metade mais antiga.
5. **Filtro de orfaos seguro**: so mata `opencode.exe run` (CLI), nunca o desktop.

## Reestruturacao das saudacoes (jarvis_bridge.py)
> Detalhado em `2026-08-06-saudacoes-inteligentes-reconexao-vs-primeira-vez.md`
> (memoria #131). Estado persistente `saudacao_estado.json`, `_classificar_conexao()`
> com 3 fontes, prompt de retomada curto na reconexao, fallback variado, timeout 90s.

## Testes realizados (100%)
1. **Recuperacao do bridge**: derrubado -> watchdog restaurou em <60s (novo PID).
2. **Recuperacao do serve**: derrubado -> watchdog restaurou em <60s (novo PID).
3. **Desktop intocado**: 8 processos `OpenCode.exe` permaneceram apos as quedas.
4. **Saudacoes**: 3 conexoes seguidas geraram 3 saudações distintas; a reconexao
   retornou "De volta, senhor. Continuando de onde paramos." e "Voltou. Sistemas
   seguem quentes, é só falar." — reconhecendo a retomada.
5. **Watchdog duplicado**: lock de PID impede duas instancias concorrentes.

## Monitoramento
- Log do watchdog: `scripts/watchdog_log.txt` (limitado a 2MB).
- Log do bridge: `scripts/bridge_log.txt`.
- Estado de saudoes: `scripts/saudacao_estado.json`.
- Estado do bridge: `scripts/bridge_estado.json`.

## Atualizacao 2026-08-27 — Unificacao de vigilantes (watchdog -> system_guardian)

O watchdog.ps1 foi **rebaixado a keeper** (boot/launcher). A saude de processos
no PC (bridge 8765, serve 8767, narrador, tts, widget, RAM/CPU e limpeza de
orfaos CLI do opencode) eh agora **unica responsabilidade do system_guardian.py**
(Python). A certificacao forense de kill (`_forensic_safe_to_kill`) e a rotina
`cleanup_orphan_cli()` foram portadas do watchdog.ps1 para o system_guardian.py.
O watchdog.ps1 mantem o lock PID e o `watchdog_log.txt` (para nao quebrar o
boot `watchdog_start.bat` nem integracoes), mas seu loop agora so garante que
`vigilante.ps1` e `system_guardian.py` estejam vivos. Cadeia: watchdog ->
vigilante -> guardian. A clausula petrea de protecao do desktop (em AGENTS.md e
00-system-rules.md) foi realinhada para citar `system_guardian.py` como o
protetor do desktop (a protecao ja vivia no guardian via `is_desktop_opencode`).
Validado: py_compile OK, parse PS1 OK, slope de RAM -200 MB/min, forensic em PID
inexistente e auto-PID sem excecao.

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
- [[backup-de-apks-fontes-no-github]]
- [[botao-importar-unificado]]
- [[build-local-flutter-orquestrador]]
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
- [[limpeza-disco-windows]]
- [[loop-infinito-de-push-no-vigilante-emails-do-github-a-cada-m]]
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
- [[unificacao-de-vigilantes-watchdogps1-rebaixado-a-keeper]]
- [[vault-obsidian-cerebro-vivo-grafo]]
- [[vault-obsidian-fonte-viva]]
- [[widget-desktop-frameless-persistente]]
- [[widget-desktop-grafo-tempo-real]]
- [[widget-edge-estabilizado-fonte-unica-processos]]
- [[widget-evolucao-3-niveis]]
- [[widget-jarvis-8-features-implementadas]]