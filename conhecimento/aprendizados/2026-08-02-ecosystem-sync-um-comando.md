# 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo

## Contexto
O usuário queria sincronizar o ecossistema inteiro com um único comando, para ficar
sempre atualizado e nada se perder ao trocar de PC.

## O que foi feito
- Corrigido `scripts/ecosystem.ps1`:
  - `$ecoDir` agora é auto-detectado via `Split-Path $PSScriptRoot -Parent` (antes
    hardcoded `Desktop\Codigos\EcoSystemUmGrau`, que não existe mais — o repo vive em
    `Documents\Default Project\EcoSystemUmGrau`).
  - `$projectsDir` aponta para `Documents\Default Project` (todos os repos irmãos).
  - Novo `Sync-DeployConfig`: renderiza `config/opencode.jsonc` trocando
    `{{USERPROFILE}}` → caminho real, copia agents (16) e `opencode-model-fallback.jsonc`
    para `~/.config/opencode/`, garante plugin `@razroo/opencode-model-fallback`
    instalado, valida com `opencode debug config` + `scripts/preflight_check.py`.
  - Consolidação do conhecimento (CONHECIMENTO.md + notas Obsidian) movida para ANTES
    do commit, para não deixar pendência após o sync.
  - Exclui o próprio Eco do loop de projetos irmãos (evita commit duplicado).
- Corrigido `config/opencode.jsonc` (template): `plugin` deve ser array de strings
  `["@razroo/opencode-model-fallback"]`, NÃO objeto `{name, config}`. A config real do
  plugin fica em `config/opencode-model-fallback.jsonc` (o plugin lê
  `~/.config/opencode/opencode-model-fallback.jsonc`).
- Corrigido `config/opencode-model-fallback.jsonc`: cadeia de 7 modelos FREE
  (nemotron, deepseek-v4-flash, laguna, ling, mimo, north-mini, big-pickle),
  `max_fallback_attempts: 5`, `cooldown: 2s`, `timeout: 15s`.

## Uso
```powershell
ecosystem sync
```
Faz: pull → consolida conhecimento → commit+push do Eco → deploy config/agents →
valida (debug config + preflight) → pull/commit/push de todos os 12 repos irmãos.

## Lição
- Em MCP `command` e em `plugin`, o opencode NÃO resolve `{{USERPROFILE}}` nem aceita
  objeto — usar paths absolutos no deploy e array de strings no plugin.
- O deploy real da config é responsabilidade do `ecosystem sync`; o repo é a fonte única.
- **Portabilidade do setup.bat**: o template `config/opencode.jsonc` NÃO pode ter paths
  hardcoded de um usuário específico (ex.: `C:/Users/David Jr/...`). Todo path deve usar
  `{{USERPROFILE}}` para o setup.bat/substituição funcionar em qualquer PC. Também removida
  a junction `~/.ler` obsoleta (LER usa `run.py`/`run.ps1` no repo) e adicionado passo 8
  de validação (`opencode debug config`) no setup.bat.
