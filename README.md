# EcoSystemUmGrau

Ecossistema de engenharia autônoma integrando **LER** (Loop Engineering Runtime), **OpenCode** e **Obsidian Vault**.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                     OpenCode CLI                      │
│  (Interface principal de engenharia assistida por IA) │
└──────────────┬──────────────────────────┬────────────┘
               │ MCP                      │ Provider Manager
┌──────────────▼──────────┐  ┌────────────▼────────────┐
│      LER v2.0           │  │  Providers de IA         │
│  Loop Engineering       │  │  ├── NVIDIA (DeepSeek V4)│
│  Runtime                │  │  ├── OpenAI (GPT-4o)     │
│                         │  │  └── OpenRouter/Anthropic│
│  Orchestrator ─► 16     │  └─────────────────────────┘
│  agentes em pipeline    │
│  (GoalAnalyzer,         │
│   StrategyEngine,       │
│   Planner, Executor,    │
│   Validator, Recovery,  │  ┌─────────────────────────┐
│   LearningEngine, ...)  │  │  Obsidian Vault          │
│                         │  │  (Notas LER + AI-Agents) │
│  knowledge_graph.json   │  └──────────┬──────────────┘
│  memory/                │             │ sync automático
└─────────────────────────┘             │ (FileSystemWatcher)
                               ┌─────────▼────────────────┐
                               │  Watch-Vault (Scheduled   │
                               │  Task) ─► sync-vault.ps1 │
                               │  ─► git commit + push    │
                               └─────────────────────────┘
```

## Componentes

### LER — Loop Engineering Runtime
Plataforma de engenharia autônoma orientada por missão com 13 camadas, máquina de estados Goal-Oriented Loop, persistência por checkpoint e aprendizado contínuo via knowledge graph.

- **Entry point:** `python run.py "sua missão aqui"`
- **16 agentes:** Orchestrator, GoalAnalyzer, StrategyEngine, RiskManager, Planner, Executor, Validator, Recovery, LearningEngine, SuccessEvaluator, FinalAuditor, EvidenceCollector, ToolSelector, SelfImprovement, Supervisor
- **Provider Manager:** Roteamento entre NVIDIA, OpenAI, OpenRouter, Anthropic, Gemini com failover automático

### OpenCode Integration
MCP server (`provider_mcp_server.py`) para gerenciamento de providers + `opencode.template.json` para configuração restrita (formato sem chave `plugins`).

### Obsidian Vault Sync
Watcher automático via Scheduled Task que monitora alterações no vault, sincroniza com o repositório via `robocopy /MIR`, e faz git commit+push com notificação visual.

## Quick Start — Máquina Nova

```powershell
powershell -c "iex (iwr -useb https://raw.githubusercontent.com/idavidjunior/EcoSystemUmGrau/opencode/mighty-meadow/bootstrap.ps1)"
```

O bootstrap verifica pré-requisitos (Git, Node.js), instala OpenCode, configura chaves de API com validação, clona o repositório e executa `setup.ps1`.

## Uso

### LER
```powershell
ler "sua missao aqui"    # Executar missão
ler --status              # Status do sistema
ler --resume              # Retomar de checkpoint
ler --learn               # Consolidar conhecimento
```

### Setup
```powershell
.\setup.ps1               # Configurar/reconfigurar ecossistema
```

## Estrutura

```
mighty-meadow/
├── LoopEngineeringAgent/     # LER v2.0 core + agentes + provider manager
├── vault/                    # Vault Obsidian versionado
│   ├── LER/                  # Notas sobre o LER
│   └── AI-Agents/            # Notas sobre agentes de IA
├── memory/                   # Memória de runtime
├── bootstrap.ps1             # Bootstrap máquina nova (1 comando)
├── setup.ps1                 # Setup completo do ecossistema
├── opencode.template.json    # Template do opencode.jsonc
├── watch-vault.ps1           # Watcher automático do vault
├── sync-vault.ps1            # Sincroniza vault para o repo
├── sync-pendrive.ps1         # Backup para pendrive
├── install-watcher.ps1       # Instala watcher como Scheduled Task
├── uninstall-watcher.ps1     # Desinstala watcher
└── notify-vault-sync.ps1     # Notificação visual de sync
```

## Repositório

**Branch:** `opencode/mighty-meadow`
**URL:** `https://github.com/idavidjunior/EcoSystemUmGrau`
