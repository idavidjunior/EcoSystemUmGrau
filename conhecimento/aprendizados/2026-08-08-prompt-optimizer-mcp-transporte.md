---
tipo: erro
tags: [mcp, prompt-optimization, transporte, stdio, content-length, opencode, jsonrpc]
data: 2026-08-08
contexto: Usuário perguntou se o otimizador de prompt estava ativo no ecossistema; verificação revelou que estava configurado mas nunca conectava
decisao: Corrigir o transporte do MCP server prompt-optimization para o padrão stdio com Content-Length framing (JSON-RPC MCP), em vez de JSON por linha
impacto: O MCP server agora responde a initialize/tools/list/tools/call com o protocolo padrão; fica ativo na próxima sessão do opencode
---

# MCP prompt-optimization não conectava: transporte JSON por linha em vez de MCP stdio

## Sintoma
O otimizador de prompt estava configurado (`config/opencode.jsonc` + deployed), o
`server.py` existia com 6 tools, mas **não ficava ativo**: nenhum processo rodava e
nenhuma tool era exposta nas sessões do opencode.

## Causa raiz
O `if __name__ == "__main__"` do `mcp/desenvolvimento/habilidades/prompt-optimization/server.py`
lia o stdin **linha a linha como JSON cru** (`for line in sys.stdin: json.loads(line)`).
O protocolo MCP sobre stdio (usado pelo opencode e por todos os clientes MCP) usa
**framing Content-Length** (estilo LSP):

```
Content-Length: 123\r\n
\r\n
{jsonrpc...}
```

Ao conectar, o opencode enviava frames; o server recebia a linha `Content-Length: N`
(JSON inválido → descartada) e a linha vazia (ignorada) e o payload ficava no buffer
sem nunca ser lido. Resultado: handshake `initialize` nunca completava → server nunca
aparecia como online.

## Prova
- Probe com framing padrão → **nenhuma resposta** (timeout de 60s).
- Probe com JSON cru por linha → respondia normalmente a `initialize` e `tools/list`.
Isso confirmou que a lógica do `handle()` estava correta; só o transporte estava errado.

## Correção aplicada
Substituído o loop de leitura por transporte MCP padrão:
- `_read_frame(stream)` — lê headers `Content-Length` do stdin.buffer e retorna o JSON.
- `_write_frame(stream, obj)` — escreve respostas com `Content-Length` framing.
- Loop principal: `_read_frame` → `handle(req)` → `_write_frame` (None = sem resposta,
  adequado para `notifications/initialized`).

## Verificação
Probe MCP padrão (framing correto) agora responde:
- `initialize` → `serverInfo: mcp-prompt-optimization v1.0.0`, capabilities tools.
- `tools/list` → 6 tools: optimize_prompt_dspy, refine_prompt_wizard, evaluate_prompt,
  compare_prompts, generate_prompt_tests, suggest_prompt_improvement.
- `tools/call evaluate_prompt` → scores (accuracy 100, overall 90, APP PROVED) OK.

## Lições
- Todo MCP server Python do ecossistema DEVE implementar o transporte stdio com
  **Content-Length framing** — "funcionar no terminal com echo" não significa que o
  opencode consiga usar.
- Ao criar/editar MCP servers, validar com um probe que faça `initialize` + `tools/list`
  + `tools/call` usando framing, não com pipe de JSON cru.
- A configuração no opencode.jsonc já apontava corretamente; o bug era 100% no server.

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
- [[fix-narrador-triplicado-e-resiliencia-orfaos]]
- [[fix-widget-grafo-desktop]]
- [[gate-ponto-unico-compilador]]
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