# Aprendizado — 2026-07-31 — Reorg: catálogo único Habilidades/ + caminhos novos

## Contexto
- Skills estavam espalhadas em `skills/` e `scripts/` (clima, busca), e o array `plugin` do opencode.jsonc apontava para `plugins/ponytail` (inexistente — Cláusula Pétrea). Decisão `2026-07-31-habilidades-catalogo-unico-jarvis.md`: Habilidades = ações executáveis; Agentes = tomadores de decisão (não mexer).

## O que foi feito
1. **`Habilidades/`** — catálogo único, 38 habilidades:
   - `tecnicas/` (35 skills vindas de `skills/*`), `pontes/busca-web` (agentic-search), `pontes/busca-conhecimento` (search_knowledge), `tecnicas/clima-api` (clima_api.py + geolocalizacao.py), `comportamentais/ponytail/`, `multimidia/`.
   - `manifesto_geral.json` — 38 habilidades com categoria/id/descrição; todas as pastas verificadas.
2. **Config**: `config/opencode.jsonc` (template) e `~/.config/opencode/opencode.jsonc` (máquina) → globs `Habilidades/**/{SKILL,skill}.md`; caminho `Documents/Default Project`; ponytail removido do `plugin`.
3. **Bridge/servers**: `jarvis_bridge.py` ganhou shim `sys.path` → `Habilidades/tecnicas/clima-api`; `mcp-knowledge-server.py` → `Habilidades/pontes/busca-conhecimento/search_knowledge.py`.
4. **CI/testes**: `eco-sync.yml` conta `Habilidades`; `test-ecosystem.ps1` matcher atualizado; `00-system-rules.md` gatilho `plugins/*` → `Habilidades/*`.
5. **Docs**: `estado_atual.md`, `README.md`, `JARVIS_SYSTEM.md`, `MOC - Projetos.md`; `ler/EcossistemaAgentes.md` → `docs/`.
6. **Limpeza**: `.gitignore` ampliado (inclui `scripts/serve_log.txt`); removidos do index runtime trackeados (guardian.*, watchdog_log.txt, test_greeting.json); gitlink quebrado `Android/VoxUmGrau` removido.

## Heurísticas registradas
- **Catálogo único vs estrutura nova (Regra de Ouro)**: mover para estrutura EXISTENTE quando a nova casa é só uma reorganização de arquivos (mesmo repo), não uma estrutura nova de conhecimento.
- **`git mv` preserva histórico**: usar `git mv` para mover skills preserva o histórico (renames a 100%).
- **`opencode serve` desta versão NÃO aceita `-c`/`--dir`** (nem global, nem no subcomando — imprime help e sai). Iniciar canônico: `opencode serve --port 8766` com `cwd=WORKDIR`; a config vem da cadeia do diretório (máquina + projeto).
- **`.gitignore` não cobre arquivo trackeado**: arquivo que foi commitado continua visível; precisa `git rm --cached` + `.gitignore`. Padrão `*.log` não cobre `*.log.txt`.
- **Manifesto valida estrutura**: script de conferência (toda habilidade tem pasta/categoria) evita drift entre JSON e disco.

## Estado
- Preflight OK (Cláusula Pétrea); JSONs válidos; `py_compile` OK; geolocalização/busca/briefing OK nos novos caminhos.
- Bridge reiniciada → saudação real no log; serve reiniciado (`run_serve.py` corrigido) → 8766 ativo, sessões HTTP OK.
- Commit `38e8468` na branch `reorg/habilidades`, pushada para o GitHub.
