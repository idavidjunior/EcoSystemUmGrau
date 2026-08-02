# 2026-08-02 - Regras em 3 camadas com sincronização e detecção de divergência

## Contexto
Usuário pediu: (1) garantir que ao atualizar/injetar regra, as 3 camadas sincronizem;
(2) detectar e avisar se algum modelo ignorar uma regra.

## Solução: scripts/sync_rules.py
Fonte única = `config/agents/00-system-rules.md` (Constituição).
Camadas:
1. **AGENTS.md** (raiz) — auto-carregado toda sessão. Blocos `<!-- RULES:START -->` e
   `<!-- SOURCES:START -->` são regenerados automaticamente.
2. **config/opencode.jsonc** instructions — referencia AGENTS.md + 00-system-rules.md.
3. **00-system-rules.md deployed** em `~/.config/opencode/agents/` — verificado idêntico.

Comandos:
- `python scripts/sync_rules.py check` — verifica: AGENTS.md contém todos os títulos de
  regra, opencode.jsonc referencia as 2, deployed idêntico. Exit 1 se divergir.
- `python scripts/sync_rules.py update` — regenera blocos do AGENTS.md a partir da
  Constituição (parse por headings `#` nível 1; mantém só CLÁUSULA PÉTREA/REGRA DE OURO).
- `python scripts/sync_rules.py audit` — check + update + re-check.

## Integração
- **preflight_check.py** — nova seção [5]: roda `sync_rules.py check`; divergência = FAIL
  (Cláusula Pétrea bloqueia deploy).
- **ecosystem.ps1 Sync-DeployConfig** — roda `sync_rules.py update` antes de deployar
  (garante AGENTS.md atualizado da fonte única).
- **vigilante.ps1** — RulesTimer 1x/h roda `check`; se divergir, loga "REGRA
  IGNORADA/NAO SINCRONIZADA" + registra memória.
- **test-ecosystem.ps1** — seção [10] verifica as 3 camadas.

## Detecção de "modelo ignorou regra" — o que é REAL
- **Detectável e confiável**: divergência entre as 3 camadas (regra injetada na
  Constituição mas não propagada), config deployada ≠ template, constituição deployed
  ≠ repo. Isso indica que alguém mudou regra sem sincronizar.
- **NÃO é confiável automaticamente**: "modelo não narrou em áudio" ou "não registrou
  aprendizado" — exigiria heurística frágil. Para isso, o reforço é o próprio AGENTS.md
  no contexto + agents de debate. Não prometo detecção automática desses casos.

## Validação (teste real)
- Injetada regra fake "CLÁUSULA PÉTREA — TESTE DE DETECÇÃO" na Constituição →
  `check` detectou: "AGENTS.md nao contem" + "Constituicao deployada divergente" (exit 1).
- `update` propagou (5 regras) → restou só "deploy divergente" (esperado, resolvido no sync).
- Restaurado original → 4 regras consistentes. Preflight seção [5] PASS.

## Lição
- Parse de regras por `#` nível 1 + filtro por padrão de título evita capturar seções
  intermediárias (ex.: FILOSOFIA/HIERARQUIA) — primeiro rascunho inchou AGENTS.md para
  633 linhas; corrigido para 126.
