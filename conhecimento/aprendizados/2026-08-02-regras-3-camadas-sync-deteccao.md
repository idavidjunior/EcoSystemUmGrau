# 2026-08-02 - Regras em 3 camadas com sincronizaÃ§Ã£o e detecÃ§Ã£o de divergÃªncia

## Contexto
UsuÃ¡rio pediu: (1) garantir que ao atualizar/injetar regra, as 3 camadas sincronizem;
(2) detectar e avisar se algum modelo ignorar uma regra.

## SoluÃ§Ã£o: scripts/sync_rules.py
Fonte Ãºnica = `config/agents/00-system-rules.md` (ConstituiÃ§Ã£o).
Camadas:
1. **AGENTS.md** (raiz) â€” auto-carregado toda sessÃ£o. Blocos `<!-- RULES:START -->` e
   `<!-- SOURCES:START -->` sÃ£o regenerados automaticamente.
2. **config/opencode.jsonc** instructions â€” referencia AGENTS.md + 00-system-rules.md.
3. **00-system-rules.md deployed** em `~/.config/opencode/agents/` â€” verificado idÃªntico.

Comandos:
- `python scripts/sync_rules.py check` â€” verifica: AGENTS.md contÃ©m todos os tÃ­tulos de
  regra, opencode.jsonc referencia as 2, deployed idÃªntico. Exit 1 se divergir.
- `python scripts/sync_rules.py update` â€” regenera blocos do AGENTS.md a partir da
  ConstituiÃ§Ã£o (parse por headings `#` nÃ­vel 1; mantÃ©m sÃ³ CLÃUSULA PÃ‰TREA/REGRA DE OURO).
- `python scripts/sync_rules.py audit` â€” check + update + re-check.

## IntegraÃ§Ã£o
- **preflight_check.py** â€” nova seÃ§Ã£o [5]: roda `sync_rules.py check`; divergÃªncia = FAIL
  (ClÃ¡usula PÃ©trea bloqueia deploy).
- **ecosystem.ps1 Sync-DeployConfig** â€” roda `sync_rules.py update` antes de deployar
  (garante AGENTS.md atualizado da fonte Ãºnica).
- **vigilante.ps1** â€” RulesTimer 1x/h roda `check`; se divergir, loga "REGRA
  IGNORADA/NAO SINCRONIZADA" + registra memÃ³ria.
- **test-ecosystem.ps1** â€” seÃ§Ã£o [10] verifica as 3 camadas.

## DetecÃ§Ã£o de "modelo ignorou regra" â€” o que Ã© REAL
- **DetectÃ¡vel e confiÃ¡vel**: divergÃªncia entre as 3 camadas (regra injetada na
  ConstituiÃ§Ã£o mas nÃ£o propagada), config deployada â‰  template, constituiÃ§Ã£o deployed
  â‰  repo. Isso indica que alguÃ©m mudou regra sem sincronizar.
- **NÃƒO Ã© confiÃ¡vel automaticamente**: "modelo nÃ£o narrou em Ã¡udio" ou "nÃ£o registrou
  aprendizado" â€” exigiria heurÃ­stica frÃ¡gil. Para isso, o reforÃ§o Ã© o prÃ³prio AGENTS.md
  no contexto + agents de debate. NÃ£o prometo detecÃ§Ã£o automÃ¡tica desses casos.

## ValidaÃ§Ã£o (teste real)
- Injetada regra fake "CLÃUSULA PÃ‰TREA â€” TESTE DE DETECÃ‡ÃƒO" na ConstituiÃ§Ã£o â†’
  `check` detectou: "AGENTS.md nao contem" + "Constituicao deployada divergente" (exit 1).
- `update` propagou (5 regras) â†’ restou sÃ³ "deploy divergente" (esperado, resolvido no sync).
- Restaurado original â†’ 4 regras consistentes. Preflight seÃ§Ã£o [5] PASS.

## LiÃ§Ã£o
- Parse de regras por `#` nÃ­vel 1 + filtro por padrÃ£o de tÃ­tulo evita capturar seÃ§Ãµes
  intermediÃ¡rias (ex.: FILOSOFIA/HIERARQUIA) â€” primeiro rascunho inchou AGENTS.md para
  633 linhas; corrigido para 126.

## Conexoes

- [[cluster-hub-programacao]]