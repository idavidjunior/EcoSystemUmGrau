---
tags: [ativa, decisao, opencode, recente, rede, resilience]
aliases: [Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper]
date: 2026-08-27
---

# Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper

**Fonte:** opencode

---
tipo: decisao
tags: [resiliencia, watchdog, system-guardian, unificacao, opencode, desktop, clausula-petrea]
data: 2026-08-27
contexto: "Usuario pediu unificar os vigilantes fragmentados do PC. Haviam 3 loops redundantes cuidando de bridge/serve: system_guardian.py (RAM/CPU + restart), watchdog.ps1 e a camada do bridge. Decisao de consolidar num unico dono de saude de processos."
decisao: "Rebaixar watchdog.ps1 a keeper (so garante que vigilante.ps1 e system_guardian.py rodem, preservando o boot watchdog_start.bat). Portar a certificacao forense de kill e a limpeza de orfaos CLI do watchdog.ps1 para system_guardian.py, tornando-o unico dono da saude de processos. NAO fundir bridge_resiliencia.py (ele e ADB/Tailscale, sobrepoe connection_guardian.py, nao a porta 8765). Realinhar a clausula petrea (AGENTS.md e 00-system-rules.md) para citar system_guardian.py como protetor do desktop. Atualizar inventario_estruturas.json e HABILIDADES.md."
impacto: "Um so watcher de processo no PC (system_guardian.py). Boot preservado (watchdog_start.bat -> watchdog.ps1 -> vigilante.ps1 -> system_guardian.py). Protecao do desktop mantida via is_desktop_opencode no guardian. Maior coesao e menos duplicacao, conforme a clausula de proibicao de estrutura redundante."
---

# Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper

## Diagnostico (antes)
- `system_guardian.py` (Python): RAM/CPU, restart de bridge 8765, serve 8767,
  narrador, tts, widget; instala o `ensure_bridge_flag` e chama `opencode_resilience`.
- `watchdog.ps1` (PowerShell): SEGUNDO loop para bridge/serve + limpeza de orfaos
  CLI + widget unico + certificacao forense de kill.
- `vigilante.ps1`: orquestrador que ja mantem `system_guardian.py` vivo (timer 5 min).
- `bridge_resiliencia.py` / `connection_guardian.py`: dominio ADB/Tailscale
  (conectividade), NAO processo do PC — confundido no primeiro diagnostico, corrigido.

Tripla redundancia em bridge/serve. A peca que faltava no guardian era a gestao
PROATIVA de RAM (alerta antes do limite) e a portabilidade da certificacao forense.

## O que foi feito
1. **Camada proativa de RAM** (ja implementada antes desta unificacao): constantes
   `RAM_EARLY_WARN_MB=1024`, `PROACTIVE_COOLDOWN_S=300`; funcoes `_record_ram_sample`,
   `_ram_slope_mb_per_min`, `check_proactive_ram` (chama `opencode_resilience.py --clean`
   quando RAM < 1GB e queda > 5 MB/min, com cooldown).
2. **Certificacao forense** `_forensic_safe_to_kill(pid, ...)` portada para Python:
   recusa kill se processo tem filhos vivos, rede ativa, e recente, ou e desktop/eco/
   essencial. Base da seguranca do desktop.
3. **`cleanup_orphan_cli()`**: mata so `opencode.exe run` orfao (CLI), com certificacao
   forense; nunca o desktop (`@opencode-aidesktop`) nem o serve. Chamada a cada ciclo
   de `check_and_act`.
4. **watchdog.ps1 rebaixado**: mantem lock PID + `watchdog_log.txt`; loop passa a
   apenas `Ensure-Running` de `vigilante.ps1` e `system_guardian.py`.
5. **Clausula petrea** realinhada: `watchdog.ps1` -> `system_guardian.py` em AGENTS.md
   e 00-system-rules.md (a protecao ja vivia no guardian).
6. **Inventario e HABILIDADES.md** atualizados para o novo papel do watchdog.

## Validacao
- `python -m py_compile scripts/system_guardian.py` -> OK.
- Parse PS1 do watchdog.ps1 -> OK.
- `_ram_slope_mb_per_min` com 5 amostras: -200 MB/min (correto).
- `_forensic_safe_to_kill(999999)` -> (False, ['processo inexistente']) sem excecao.
- `_forensic_safe_to_kill(os.getpid())` -> (False, ['recem-criado']) sem excecao.

## Licoes
- Ao unificar, PRESERVAR o ponto de boot (watchdog_start.bat depende de watchdog.ps1).
  Rebaixar a arquivo mantem a cadeia; apagar quebraria o boot.
- Nao confundir dominios: bridge_resiliencia.py e conectividade (ADB/Tailscale),
  nao processo do PC. Verificar o conteudo antes de propor fusao.
- Clauses petreas que citam nomes de arquivos devem ser realinhadas quando a
  propriedade da responsabilidade muda, para nao mentirem.

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
- [[widget-jarvis-8-features-implementadas]] // ---
tipo: decisao
tags: [resiliencia, watchdog, system-guardian, unificacao, opencode, desktop, clausula-petrea]
data: 2026-08-27
contexto: "Usuario pediu unificar os vigilantes fragmentados do PC. Haviam 3 loops redundantes cuidando de bridge/serve: system_guardian.py (RAM/CPU + restart), watchdog.ps1 e a camada do bridge. Decisao de consolidar num unico dono de saude de processos."
decisao: "Rebaixar watchdog.ps1 a keeper (so garante que vigilante.ps1 e system_guardian.py rodem, preservando o boot watchdog_start.bat). Portar a certificacao forense de kill e a limpeza de orfaos CLI do watchdog.ps1 para system_guardian.py, tornando-o unico dono da saude de processos. NAO fundir bridge_resiliencia.py (ele e ADB/Tailscale, sobrepoe connection_guardian.py, nao a porta 8765). Realinhar a clausula petrea (AGENTS.md e 00-system-rules.md) para citar system_guardian.py como protetor do desktop. Atualizar inventario_estruturas.json e HABILIDADES.md."
impacto: "Um so watcher de processo no PC (system_guardian.py). Boot preservado (watchdog_start.bat -> watchdog.ps1 -> vigilante.ps1 -> system_guardian.py). Protecao do desktop mantida via is_desktop_opencode no guardian. Maior coesao e menos duplicacao, conforme a clausula de proibicao de estrutura redundante."
---

# Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper

## Diagnostico (antes)
- `system_guardian.py` (Python): RAM/CPU, restart de bridge 8765, serve 8767,
  narrador, tts, widget; instala o `ensure_bridge_flag` e chama `opencode_resilience`.
- `watchdog.ps1` (PowerShell): SEGUNDO loop para bridge/serve + limpeza de orfaos
  CLI + widget unico + certificacao forense de kill.
- `vigilante.ps1`: orquestrador que ja mantem `system_guardian.py` vivo (timer 5 min).
- `bridge_resiliencia.py` / `connection_guardian.py`: dominio ADB/Tailscale
  (conectividade), NAO processo do PC — confundido no primeiro diagnostico, corrigido.

Tripla redundancia em bridge/serve. A peca que faltava no guardian era a gestao
PROATIVA de RAM (alerta antes do limite) e a portabilidade da certificacao forense.

## O que foi feito
1. **Camada proativa de RAM** (ja implementada antes desta unificacao): constantes
   `RAM_EARLY_WARN_MB=1024`, `PROACTIVE_COOLDOWN_S=300`; funcoes `_record_ram_sample`,
   `_ram_slope_mb_per_min`, `check_proactive_ram` (chama `opencode_resilience.py --clean`
   quando RAM < 1GB e queda > 5 MB/min, com cooldown).
2. **Certificacao forense** `_forensic_safe_to_kill(pid, ...)` portada para Python:
   recusa kill se processo tem filhos vivos, rede ativa, e recente, ou e desktop/eco/
   essencial. Base da seguranca do desktop.
3. **`cleanup_orphan_cli()`**: mata so `opencode.exe run` orfao (CLI), com certificacao
   forense; nunca o desktop (`@opencode-aidesktop`) nem o serve. Chamada a cada ciclo
   de `check_and_act`.
4. **watchdog.ps1 rebaixado**: mantem lock PID + `watchdog_log.txt`; loop passa a
   apenas `Ensure-Running` de `vigilante.ps1` e `system_guardian.py`.
5. **Clausula petrea** realinhada: `watchdog.ps1` -> `system_guardian.py` em AGENTS.md
   e 00-system-rules.md (a protecao ja vivia no guardian).
6. **Inventario e HABILIDADES.md** atualizados para o novo papel do watchdog.

## Validacao
- `python -m py_compile scripts/system_guardian.py` -> OK.
- Parse PS1 do watchdog.ps1 -> OK.
- `_ram_slope_mb_per_min` com 5 amostras: -200 MB/min (correto).
- `_forensic_safe_to_kill(999999)` -> (False, ['processo inexistente']) sem excecao.
- `_forensic_safe_to_kill(os.getpid())` -> (False, ['recem-criado']) sem excecao.

## Licoes
- Ao unificar, PRESERVAR o ponto de boot (watchdog_start.bat depende de watchdog.ps1).
  Rebaixar a arquivo mantem a cadeia; apagar quebraria o boot.
- Nao confundir dominios: bridge_resiliencia.py e conectividade (ADB/Tailscale),
  nao processo do PC. Verificar o conteudo antes de propor fusao.
- Clauses petreas que citam nomes de arquivos devem ser realinhadas quando a
  propriedade da responsabilidade muda, para nao mentirem.

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
- [[unificacao-de-vigilantes-watchdogps1-rebaixado-a-keeper]]
- [[vault-obsidian-cerebro-vivo-grafo]]
- [[vault-obsidian-fonte-viva]]
- [[widget-desktop-frameless-persistente]]
- [[widget-desktop-grafo-tempo-real]]
- [[widget-edge-estabilizado-fonte-unica-processos]]
- [[widget-evolucao-3-niveis]]
- [[widget-jarvis-8-features-implementadas]] // ---
tipo: decisao
tags: [resiliencia, watchdog, system-guardian, unificacao, opencode, desktop, clausula-petrea]
data: 2026-08-27
contexto: "Usuario pediu unificar os vigilantes fragmentados do PC. Haviam 3 loops redundantes cuidando de bridge/serve: system_guardian.py (RAM/CPU + restart), watchdog.ps1 e a camada do bridge. Decisao de consolidar num unico dono de saude de processos."
decisao: "Rebaixar watchdog.ps1 a keeper (so garante que vigilante.ps1 e system_guardian.py rodem, preservando o boot watchdog_start.bat). Portar a certificacao forense de kill e a limpeza de orfaos CLI do watchdog.ps1 para system_guardian.py, tornando-o unico dono da saude de processos. NAO fundir bridge_resiliencia.py (ele e ADB/Tailscale, sobrepoe connection_guardian.py, nao a porta 8765). Realinhar a clausula petrea (AGENTS.md e 00-system-rules.md) para citar system_guardian.py como protetor do desktop. Atualizar inventario_estruturas.json e HABILIDADES.md."
impacto: "Um so watcher de processo no PC (system_guardian.py). Boot preservado (watchdog_start.bat -> watchdog.ps1 -> vigilante.ps1 -> system_guardian.py). Protecao do desktop mantida via is_desktop_opencode no guardian. Maior coesao e menos duplicacao, conforme a clausula de proibicao de estrutura redundante."
---

# Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper

## Diagnostico (antes)
- `system_guardian.py` (Python): RAM/CPU, restart de bridge 8765, serve 8767,
  narrador, tts, widget; instala o `ensure_bridge_flag` e chama `opencode_resilience`.
- `watchdog.ps1` (PowerShell): SEGUNDO loop para bridge/serve + limpeza de orfaos
  CLI + widget unico + certificacao forense de kill.
- `vigilante.ps1`: orquestrador que ja mantem `system_guardian.py` vivo (timer 5 min).
- `bridge_resiliencia.py` / `connection_guardian.py`: dominio ADB/Tailscale
  (conectividade), NAO processo do PC — confundido no primeiro diagnostico, corrigido.

Tripla redundancia em bridge/serve. A peca que faltava no guardian era a gestao
PROATIVA de RAM (alerta antes do limite) e a portabilidade da certificacao forense.

## O que foi feito
1. **Camada proativa de RAM** (ja implementada antes desta unificacao): constantes
   `RAM_EARLY_WARN_MB=1024`, `PROACTIVE_COOLDOWN_S=300`; funcoes `_record_ram_sample`,
   `_ram_slope_mb_per_min`, `check_proactive_ram` (chama `opencode_resilience.py --clean`
   quando RAM < 1GB e queda > 5 MB/min, com cooldown).
2. **Certificacao forense** `_forensic_safe_to_kill(pid, ...)` portada para Python:
   recusa kill se processo tem filhos vivos, rede ativa, e recente, ou e desktop/eco/
   essencial. Base da seguranca do desktop.
3. **`cleanup_orphan_cli()`**: mata so `opencode.exe run` orfao (CLI), com certificacao
   forense; nunca o desktop (`@opencode-aidesktop`) nem o serve. Chamada a cada ciclo
   de `check_and_act`.
4. **watchdog.ps1 rebaixado**: mantem lock PID + `watchdog_log.txt`; loop passa a
   apenas `Ensure-Running` de `vigilante.ps1` e `system_guardian.py`.
5. **Clausula petrea** realinhada: `watchdog.ps1` -> `system_guardian.py` em AGENTS.md
   e 00-system-rules.md (a protecao ja vivia no guardian).
6. **Inventario e HABILIDADES.md** atualizados para o novo papel do watchdog.

## Validacao
- `python -m py_compile scripts/system_guardian.py` -> OK.
- Parse PS1 do watchdog.ps1 -> OK.
- `_ram_slope_mb_per_min` com 5 amostras: -200 MB/min (correto).
- `_forensic_safe_to_kill(999999)` -> (False, ['processo inexistente']) sem excecao.
- `_forensic_safe_to_kill(os.getpid())` -> (False, ['recem-criado']) sem excecao.

## Licoes
- Ao unificar, PRESERVAR o ponto de boot (watchdog_start.bat depende de watchdog.ps1).
  Rebaixar a arquivo mantem a cadeia; apagar quebraria o boot.
- Nao confundir dominios: bridge_resiliencia.py e conectividade (ADB/Tailscale),
  nao processo do PC. Verificar o conteudo antes de propor fusao.
- Clauses petreas que citam nomes de arquivos devem ser realinhadas quando a
  propriedade da responsabilidade muda, para nao mentirem.

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
- [[unificacao-de-vigilantes-watchdogps1-rebaixado-a-keeper]]
- [[vault-obsidian-cerebro-vivo-grafo]]
- [[vault-obsidian-fonte-viva]]
- [[widget-desktop-frameless-persistente]]
- [[widget-desktop-grafo-tempo-real]]
- [[widget-edge-estabilizado-fonte-unica-processos]]
- [[widget-evolucao-3-niveis]]
- [[widget-jarvis-8-features-implementadas]] // ---
tipo: decisao
tags: [resiliencia, watchdog, system-guardian, unificacao, opencode, desktop, clausula-petrea]
data: 2026-08-27
contexto: "Usuario pediu unificar os vigilantes fragmentados do PC. Haviam 3 loops redundantes cuidando de bridge/serve: system_guardian.py (RAM/CPU + restart), watchdog.ps1 e a camada do bridge. Decisao de consolidar num unico dono de saude de processos."
decisao: "Rebaixar watchdog.ps1 a keeper (so garante que vigilante.ps1 e system_guardian.py rodem, preservando o boot watchdog_start.bat). Portar a certificacao forense de kill e a limpeza de orfaos CLI do watchdog.ps1 para system_guardian.py, tornando-o unico dono da saude de processos. NAO fundir bridge_resiliencia.py (ele e ADB/Tailscale, sobrepoe connection_guardian.py, nao a porta 8765). Realinhar a clausula petrea (AGENTS.md e 00-system-rules.md) para citar system_guardian.py como protetor do desktop. Atualizar inventario_estruturas.json e HABILIDADES.md."
impacto: "Um so watcher de processo no PC (system_guardian.py). Boot preservado (watchdog_start.bat -> watchdog.ps1 -> vigilante.ps1 -> system_guardian.py). Protecao do desktop mantida via is_desktop_opencode no guardian. Maior coesao e menos duplicacao, conforme a clausula de proibicao de estrutura redundante."
---

# Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper

## Diagnostico (antes)
- `system_guardian.py` (Python): RAM/CPU, restart de bridge 8765, serve 8767,
  narrador, tts, widget; instala o `ensure_bridge_flag` e chama `opencode_resilience`.
- `watchdog.ps1` (PowerShell): SEGUNDO loop para bridge/serve + limpeza de orfaos
  CLI + widget unico + certificacao forense de kill.
- `vigilante.ps1`: orquestrador que ja mantem `system_guardian.py` vivo (timer 5 min).
- `bridge_resiliencia.py` / `connection_guardian.py`: dominio ADB/Tailscale
  (conectividade), NAO processo do PC — confundido no primeiro diagnostico, corrigido.

Tripla redundancia em bridge/serve. A peca que faltava no guardian era a gestao
PROATIVA de RAM (alerta antes do limite) e a portabilidade da certificacao forense.

## O que foi feito
1. **Camada proativa de RAM** (ja implementada antes desta unificacao): constantes
   `RAM_EARLY_WARN_MB=1024`, `PROACTIVE_COOLDOWN_S=300`; funcoes `_record_ram_sample`,
   `_ram_slope_mb_per_min`, `check_proactive_ram` (chama `opencode_resilience.py --clean`
   quando RAM < 1GB e queda > 5 MB/min, com cooldown).
2. **Certificacao forense** `_forensic_safe_to_kill(pid, ...)` portada para Python:
   recusa kill se processo tem filhos vivos, rede ativa, e recente, ou e desktop/eco/
   essencial. Base da seguranca do desktop.
3. **`cleanup_orphan_cli()`**: mata so `opencode.exe run` orfao (CLI), com certificacao
   forense; nunca o desktop (`@opencode-aidesktop`) nem o serve. Chamada a cada ciclo
   de `check_and_act`.
4. **watchdog.ps1 rebaixado**: mantem lock PID + `watchdog_log.txt`; loop passa a
   apenas `Ensure-Running` de `vigilante.ps1` e `system_guardian.py`.
5. **Clausula petrea** realinhada: `watchdog.ps1` -> `system_guardian.py` em AGENTS.md
   e 00-system-rules.md (a protecao ja vivia no guardian).
6. **Inventario e HABILIDADES.md** atualizados para o novo papel do watchdog.

## Validacao
- `python -m py_compile scripts/system_guardian.py` -> OK.
- Parse PS1 do watchdog.ps1 -> OK.
- `_ram_slope_mb_per_min` com 5 amostras: -200 MB/min (correto).
- `_forensic_safe_to_kill(999999)` -> (False, ['processo inexistente']) sem excecao.
- `_forensic_safe_to_kill(os.getpid())` -> (False, ['recem-criado']) sem excecao.

## Licoes
- Ao unificar, PRESERVAR o ponto de boot (watchdog_start.bat depende de watchdog.ps1).
  Rebaixar a arquivo mantem a cadeia; apagar quebraria o boot.
- Nao confundir dominios: bridge_resiliencia.py e conectividade (ADB/Tailscale),
  nao processo do PC. Verificar o conteudo antes de propor fusao.
- Clauses petreas que citam nomes de arquivos devem ser realinhadas quando a
  propriedade da responsabilidade muda, para nao mentirem.

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
- [[retencao-opencode-db-vigilante]]
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
- [[widget-jarvis-8-features-implementadas]] // ---
tipo: decisao
tags: [resiliencia, watchdog, system-guardian, unificacao, opencode, desktop, clausula-petrea]
data: 2026-08-27
contexto: "Usuario pediu unificar os vigilantes fragmentados do PC. Haviam 3 loops redundantes cuidando de bridge/serve: system_guardian.py (RAM/CPU + restart), watchdog.ps1 e a camada do bridge. Decisao de consolidar num unico dono de saude de processos."
decisao: "Rebaixar watchdog.ps1 a keeper (so garante que vigilante.ps1 e system_guardian.py rodem, preservando o boot watchdog_start.bat). Portar a certificacao forense de kill e a limpeza de orfaos CLI do watchdog.ps1 para system_guardian.py, tornando-o unico dono da saude de processos. NAO fundir bridge_resiliencia.py (ele e ADB/Tailscale, sobrepoe connection_guardian.py, nao a porta 8765). Realinhar a clausula petrea (AGENTS.md e 00-system-rules.md) para citar system_guardian.py como protetor do desktop. Atualizar inventario_estruturas.json e HABILIDADES.md."
impacto: "Um so watcher de processo no PC (system_guardian.py). Boot preservado (watchdog_start.bat -> watchdog.ps1 -> vigilante.ps1 -> system_guardian.py). Protecao do desktop mantida via is_desktop_opencode no guardian. Maior coesao e menos duplicacao, conforme a clausula de proibicao de estrutura redundante."
---

# Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper

## Diagnostico (antes)
- `system_guardian.py` (Python): RAM/CPU, restart de bridge 8765, serve 8767,
  narrador, tts, widget; instala o `ensure_bridge_flag` e chama `opencode_resilience`.
- `watchdog.ps1` (PowerShell): SEGUNDO loop para bridge/serve + limpeza de orfaos
  CLI + widget unico + certificacao forense de kill.
- `vigilante.ps1`: orquestrador que ja mantem `system_guardian.py` vivo (timer 5 min).
- `bridge_resiliencia.py` / `connection_guardian.py`: dominio ADB/Tailscale
  (conectividade), NAO processo do PC — confundido no primeiro diagnostico, corrigido.

Tripla redundancia em bridge/serve. A peca que faltava no guardian era a gestao
PROATIVA de RAM (alerta antes do limite) e a portabilidade da certificacao forense.

## O que foi feito
1. **Camada proativa de RAM** (ja implementada antes desta unificacao): constantes
   `RAM_EARLY_WARN_MB=1024`, `PROACTIVE_COOLDOWN_S=300`; funcoes `_record_ram_sample`,
   `_ram_slope_mb_per_min`, `check_proactive_ram` (chama `opencode_resilience.py --clean`
   quando RAM < 1GB e queda > 5 MB/min, com cooldown).
2. **Certificacao forense** `_forensic_safe_to_kill(pid, ...)` portada para Python:
   recusa kill se processo tem filhos vivos, rede ativa, e recente, ou e desktop/eco/
   essencial. Base da seguranca do desktop.
3. **`cleanup_orphan_cli()`**: mata so `opencode.exe run` orfao (CLI), com certificacao
   forense; nunca o desktop (`@opencode-aidesktop`) nem o serve. Chamada a cada ciclo
   de `check_and_act`.
4. **watchdog.ps1 rebaixado**: mantem lock PID + `watchdog_log.txt`; loop passa a
   apenas `Ensure-Running` de `vigilante.ps1` e `system_guardian.py`.
5. **Clausula petrea** realinhada: `watchdog.ps1` -> `system_guardian.py` em AGENTS.md
   e 00-system-rules.md (a protecao ja vivia no guardian).
6. **Inventario e HABILIDADES.md** atualizados para o novo papel do watchdog.

## Validacao
- `python -m py_compile scripts/system_guardian.py` -> OK.
- Parse PS1 do watchdog.ps1 -> OK.
- `_ram_slope_mb_per_min` com 5 amostras: -200 MB/min (correto).
- `_forensic_safe_to_kill(999999)` -> (False, ['processo inexistente']) sem excecao.
- `_forensic_safe_to_kill(os.getpid())` -> (False, ['recem-criado']) sem excecao.

## Licoes
- Ao unificar, PRESERVAR o ponto de boot (watchdog_start.bat depende de watchdog.ps1).
  Rebaixar a arquivo mantem a cadeia; apagar quebraria o boot.
- Nao confundir dominios: bridge_resiliencia.py e conectividade (ADB/Tailscale),
  nao processo do PC. Verificar o conteudo antes de propor fusao.
- Clauses petreas que citam nomes de arquivos devem ser realinhadas quando a
  propriedade da responsabilidade muda, para nao mentirem.

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
- [[unificacao-de-vigilantes-watchdogps1-rebaixado-a-keeper]]
- [[vault-obsidian-cerebro-vivo-grafo]]
- [[vault-obsidian-fonte-viva]]
- [[widget-desktop-frameless-persistente]]
- [[widget-desktop-grafo-tempo-real]]
- [[widget-edge-estabilizado-fonte-unica-processos]]
- [[widget-evolucao-3-niveis]]
- [[widget-jarvis-8-features-implementadas]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]