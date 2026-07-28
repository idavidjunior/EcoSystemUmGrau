# Snapshot do Ecossistema — 2026-07-27 (v7 - Setup Plug & Play)

> Estado funcional com sistema automático de captura de conhecimento em 3 camadas.
> Skills unificadas em EcoSystemUmGrau/skills/. VAULT_PATH redirecionado.
>
> ## FONTE ÚNICA: O REPOSITÓRIO
> Toda config, agente e skill vive no repo `EcoSystemUmGrau/config/` e `skills/`.
> Nada duplicado. setup.bat gera os arquivos no destino a partir dos templates.
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
> ## VIGILANTE — AUTO-APRENDIZADO + GIT SYNC
> Sincroniza automaticamente o EcoSystemUmGrau (git push cada 5min).
> LER nao tem remote proprio — o conhecimento viaja no EcoSystemUmGrau.

### Arquitetura final do conhecimento automático

```
Maestro (passo 11 obrigatório)
  → 10-Aprendizado escreve conhecimento/aprendizados/YYYY-MM-DD-N.md
      → Vigilante.ps1 (processo Windows oculto, polling 30s)
          → Detecta novo .md por hash
          → Chama KnowledgeConsolidator.register_learning()
              → Atualiza knowledge_graph.json (merge Jaccard)
              → Exporta CONHECIMENTO.md
           → A cada 5 min: git add, commit, push em EcoSystemUmGrau + LER (~/.ler/)
       → CONHECIMENTO.md carregado no contexto de todo agente via opencode.jsonc
```

### Gatilhos de inicialização
- **Logon do Windows**: Scheduled Task `EcoSystemVigilante`
- **PowerShell profile**: `start-vigilante` (auto-start ao abrir terminal)
- **Manual**: `start-vigilante`, `stop-vigilante`, `status-vigilante`

---

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

### `Desktop/Codigos/EcoSystemUmGrau/` (ecossistema)
```
.obsidian/           # Vault Obsidian (VAULT_PATH atualizado)
skills/              # 34 skills unificadas
├── graphify/
├── ler/
├── agentic-search/
├── api-design/
├── authz-authn-matrix/
├── autonomous-loops/
├── backend-patterns/
├── cache-strategy-selector/
├── concurrent-computation-patterns/
├── cost-aware-llm-pipeline/
├── data-privacy-by-design/
├── database-migrations/
├── deployment-patterns/
├── developer-experience-dx/
├── docker-patterns/
├── e2e-testing/
├── edge-compute-patterns/
├── error-message-design/
├── frontend-patterns/
├── golang-patterns/
├── local-first-architecture/
├── migration-playbooks/
├── mobile-specific-patterns/
├── mp3player-metadata-rescue/
├── multi-modal-ai/
├── observability-stack/
├── python-patterns/
├── resilience-engineering/
├── search-first/
├── security-review/
├── semantic-release-automation/
├── state-machine-patterns/
└── tdd-workflow/
ler/                 # Documentação LER
├── EcossistemaAgentes.md
ai-agents/           # Claude Code extra agents
├── claude-code-extra-agents/
scripts/             # Scripts do ecossistema (vazio)
ferramentas/         # Ferramentas
├── FLUTTER/
documentos/          # Documentos diversos
agents/              # Referência dos agents OpenCode
plugins/             # Referência dos plugins
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
  "plugin": [
    "file:///C:/Users/Playtec-bancada/Desktop/Codigos/EcoSystemUmGrau/plugins/ponytail/.opencode/plugins/ponytail.mjs",
    "@razroo/opencode-model-fallback"
  ],
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
    "C:/Users/Playtec-bancada/Desktop/Codigos/EcoSystemUmGrau/skills/*/SKILL.md",
    "C:/Users/Playtec-bancada/Desktop/Codigos/EcoSystemUmGrau/skills/**/SKILL.md",
    "C:/Users/Playtec-bancada/Desktop/Codigos/EcoSystemUmGrau/conhecimento/INDEX.md"
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
|---|---|
| **Diretório** | `C:\Users\Playtec-bancada\.ler\` |
| **Launcher** | `C:\Users\Playtec-bancada\.local\bin\ler.bat` |
| **Camadas** | 13 (Governança → Supervisor) |
| **Agentes LER** | 16 |
| **Providers** | NVIDIA + OpenAI |
| **Knowledge consolidator** | `agent/knowledge_consolidator.py` (~870 linhas, merge Jaccard, export markdown, registro de aprendizado) |
| **Learning engine** | `agent/learning_engine.py` (aprendizado por erro/sucesso, tool stats) |
| **Seed knowledge** | `tools/seed_knowledge.py` (595 linhas, seed inicial de padrões) |
| **CONHECIMENTO.md** | Exportado pelo próprio `KnowledgeConsolidator.export_to_markdown()` |
| **knowledge_bridge.py** | Removido — função absorvida pelo consolidator |
| **Remote** | `github.com/idavidjunior/LER.git` — configurado e com push inicial |
| **Vigilante** | `scripts/vigilante.ps1` — processo Windows oculto, polling 30s, git sync 5min (EcoSystemUmGrau + LER) |

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
| Vigilante (watcher + git sync) | `EcoSystemUmGrau/scripts/vigilante.ps1` |
| Registro no LER | `register_learning()` no `KnowledgeConsolidator` (automático via vigilante) |
| Knowledge graph | `~/.ler/knowledge/knowledge_graph.json` (67 patterns, 39 decisões, 46 bugs) |
| Git sync (EcoSystemUmGrau) | Automático a cada 5 min via vigilante → `idavidjunior/EcoSystemUmGrau` |
| Git sync (LER) | Automático a cada 5 min via vigilante → `idavidjunior/LER` |
| Scheduled task | `EcoSystemVigilante` — inicia no logon |
| Profile helpers | `start-vigilante`, `stop-vigilante`, `status-vigilante` |
| Aprendizados registrados | 2 (seed inicial) |

---

## 7. Testes Realizados

- [x] `opencode --version` → `1.18.7`
- [x] `opencode debug info` → ambos plugins listados (ponytail + fallback)
- [x] Agents detectados: 13
- [x] Skills no novo caminho: 34 skills via glob `skills/**/SKILL.md`
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
