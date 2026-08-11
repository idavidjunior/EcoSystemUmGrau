# 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo

## Contexto
O usuÃ¡rio queria sincronizar o ecossistema inteiro com um Ãºnico comando, para ficar
sempre atualizado e nada se perder ao trocar de PC.

## O que foi feito
- Corrigido `scripts/ecosystem.ps1`:
  - `$ecoDir` agora Ã© auto-detectado via `Split-Path $PSScriptRoot -Parent` (antes
    hardcoded `Desktop\Codigos\EcoSystemUmGrau`, que nÃ£o existe mais â€” o repo vive em
    `Documents\Default Project\EcoSystemUmGrau`).
  - `$projectsDir` aponta para `Documents\Default Project` (todos os repos irmÃ£os).
  - Novo `Sync-DeployConfig`: renderiza `config/opencode.jsonc` trocando
    `{{USERPROFILE}}` â†’ caminho real, copia agents (16) e `opencode-model-fallback.jsonc`
    para `~/.config/opencode/`, garante plugin `@razroo/opencode-model-fallback`
    instalado, valida com `opencode debug config` + `scripts/preflight_check.py`.
  - ConsolidaÃ§Ã£o do conhecimento (CONHECIMENTO.md + notas Obsidian) movida para ANTES
    do commit, para nÃ£o deixar pendÃªncia apÃ³s o sync.
  - Exclui o prÃ³prio Eco do loop de projetos irmÃ£os (evita commit duplicado).
- Corrigido `config/opencode.jsonc` (template): `plugin` deve ser array de strings
  `["@razroo/opencode-model-fallback"]`, NÃƒO objeto `{name, config}`. A config real do
  plugin fica em `config/opencode-model-fallback.jsonc` (o plugin lÃª
  `~/.config/opencode/opencode-model-fallback.jsonc`).
- Corrigido `config/opencode-model-fallback.jsonc`: cadeia de 7 modelos FREE
  (nemotron, deepseek-v4-flash, laguna, ling, mimo, north-mini, big-pickle),
  `max_fallback_attempts: 5`, `cooldown: 2s`, `timeout: 15s`.

## Uso
```powershell
ecosystem sync
```
Faz: pull â†’ consolida conhecimento â†’ commit+push do Eco â†’ deploy config/agents â†’
valida (debug config + preflight) â†’ pull/commit/push de todos os 12 repos irmÃ£os.

## LiÃ§Ã£o
- Em MCP `command` e em `plugin`, o opencode NÃƒO resolve `{{USERPROFILE}}` nem aceita
  objeto â€” usar paths absolutos no deploy e array de strings no plugin.
- O deploy real da config Ã© responsabilidade do `ecosystem sync`; o repo Ã© a fonte Ãºnica.
- **Portabilidade do setup.bat**: o template `config/opencode.jsonc` NÃƒO pode ter paths
  hardcoded de um usuÃ¡rio especÃ­fico (ex.: `C:/Users/David Jr/...`). Todo path deve usar
  `{{USERPROFILE}}` para o setup.bat/substituiÃ§Ã£o funcionar em qualquer PC. TambÃ©m removida
  a junction `~/.ler` obsoleta (LER usa `run.py`/`run.ps1` no repo) e adicionado passo 8
  de validaÃ§Ã£o (`opencode debug config`) no setup.bat.

## Conexoes

- [[cluster-hub-programacao]]