# Aprendizado â€” 2026-07-31 â€” Reorg: catÃ¡logo Ãºnico Habilidades/ + caminhos novos

## Contexto
- Skills estavam espalhadas em `skills/` e `scripts/` (clima, busca), e o array `plugin` do opencode.jsonc apontava para `plugins/ponytail` (inexistente â€” ClÃ¡usula PÃ©trea). DecisÃ£o `2026-07-31-habilidades-catalogo-unico-jarvis.md`: Habilidades = aÃ§Ãµes executÃ¡veis; Agentes = tomadores de decisÃ£o (nÃ£o mexer).

## O que foi feito
1. **`Habilidades/`** â€” catÃ¡logo Ãºnico, 38 habilidades:
   - `tecnicas/` (35 skills vindas de `skills/*`), `pontes/busca-web` (agentic-search), `pontes/busca-conhecimento` (search_knowledge), `tecnicas/clima-api` (clima_api.py + geolocalizacao.py), `comportamentais/ponytail/`, `multimidia/`.
   - `manifesto_geral.json` â€” 38 habilidades com categoria/id/descriÃ§Ã£o; todas as pastas verificadas.
2. **Config**: `config/opencode.jsonc` (template) e `~/.config/opencode/opencode.jsonc` (mÃ¡quina) â†’ globs `Habilidades/**/{SKILL,skill}.md`; caminho `Documents/Default Project`; ponytail removido do `plugin`.
3. **Bridge/servers**: `jarvis_bridge.py` ganhou shim `sys.path` â†’ `Habilidades/tecnicas/clima-api`; `mcp-knowledge-server.py` â†’ `Habilidades/pontes/busca-conhecimento/search_knowledge.py`.
4. **CI/testes**: `eco-sync.yml` conta `Habilidades`; `test-ecosystem.ps1` matcher atualizado; `00-system-rules.md` gatilho `plugins/*` â†’ `Habilidades/*`.
5. **Docs**: `estado_atual.md`, `README.md`, `JARVIS_SYSTEM.md`, `MOC - Projetos.md`; `ler/EcossistemaAgentes.md` â†’ `docs/`.
6. **Limpeza**: `.gitignore` ampliado (inclui `scripts/serve_log.txt`); removidos do index runtime trackeados (guardian.*, watchdog_log.txt, test_greeting.json); gitlink quebrado `Android/VoxUmGrau` removido.

## HeurÃ­sticas registradas
- **CatÃ¡logo Ãºnico vs estrutura nova (Regra de Ouro)**: mover para estrutura EXISTENTE quando a nova casa Ã© sÃ³ uma reorganizaÃ§Ã£o de arquivos (mesmo repo), nÃ£o uma estrutura nova de conhecimento.
- **`git mv` preserva histÃ³rico**: usar `git mv` para mover skills preserva o histÃ³rico (renames a 100%).
- **`opencode serve` desta versÃ£o NÃƒO aceita `-c`/`--dir`** (nem global, nem no subcomando â€” imprime help e sai). Iniciar canÃ´nico: `opencode serve --port 8766` com `cwd=WORKDIR`; a config vem da cadeia do diretÃ³rio (mÃ¡quina + projeto).
- **`.gitignore` nÃ£o cobre arquivo trackeado**: arquivo que foi commitado continua visÃ­vel; precisa `git rm --cached` + `.gitignore`. PadrÃ£o `*.log` nÃ£o cobre `*.log.txt`.
- **Manifesto valida estrutura**: script de conferÃªncia (toda habilidade tem pasta/categoria) evita drift entre JSON e disco.

## Estado
- Preflight OK (ClÃ¡usula PÃ©trea); JSONs vÃ¡lidos; `py_compile` OK; geolocalizaÃ§Ã£o/busca/briefing OK nos novos caminhos.
- Bridge reiniciada â†’ saudaÃ§Ã£o real no log; serve reiniciado (`run_serve.py` corrigido) â†’ 8766 ativo, sessÃµes HTTP OK.
- Commit `38e8468` na branch `reorg/habilidades`, pushada para o GitHub.

## Conexoes

- [[cluster-hub-programacao]]