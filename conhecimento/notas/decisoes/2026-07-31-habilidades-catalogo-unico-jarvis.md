---
tags: [decisao, ecossistema, arquitetura, habilidades, agentes]
aliases: [2026-07-31: Habilidades vs Agentes — Catálogo Único de Capacidades do Jarvis]
date: 2026-07-31
---

# 2026-07-31: Habilidades vs Agentes — Catálogo Único de Capacidades do Jarvis

**Fonte:** opencode (sessão de revisão de arquitetura)

**Categoria:** decisao
**Contexto:** O usuário consolidou uma ideia persistente de organização: criar um local único e dedicado para **habilidades do Jarvis**, onde cada capacidade adquirida/aprendida é organizada automaticamente. É **crucial** manter a distinção: agentes NÃO são habilidades. A avaliação do estado real do repo (branch `opencode/mighty-meadow`) confirmou que `ler-runtime/` já é o cérebro único e `skills/` já concentra as capacidades — a decisão formaliza e padroniza essa separação.
**Gravidade:** MÉDIA — organizacional; risco de quebra se executada sem guardrails (bridge e opencode.jsonc dependem dos caminhos atuais)

## Definições (a distinção que não pode ser violada)

- **Habilidades** = capacidades **executáveis** (ações). Atômicas, com entrada → saída. Não têm opinião, não decidem nada. Ex.: `clima-api`, `busca-conhecimento`, `android-diagnostics`.
- **Agentes** = **tomadores de decisão** (personalidades). Analisam, debatem e escolhem **qual** habilidade acionar, **com quais parâmetros** e **em que ordem**. Nunca executam a ação diretamente.

Fluxo: Agente decide `executar_habilidade("clima-api", {cidade})` → Habilidade executa → Agente avalia o resultado. O agente nunca sabe *onde* o código mora; a habilidade nunca decide.

**Regra de ouro da distinção:** nenhum agente dentro de `Habilidades/`; nenhuma habilidade dentro de agentes. Agentes permanecem exclusivamente em `ler-runtime/agent/` (runtime Python) e `config/agents/*.md` (definições de personalidade).

## Decisão

1. **Criar `Habilidades/` como o catálogo ÚNICO e vivo de capacidades do Jarvis.** Toda habilidade nova que o Jarvis aprender/adquirir é organizada dentro dele — a estrutura é auto-organizada pelo agente de aprendizado.
2. **Manter agentes intocados** em `ler-runtime/agent/` + `config/agents/`.
3. **Criar `manifesto_geral.json`** como o contrato: única fonte que os agentes consultam para saber quais habilidades existem e como acioná-las. Se não está no manifesto, não existe para o Jarvis.
4. **`scripts/` = apenas infraestrutura** (bridge, watchdog, vigilante, memory_engine, mcp-server, preflight). Nunca recebe habilidades.
5. **Executar em branch própria** (`reorg/habilidades`), com backup e testes antes/depois.

## Estrutura-alvo

```
Habilidades/
├── tecnicas/                    ← antigo skills/ (capacidades técnicas)
│   ├── clima-api/
│   ├── android-diagnostics/
│   ├── mp3player-metadata-rescue/
│   └── ... (36 skills atuais)
├── comportamentais/             ← comportamento/personalidade acionável
│   └── ponytail/                (ex.: comandos /preguiça, /review, /sarcasmo)
├── pontes/                      ← interfaces externas acionáveis como habilidade
│   ├── busca-web/               (antigo skills/agentic-search)
│   └── busca-conhecimento/      (antigo scripts/search_knowledge.py)
├── multimidia/                  ← áudio/imagem/vídeo (se houver separação pura)
└── manifesto_geral.json         ← índice oficial de todas as habilidades
```

## Mapa de migração do estado atual

| Atual | Destino | Observação |
|---|---|---|
| `skills/` (36 dirs) | `Habilidades/tecnicas/` | nomes de diretório mantidos |
| `skills/agentic-search` | `Habilidades/pontes/busca-web/` | é busca externa, não skill técnica |
| `scripts/search_knowledge.py` | `Habilidades/pontes/busca-conhecimento/` | |
| `scripts/clima_api.py` | `Habilidades/tecnicas/clima-api/` | entrypoint real é `clima_api.py` (não `clima.py`) |
| `scripts/geolocalizacao.py` | **NÃO vira habilidade** | dependência interna de `clima-api`; empacotar junto ou manter onde a bridge acha |
| `plugins/ponytail/` | `Habilidades/comportamentais/ponytail/` | ⚠ está VAZIO no repo — localizar o ponytail real antes |
| `scripts/parallel_dispatcher.py` | permanece em `scripts/` ou `ler-runtime/tools/` | é concorrência/locks, não dispatcher de habilidades |

**36 skills de `tecnicas/`:** agentic-search*, android-diagnostics, android-pure-sdk, api-design, authz-authn-matrix, autonomous-loops, backend-patterns, cache-strategy-selector, clima-api, concurrent-computation-patterns, cost-aware-llm-pipeline, data-privacy-by-design, database-migrations, deployment-patterns, developer-experience-dx, docker-patterns, e2e-testing, edge-compute-patterns, error-message-design, frontend-patterns, golang-patterns, graphify, ler, local-first-architecture, migration-playbooks, mobile-specific-patterns, mp3player-metadata-rescue, multi-modal-ai, observability-stack, python-patterns, resilience-engineering, search-first, security-review, semantic-release-automation, state-machine-patterns, tdd-workflow. (*`agentic-search` vai para `pontes/busca-web/`, não fica em tecnicas.)

**NÃO são habilidades (infraestrutura, permanecem em `scripts/`):** `jarvis_bridge.py`, `run_bridge.py`, `run_serve.py`, `ecosystem.ps1`, `vigilante.ps1`, `watchdog.ps1`, `guardian_manager.ps1`, `system_guardian.py`, `memory_engine.py`, `mcp-knowledge-server.py`, `preflight_check.py`, `bootstrap.ps1`, `deploy-config.ps1`, `generate-obsidian-notes.py`, `test-ecosystem.ps1`, `test_vox.py`.

## Contrato do `manifesto_geral.json`

Cada habilidade registra: `id`, `categoria` (tecnica/comportamental/ponte/multimidia), `descricao`, `entrypoint` (script/manifesto), `parametros`, `triggers` (palavras-chave de ativação), `dependencias`. O kernel do `ler-runtime` carrega o manifesto na inicialização e o orquestrador usa `executar_habilidade(id, parametros)` (subprocess/import dinâmico/API interna).

## Guardrails de execução (não esquecer)

1. **Bridge em produção**: `jarvis_bridge.py` importa `from clima_api import get_weather_data, get_forecast_data` e `clima_api` importa `geolocalizacao`. Mover esses módulos **quebra a saudação** — exigir shim de `sys.path` ou manter entrypoints onde a bridge os encontra. Testar a saudação via voz após a migração.
2. **`config/opencode.jsonc`**: globs `skills/*/SKILL.md`, `skills/**/SKILL.md`, `skills/clima-api/skill.md` e `ler-runtime/CONHECIMENTO.md` alimentam o opencode. Renomear `skills/` quebra a injeção. Além disso, o template aponta para `{{USERPROFILE}}/Desktop/Codigos/...` (caminho **antigo** — hoje é `Documents\Default Project`). Atualizar ambos.
3. **Ponytail**: `plugins/ponytail/` está vazio no repo e não existe em `~/.config/opencode`. Localizar o ponytail real antes de "migrar" (procurar `ponytail.mjs` / `manifesto.json` / comandos).
4. **`ai-agents/`** (195 arquivos, subárvore `claude-code-extra-agents`): repo aninhado — decidir submodule vs remoção antes da reorganização.
5. **`mcp-servers/`** está vazio — remover ou documentar.
6. **Dois "scripts"**: `ler-runtime/scripts/` (run.ps1, setup.ps1, git_setup.ps1) vs `scripts/` raiz — documentar a diferença.
7. **Sujeira**: `scripts/.env` (segredos reais!), `bridge_out.txt`, `bridge_err.txt`, `openapi_spec.json`, `guardian.pid`, `watchdog_log.txt` — adicionar ao `.gitignore`.
8. **`ler/EcossistemaAgentes.md`**: é 1 doc de bootstrap (183 linhas), não "cérebro legado" — mover para `docs/` ou `conhecimento/`, NÃO deletar.
9. **Submodule `Android/VoxUmGrau`**: VoxUmGrau também é repo separado no workspace — manter apenas uma representação.
10. **`ler-runtime/agent/knowledge_consolidator.py`** lê skills de `.claude/skills` — não é afetado pela migração, mas documentar para não confundir com `Habilidades/`.

## Mecanismos

1. **Agente de aprendizado auto-organizador**: ao adquirir/implementar uma habilidade nova, o agente `10-aprendizado` cria a pasta em `Habilidades/`, registra no `manifesto_geral.json` e valida o entrypoint.
2. **Validação do manifesto**: teste que confere cada `entrypoint` do manifesto contra as pastas/arquivos reais (estender `preflight_check.py`).
3. **Interface única**: `executar_habilidade(id, parametros)` — agentes nunca importam módulos diretamente.

## Trigger

- Ao criar/adquirir qualquer nova capacidade para o Jarvis.
- Ao reorganizar skills/scripts/plugins.
- Ao revisar arquitetura do ecossistema (este doc é o ponto de referência).

## Próximos passos

1. Revisar este rascunho com o usuário; confirmar a Opção A (manifesto sem mover arquivos) vs Opção B (migração completa em branch).
2. Localizar o ponytail real (ponto 3 dos guardrails).
3. Limpar sujeira + `.gitignore` (guardrail 7) — ação de baixo risco, pode ir primeiro.
4. Definir tratamento de `ai-agents/` e do submodule (guardrails 4 e 9).
5. Executar migração (se Opção B) em `reorg/habilidades` com backup, atualizando opencode.jsonc e bridge.
6. Atualizar `README.md` e `estado_atual.md` ao concluir.

## Ver também

- [[taxonomia-correta-de-habilidades-jarvis]] — taxonomia de 3 níveis das habilidades
- [[registro-de-habilidades-de-jarvis]] — padrão de registro de habilidades no manifesto
