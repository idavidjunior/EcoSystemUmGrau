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

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]