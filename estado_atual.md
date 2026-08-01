# Snapshot do Ecossistema — 2026-07-28 (v12 - Estágio 3: Orquestrado)

> **Evolução:** Estágio 2 (Estruturado) → **Estágio 3 (Orquestrado)** ✅
> Adicionado: memória entre sessões (Ebbinghaus), busca semântica (BM25), MCP (3 servidores),
> SDLC gates (5 gates formais), CI/CD (GitHub Actions), e métricas de performance.
>
> ## FONTE ÚNICA: O REPOSITÓRIO
> Toda config, agente e skill vive no repo `EcoSystemUmGrau/config/` e `Habilidades/`.
> Nada duplicado. setup.bat gera os arquivos no destino a partir dos templates.
>
> ## REGRA DE OURO: ABASTECER, NÃO CRIAR ESTRUTURA NOVA
> O ecossistema já está estruturado. Todo projeto deve apenas **abastecer** as
> estruturas existentes — conhecimento, decisões, padrões, bugs — sem criar novas
> pastas, novos repositórios, novos tipos de aprendizado fora do que já foi definido.
> Antes de criar algo, pergunte: "Isso abastece uma estrutura existente ou cria
> uma nova?" Se for nova, não faça. Use as categorias já existentes no CONHECIMENTO.md:
> Decisoes, Padroes Tecnicos, Bug Fixes, Padroes Cognitivos, Heuristicas, Frameworks,
> Missoes Aprendidas. Qualquer projeto que precisar de algo novo primeiro deve
> conversar com o ecossistema para ver se já existe. Só criar se realmente não existir,
> e mesmo assim deve ser feito dentro da estrutura estabelecida, não fora dela.
>
> ## REGRA OBRIGATÓRIA: TESTAR SEMPRE
> Toda alteração no opencode.jsonc, plugins, agents ou skills deve ser testada
> com `opencode debug config` antes de considerar concluída.
>
> ## FALLBACK AUTOMÁTICO
> Quando um modelo bate limite de uso, o plugin @razroo/opencode-model-fallback
> troca automaticamente para o próximo modelo na cadeia (nvidia/deepseek-v3.1)
> sem intervenção manual. Cooldown de 60s com auto-recovery.
>
> ## SETUP.BAT — PLUG & PLAY
> `setup.bat` na raiz do repo faz tudo automaticamente em PC novo:
> clona, instala OpenCode, gera configs, configura LER, pergunta API Keys.
> Unico comando: `git clone ... && cd EcoSystemUmGrau && setup.bat`
>
> ## LER ENXUTO (64 ARQUIVOS, SÓ CÓDIGO + CONFIG + CONHECIMENTO)
> Checkpoints, logs, memória de missão e relatórios foram removidos do
> versionamento (.gitignore restritivo). Só o que importa: .py, configs,
> knowledge_graph.json, CONHECIMENTO.md.
>
> ## MAESTRO COM MATRIZ DE DECISÃO
> Rota A (OpenCode): tarefa simples, 1-3 arquivos, resultado óbvio.
> Rota B (LER): multi-passo, exploração, loop, 4+ arquivos, >15min.
> Rota C (Híbrido): começa A, vira B se o contexto crescer.
>
> ## ECOSYSTEM REPAIR
> Reconstrói o knowledge_graph.json a partir dos .md crus em
> conhecimento/aprendizados/. Útil se o grafo corromper.
>
> ## VIGILANTE COM FILESYSTEMWATCHER
> Tempo real (sem polling), monitora TODOS os projetos Android (não só aprendizado).
> Sync bidirecional (pull → commit → push) para EcoSystemUmGrau + Android repos.
> Auto-descoberta: varre Android/ por pastas com git remote — sem config manual.
>
> ## ECOSYSTEM.PS1 — 4 COMANDOS
> ecosystem sync    → pull + push forcado (Eco + LER + TODOS os projetos Android)
> ecosystem scan    → varre projetos, extrai métricas
> ecosystem repair  → reconstrói knowledge graph dos aprendizados crus
> ecosystem status  → status completo (inclui status git de cada projeto Android)

## ESTÁGIO 3 — ORQUESTRADO (v12)

### O que foi adicionado

| Capacidade | Antes | Agora | Status |
|---|---|---|---|
| **Memória entre sessões** | ❌ Nada | ✅ Ebbinghaus decay + reforço + sessões JSONL | ✅ |
| **Busca semântica** | ❌ Só grep | ✅ BM25 lexical + tag fusion em 4 fontes | ✅ |
| **MCP** | ❌ Nada | ✅ 3 servidores: knowledge, filesystem, github | ✅ |
| **SDLC Gates** | ❌ Maestro simples | ✅ G1-G5 com critérios de evidência | ✅ |
| **Métricas** | ❌ Nada | ✅ Memory engine stats + CI report | ✅ |
| **CI/CD** | ❌ Só vigilante local | ✅ GitHub Actions (eco-sync + report) | ✅ |

### Arquitetura atual (3 cérebros)

```
1. KNOWLEDGE GRAPH (248 entradas) — conhecimento explícito
   KnowledgeConsolidator.register_learning() → knowledge_graph.json → CONHECIMENTO.md

2. MEMORY ENGINE (Ebbinghaus decay) — memória de sessão
   memory_engine.py → sessions JSONL → memories.json → index.json
   → Score: strength * (0.5 ^ (days / half_life))
   → Half-life: erro=90d, padrao=60d, decisao=30d, episodio=7d
   → Acesso frequente = reforço (strength += 0.15)

3. SEMANTIC SEARCH (BM25 fusion) — busca unificada
   search_knowledge.py → corpus de 4 fontes (KG + memória + notas + skills)
   → BM25 scoring → top 20 resultados
```

### Fluxo de tarefa (com quality gates)

```
Usuário → Maestro
  → Carrega contexto de memória (memory_engine.py context)
  → Classifica (Rota A/B/C)
  → G1 PLAN → G2 IMPLEMENT → G3 VERIFY → G4 REVIEW → G5 MERGE
    → Se gate falha: retorna ao passo anterior
  → Registra aprendizado (aprendizados/)
  → Registra memória (memory_engine.py add)
  → git push (via vigilante)
```

### Diagrama do ecossistema completo

```
┌─────────────────────────────────────────────────┐
│                  OPENCODE                       │
│  15 agents → Maestro roteia + 5 gates SDLC      │
│  MCP: 3 servidores (knowledge+filesystem+github)│
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌──────────┐     ┌──────────────┐
│ LER      │     │ VIGILANTE    │
│ Python   │     │ FSWatcher    │
│ loop     │     │ 5 repos      │
│ autonomo │     │ tempo real   │
└──────────┘     └──────┬───────┘
                        │
               ┌────────┴────────┐
               ▼                 ▼
        ┌──────────┐     ┌──────────────┐
        │ CRANIO 1 │     │ CRANIO 2     │
        │ KNOWLEDGE│     │ MEMORY       │
        │ GRAPH    │     │ ENGINE       │
        │ 248 ents │     │ Ebbinghaus   │
        └──────────┘     └──────────────┘
               │                 │
               └────────┬────────┘
                        ▼
                ┌──────────────┐
                │ OBSIDIAN     │
                │ 228 notas    │
                │ Dataview MOCs│
                │ Graph View   │
                └──────────────┘
                        │
                        ▼
                ┌──────────────┐
                │ GITHUB       │
                │ EcoSystemUmGrau│
                │ + 4 projetos │
                │ + CI/CD      │
                └──────────────┘
```

### Arquitetura final do conhecimento automático

```
Maestro (passo 11 obrigatório)
  → 10-Aprendizado escreve conhecimento/aprendizados/YYYY-MM-DD-N.md
      → Vigilante.ps1 (FileSystemWatcher, tempo real)
          ├── Watcher aprendizado (300ms debounce)
          │   → Chama KnowledgeConsolidator.register_learning()
          │       → Atualiza knowledge_graph.json (merge Jaccard)
          │       → Exporta CONHECIMENTO.md
          ├── Watcher projetos Android (3s debounce)
          │   → Detecta alterações em .kt/.java/.py/.xml/.json
          │   → Marca repo como dirty → sync imediato
          └── Timer 30s: git sync todos os repos
              → EcoSystemUmGrau (push, 5min cooldown)
              → LER (local, 5min cooldown)
              → Android/Mp3Player, CellCleaner, Biblia, SupermarketCalculator (push, 1min cooldown)
      → CONHECIMENTO.md carregado no contexto de todo agente via opencode.jsonc
```

### Comandos disponíveis

| Comando | Função |
|---|---|---|
| `start-vigilante` | Inicia watcher + git sync em background (monitora TODOS os projetos) |
| `stop-vigilante` | Para o processo |
| `status-vigilante` | Status do vigilante |
| `ecosystem sync` | Pull + push forcado (Eco + LER + projetos Android) |
| `ecosystem scan` | Varre projetos, extrai padrões, registra aprendizado |
| `ecosystem status` | Status completo do ecossistema (inclui status git de cada projeto) |
| `ecosystem help` | Ajuda detalhada |

---

## OBSIDIAN VAULT INTELIGENTE (vault = raiz do ecossistema)

> Vault completamente integrado: plugins, templates, MOCs, workspace, autosync.

**Plugins instalados:**
- **Obsidian Git** — auto-commit local a cada 5 min; vigilante faz o push
- **Dataview** — queries SQL-like nas notas (tabelas dinâmicas nas MOCs)

**Config:**
- `core-plugins.json`: 20 core plugins ativos (file-explorer, graph, templates, etc.)
- `community-plugins.json`: obsidian-git + dataview
- `appearance.json`: tema Obsidian (dark), accent #6c5ce7, fonte Inter
- `hotkeys.json`: Ctrl+P palette, Ctrl+O switcher, Ctrl+Shift+T template, Ctrl+Shift+S git, Ctrl+Shift+G graph
- `templates.json`: pasta `conhecimento/templates/`
- `workspace.json`: INDEX.md central + file-explorer/search à esquerda + graph/tags à direita
- `graph.json`: showTags, showArrow, linkDistance 250

**Templates (4):**
| Template | Uso |
|----------|-----|
| `template-aprendizado.md` | Nova entrada de aprendizado |
| `template-decisao.md` | Nova decisão arquitetural |
| `template-bug.md` | Novo bug corrigido |
| `template-padrao.md` | Novo padrão técnico |

**MOCs (8 Mapas de Conteúdo):**
| MOC | Cobre |
|-----|-------|
| `INDEX.md` | Entry point do vault |
| `MOC - Projetos.md` | Mp3Player, CellCleaner, Biblia, SupermarketCalculator |
| `MOC - Conhecimento.md` | Decisões, padrões, skills (34) |
| `MOC - Decisoes.md` | 20+ decisões arquiteturais + infra |
| `MOC - Bugs.md` | 30+ bugs com causa raiz e correção |
| `MOC - Heuristicas.md` | 32 heurísticas de debugging/código |
| `MOC - Frameworks.md` | 10 frameworks de raciocínio |
| `MOC - Padroes Cognitivos.md` | 22 padrões cognitivos |
| `MOC - Padroes.md` | 71 padrões técnicos tabelados |

**Integração:**
- Obsidian Git commita localmente → vigilante detecta mudanças no `.obsidian/` → push automático
- Mudanças no `conhecimento/aprendizados/` aparecem automaticamente no Obsidian (mesmo filesystem)
- Dataview queries nas MOCs listam dinamicamente os aprendizados
- Templates disponíveis via `Ctrl+Shift+T`

**Atalhos:**
| Atalho | Ação |
|--------|------|
| `Ctrl+P` | Command palette |
| `Ctrl+O` | Quick switcher |
| `Ctrl+K` | Inserir wikilink |
| `Ctrl+Shift+T` | Inserir template |
| `Ctrl+Shift+S` | Git commit + push |
| `Ctrl+Shift+G` | Graph view |
| `Ctrl+Shift+R` | Refresh Dataview |

## 1. Estrutura de Pastas

### GitHub (12 repos, 1 ecossistema)

| Repo | Local | Tipo |
|---|---|---|
| `EcoSystemUmGrau` | `Desktop\Codigos\EcoSystemUmGrau\` | **Ecossistema** (config, agents, skills, setup.bat) |
| `Mp3Player` | `Desktop\Codigos\Android\Mp3Player\` | Android/Kotlin |
| `CellCleaner` | `Desktop\Codigos\Android\CellCleaner\` | Android/Java |
| `SupermarketCalculator` | `Desktop\Codigos\Android\SupermarketCalculator\` | Android/Java |
| `BibliaEstudoCompleta` | `Desktop\Codigos\Android\Biblia\` | Android/Java |
| `WindowsMaintenanceSuite_v3` | (so remoto) | PowerShell |
| `OrquestradorAPK-FLUTTER` | (so remoto) | Python |
| `compiladorAPK` | `~/.apk_compiler\` | PowerShell |
| `roboumgrau` | (so remoto) | HTML |
| `Rob-Trader` | (so remoto) | JS |
| `claude-code-extra-agents` | (so remoto) | Python |

> **LER runtime** (`~/.ler/`) nao tem remote proprio. O conhecimento
> viaja no EcoSystemUmGrau via conhecimento/aprendizados/ + CONHECIMENTO.md.
> setup.bat inicializa o LER em qualquer maquina.

### `Documents/Default Project/EcoSystemUmGrau/` (ecossistema — fonte unica)
```
.obsidian/           # Vault Obsidian (VAULT_PATH atualizado)
ler-runtime/         # LER runtime (antigo ~/.ler/) — cérebro único — versionado aqui
Habilidades/         # ★ Catálogo único de habilidades (decisão 2026-07-31-habilidades-catalogo-unico-jarvis)
├── tecnicas/        # 35 habilidades técnicas (skills antigas)
│   ├── graphify/
│   ├── ler/
│   ├── clima-api/   # + clima_api.py e geolocalizacao.py (Open-Meteo, sem chave)
│   ├── api-design/
│   ├── authz-authn-matrix/
│   ├── autonomous-loops/
│   ├── backend-patterns/
│   ├── cache-strategy-selector/
│   ├── concurrent-computation-patterns/
│   ├── cost-aware-llm-pipeline/
│   ├── data-privacy-by-design/
│   ├── database-migrations/
│   ├── deployment-patterns/
│   ├── developer-experience-dx/
│   ├── docker-patterns/
│   ├── e2e-testing/
│   ├── edge-compute-patterns/
│   ├── error-message-design/
│   ├── frontend-patterns/
│   ├── golang-patterns/
│   ├── local-first-architecture/
│   ├── migration-playbooks/
│   ├── mobile-specific-patterns/
│   ├── mp3player-metadata-rescue/
│   ├── multi-modal-ai/
│   ├── observability-stack/
│   ├── python-patterns/
│   ├── resilience-engineering/
│   ├── search-first/
│   ├── security-review/
│   ├── semantic-release-automation/
│   ├── state-machine-patterns/
│   └── tdd-workflow/
├── pontes/
│   ├── busca-web/            # antigo skills/agentic-search
│   └── busca-conhecimento/   # antigo scripts/search_knowledge.py
├── comportamentais/ponytail/ # pendente de conteúdo real
├── multimidia/
└── manifesto_geral.json      # índice oficial (38 habilidades)
ai-agents/           # Claude Code extra agents
├── claude-code-extra-agents/
scripts/             # Apenas infraestrutura (bridge, vigilante, memory_engine, mcp-server, preflight)
ferramentas/         # Ferramentas
├── FLUTTER/
documentos/          # Documentos diversos
config/agents/       # Definições dos 17 agentes (tomadores de decisão)
docs/                # Documentação (EcossistemaAgentes.md migrado de ler/)
estado_atual.md      # Este arquivo
```

---

## 2. Runtime

| Componente | Versão | Localização |
|---|---|---|
| **OpenCode** | `1.18.7` | `npm i -g opencode-ai` |
| **Node.js** | `v25.9.0` | `C:\Program Files\nodejs\` |
| **npm** | `11.12.1` | — |
| **Bun** | `1.3.14` | `~\.bun\bin\bun.exe` |
| **Python** | `3.12.7` | `C:\Program Files\Python312\` |
| **pip** | `24.2` | — |
| **Git** | `2.55.0.windows.2` | `C:\Program Files\Git\cmd` |
| **gh CLI** | `2.96.0` | `C:\Program Files\GitHub CLI\gh.exe` |
| **OS** | Windows (PowerShell 5.1) | — |

---

## 3. Config OpenCode (`~/.config/opencode/opencode.jsonc`)

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "nvidia": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "NVIDIA",
      "options": {
        "baseURL": "https://integrate.api.nvidia.com/v1",
        "apiKey": "{env:NVIDIA_API_KEY}"
      }
    }
  },
  "instructions": [
    "C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/Habilidades/**/SKILL.md",
    "C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/Habilidades/**/skill.md",
    "C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/Habilidades/tecnicas/clima-api/skill.md",
    "C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/ler-runtime/CONHECIMENTO.md"
  ]
}
```

**Plugins ativos:**
1. `ponytail.mjs` — Modo `full` via `.ponytail-active`
2. `@razroo/opencode-model-fallback` v0.3.2 — Fallback automático de modelos

**Plugin config:** `~/.config/opencode/opencode-model-fallback.jsonc`
- Fallback global: `nvidia/deepseek-ai/deepseek-v3.1`
- Cooldown: 60s, Timeout TTFT: 30s
- Notificações toast ativadas

---

## 4. Agents (13)

Carregados de `~/.config/opencode/agents/`:

| Arquivo | Modo | Função |
|---|---|---|
| `00-maestro.md` | `primary` | Coordenador principal |
| `00-system-rules.md` | — | Constituição (prioridade máxima) |
| `00-agent-template.md` | — | Template p/ criar agentes |
| `01-estrategista.md` | `subagent` | Direção, objetivos |
| `02-cetico.md` | `subagent` | Desafiar hipóteses |
| `03-realista.md` | — | Viabilidade prática |
| `04-etica.md` | — | Conformidade |
| `05-futuro.md` | — | Tendências |
| `06-recursos.md` | — | Mapear recursos |
| `07-criativo.md` | — | Soluções inovadoras |
| `08-revisor.md` | `subagent` | Revisão |
| `09-executor.md` | `subagent` | Implementar |
| `10-aprendizado.md` | `subagent` | Extrair e persistir conhecimento (passo final obrigatório) |
| `11-ler-executor.md` | `subagent` | Delegar tarefas complexas ao LER (loop autônomo até resultado) |
| `99-gerador-de-agentes.md` | — | Criar agentes |

---

## 5. LER (Loop Engineering Runtime v2.0)

| Item | Valor |
|---|---|---|
| **Diretório** | `EcoSystemUmGrau/ler-runtime/` (junction em `~/.ler/` p/ compatibilidade) |
| **Launcher** | `C:\Users\Playtec-bancada\.local\bin\ler.bat` (aponta p/ novo path) |
| **Camadas** | 13 (Governança → Supervisor) |
| **Agentes LER** | 16 (internos, nao duplicam os 15 do OpenCode) |
| **Providers** | NVIDIA + OpenAI |
| **Knowledge consolidator** | `ler-runtime/agent/knowledge_consolidator.py` (merge Jaccard, export, registro) |
| **Learning engine** | `ler-runtime/agent/learning_engine.py` |
| **CONHECIMENTO.md** | Exportado pelo consolidator, carregado no contexto de todo agente |
| **Versionamento** | Direto no repo EcoSystemUmGrau (sem remote proprio) |
| **Vigilante** | `scripts/vigilante.ps1` — FileSystemWatcher + git sync bidirecional |

---

## 6. Variáveis de Ambiente

| Variável | Valor |
|---|---|
| `NVIDIA_API_KEY` | Configurada |
| `OPENAI_API_KEY` | Configurada |
| `VAULT_PATH` | `C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau` |
| BUN | `~\.bun\bin` no `Path` via `profile.ps1` |

### Conhecimento

| Item | Caminho |
|---|---|
| Base local (entradas por tarefa) | `EcoSystemUmGrau/conhecimento/aprendizados/` |
| Base exportada (contexto global) | `~/.ler/CONHECIMENTO.md` (carregado nas instructions do opencode.jsonc) |
| Agente de aprendizado | `~/.config/opencode/agents/10-aprendizado.md` |
| Vigilante (watcher + git sync multi-projeto) | `EcoSystemUmGrau/scripts/vigilante.ps1` |
| Registro no LER | `register_learning()` no `KnowledgeConsolidator` (automático via vigilante) |
| Knowledge graph | `~/.ler/knowledge/knowledge_graph.json` (67 patterns, 39 decisões, 46 bugs) |
| Git sync (EcoSystemUmGrau) | Automático: pull → commit → push (FileSystemWatcher + timer) |
| Git sync (LER) | Automático: commit local (dentro do EcoSystemUmGrau) |
| Scheduled task | `EcoSystemVigilante` — inicia no logon |
| Profile helpers | `start-vigilante`, `stop-vigilante`, `status-vigilante` |
| Aprendizados registrados | 2 (seed inicial) |

---

## 7. Testes Realizados

- [x] `opencode --version` → `1.18.7`
- [x] `opencode debug info` → plugins funcionais (fallback)
- [x] Agents detectados: 13
- [x] Habilidades no novo caminho: 38 via glob `Habilidades/**/{SKILL,skill}.md` (decisão 2026-07-31)
- [x] VAULT_PATH atualizado para `EcoSystemUmGrau`
- [x] Estrutura de pastas organizada (projetos vs ecossistema)
- [x] Bun 1.3.14 instalado e funcional
- [x] @razroo/opencode-model-fallback v0.3.2 instalado e configurado
- [x] Bun adicionado ao PATH permanentemente via profile.ps1
- [x] Agente 10-aprendizado criado e reconhecido (`opencode debug agent 10-aprendizado`)
- [x] Maestro atualizado com passo 11 (Registrar Aprendizado) no fluxo obrigatório
- [x] Base de conhecimento criada em `EcoSystemUmGrau/conhecimento/`
- [x] `KnowledgeConsolidator` atualizado com `export_to_markdown()` e `register_learning_file()` — ~870 linhas
- [x] `knowledge_bridge.py` removido — função absorvida pelo consolidator
- [x] `conhecimento/INDEX.md` removido — instructions aponta para `~/.ler/CONHECIMENTO.md`
- [x] `10-aprendizado.md` atualizado — chama `register_learning()` direto no consolidator
- [x] `opencode.jsonc` atualizado — instructions aponta para CONHECIMENTO.md do LER
- [x] 2 aprendizados seed registrados no consolidator, CONHECIMENTO.md exportado
- [x] Arquivos pré-existentes mantidos: `knowledge_consolidator.py`, `learning_engine.py`, `seed_knowledge.py`
- [x] **Vigilante.ps1** criado — polling 30s, detecta novos aprendizados, registra no consolidator, git sync 5min
- [x] **Scheduled Task** `EcoSystemVigilante` criada — inicia no logon do Windows
- [x] **Profile helpers** `start-vigilante`, `stop-vigilante`, `status-vigilante`
- [x] **Testado**: vigilante detecta arquivo → consolidator registra → git commit + push — tudo automático
- [x] **Obsidian**: vault em `EcoSystemUmGrau/` já reflete mudanças automaticamente
- [x] **Skill LER** atualizada com protocolo de delegação para agentes OpenCode
- [x] **Agente 11-ler-executor** criado e reconhecido — ponte OpenCode ↔ LER
- [x] **Maestro** atualizado: critério de delegação LER + agende listado
- [x] **Total agents**: 15 (00 a 11 + 99) — Maestro, System Rules, Template, Estrategista, Cetico, Realista, Etica, Futuro, Recursos, Criativo, Revisor, Executor, Aprendizado, LER-Executor, Gerador
- [x] **LER movido p/ repo**: `~/.ler/` → `ler-runtime/` com junction funcional
- [x] **ler.bat atualizado**: aponta p/ `EcoSystemUmGrau/ler-runtime/`
- [x] **Vigilante reescrito**: FileSystemWatcher (sem polling) + git pull antes do push
- [x] **ecosystem.ps1 criado**: `ecosystem sync|scan|status`
- [x] **setup.bat atualizado**: LER path correto, junction, ecosystem function no profile
- [x] **opencode.jsonc template**: `{{USERPROFILE}}/.../ler-runtime/CONHECIMENTO.md`
- [x] **Profile**: ecosystem function adicionada
- [x] **LER remoto deletado**: `github.com/idavidjunior/LER` nao existe mais
