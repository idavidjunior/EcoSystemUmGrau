# Snapshot do Ecossistema — 2026-07-27 (v2 - pós reorganização)

> Estado funcional após reorganização da estrutura de pastas.
> Skills unificadas em EcoSystemUmGrau/skills/. VAULT_PATH redirecionado.

---

## 1. Estrutura de Pastas

### `Desktop/Codigos/` (projetos)
```
Android/
├── Biblia/
├── CellCleaner/
├── Mp3Player/
├── SupermarketCalculator/
Midia/               # (vazio, neutro)
EcoSystemUmGrau/     # (ecossistema — ver abaixo)
```

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
| **Python** | `3.12.7` | `C:\Program Files\Python312\` |
| **pip** | `24.2` | — |
| **Git** | `2.55.0.windows.2` | `C:\Program Files\Git\cmd` |
| **OS** | Windows (PowerShell 5.1) | — |

---

## 3. Config OpenCode (`~/.config/opencode/opencode.jsonc`)

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "C:/Users/Playtec-bancada/Desktop/Codigos/EcoSystemUmGrau/skills/*/SKILL.md",
    "C:/Users/Playtec-bancada/Desktop/Codigos/EcoSystemUmGrau/skills/**/SKILL.md"
  ]
}
```

**Plugin ativo:** `ponytail.mjs` em `~/.config/opencode/plugin/ponytail.mjs`
- Dependência: `@opencode-ai/plugin@1.17.13`
- Estado: `off` (sem `.ponytail-active`)

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

---

## 6. Variáveis de Ambiente

| Variável | Valor |
|---|---|
| `NVIDIA_API_KEY` | Configurada |
| `OPENAI_API_KEY` | Configurada |
| `VAULT_PATH` | `C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau` |

---

## 7. Testes Realizados

- [x] `opencode --version` → `1.18.7`
- [x] `opencode debug config` → config carregado sem erros
- [x] Agents detectados: 13
- [x] Skills no novo caminho: 34 skills via glob `skills/**/SKILL.md`
- [x] VAULT_PATH atualizado para `EcoSystemUmGrau`
- [x] Estrutura de pastas organizada (projetos vs ecossistema)
