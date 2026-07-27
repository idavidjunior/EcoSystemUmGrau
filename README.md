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
│  (GoalAnalyzer,         │       ┌─────────────────────────┐
│   StrategyEngine,       │       │  EcoSystemUmGrau/        │
│   Planner, Executor,    │       │  ├── .obsidian (vault)   │
│   Validator, Recovery,  │       │  ├── skills/ (34)        │
│   LearningEngine, ...)  │       │  ├── ecosystem/docs      │
│                         │       │  ├── LoopEngineeringAgent│
│  knowledge_graph.json   │       │  └── vault/ (notas)      │
│  memory/                │       └──────────────────────────`
└─────────────────────────┘
```

## Componentes

### LER — Loop Engineering Runtime
Plataforma de engenharia autônoma orientada por missão com 13 camadas, máquina de estados Goal-Oriented Loop, persistência por checkpoint e aprendizado contínuo via knowledge graph.

- **Entry point:** `python run.py "sua missão aqui"`
- **16 agentes:** Orchestrator, GoalAnalyzer, StrategyEngine, RiskManager, Planner, Executor, Validator, Recovery, LearningEngine, SuccessEvaluator, FinalAuditor, EvidenceCollector, ToolSelector, SelfImprovement, Supervisor
- **Provider Manager:** Roteamento entre NVIDIA, OpenAI, OpenRouter, Anthropic, Gemini com failover automático

### OpenCode Integration
Skills unificadas em `skills/`, config gerado via template, plugin Ponytail. Agents em `~/.config/opencode/agents/`.

### Obsidian Vault
`.obsidian/` na raiz do repositório. O vault inteiro é versionado. Watcher automático via Scheduled Task.

## Quick Start — Máquina Nova

```powershell
powershell -c "iex (iwr -useb https://raw.githubusercontent.com/idavidjunior/EcoSystemUmGrau/opencode/mighty-meadow/bootstrap.ps1)"
```

O bootstrap verifica pré-requisitos (Git, Node.js), instala OpenCode, configura chaves de API, clona para `Desktop/Codigos/EcoSystemUmGrau/` e executa `setup.ps1`.

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
EcoSystemUmGrau/
├── .obsidian/                 # Vault Obsidian (raiz do vault)
├── LoopEngineeringAgent/      # LER v2.0 core + agentes + provider
├── skills/                    # 34 skills unificadas
├── vault/                     # Notas do vault (LER, AI-Agents)
├── memory/                    # Memória de runtime LER
├── ecosystem/                 # Documentação e config do ecossistema
│   ├── ler/                   #  EcossistemaAgentes.md
│   ├── ai-agents/             #  Claude Code extra agents
│   ├── agents/                #  Referência dos agents OpenCode
│   ├── plugins/               #  Referência dos plugins
│   ├── scripts/               #  Scripts auxiliares
│   ├── ferramentas/           #  Ferramentas
│   └── documentos/            #  Documentos diversos
├── bootstrap.ps1              # Bootstrap máquina nova (1 comando)
├── setup.ps1                  # Setup completo do ecossistema
├── opencode.template.json     # Template do opencode.jsonc
├── watch-vault.ps1            # Watcher automático do vault
├── sync-vault.ps1             # Sincroniza vault para o repo
├── sync-pendrive.ps1          # Backup para pendrive
├── install-watcher.ps1        # Instala watcher como Scheduled Task
├── uninstall-watcher.ps1      # Desinstala watcher
├── notify-vault-sync.ps1      # Notificação visual de sync
├── estado_atual.md            # Snapshot do estado do ecossistema
├── .gitignore
└── README.md
```

## Repositório

**Branch:** `opencode/mighty-meadow`
**URL:** `https://github.com/idavidjunior/EcoSystemUmGrau`
