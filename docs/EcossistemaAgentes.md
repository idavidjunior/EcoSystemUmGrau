# Ecossistema Inteligente de Agentes

> _Arquitetura do ecossistema LER + OpenCode + Ponytail + Obsidian_
> _Criado: 2026-07-26_

## Bootstrap em Máquina Nova

Para instalar o ecossistema completo em uma máquina Windows nova (com Git, Node.js e PowerShell):

```powershell
powershell -c "iex (iwr -useb https://raw.githubusercontent.com/idavidjunior/EcoSystemUmGrau/opencode/mighty-meadow/bootstrap.ps1)"
```

Este comando instala OpenCode, configura VAULT_PATH, clona o repositório, skills, MCP, watcher e LER governance.

Após o bootstrap, configure as chaves de API:
```powershell
[Environment]::SetEnvironmentVariable('NVIDIA_API_KEY', 'nvapi-...', 'User')
[Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-...', 'User')
```

## Visão Geral

```
                    ┌─────────────────────────────────────┐
                    │         Ponytail (qualidade)         │
                    │   Age em toda sessão automaticamente │
                    │   Simplifica código, reduz tokens    │
                    └──────────┬──────────────────────────┘
                               │
┌───────────────────────────────────────────────────────────┐
│               LER Orchestrator (13 agentes)               │
│                                                          │
│  GoalAnalyzer → StrategyEngine → RiskManager →          │
│  Planner → Executor → Validator → Recovery →            │
│  LearningEngine → SuccessEvaluator → FinalAuditor       │
│                                                          │
│  + EvidenceCollector + ToolSelector + SelfImprovement   │
│  + Supervisor                                            │
│                                                          │
│  (loop contínuo até DoD satisfeito)                      │
└──────────┬──────────────────────────────────┬───────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────┐           ┌──────────────────────┐
│  OpenCode Subagents  │           │   Obsidian Vault     │
│  (on-demand)         │           │   (MCPVault)         │
│                      │           │                      │
│  01-estrategista     │           │  /LER/Regras         │
│  02-cetico           │◄─────────►│  /LER/Padroes        │
│  03-realista         │           │  /LER/Decisoes       │
│  04-etica            │           │  /LER/Missoes        │
│  05-futuro           │           │  /LER/Melhorias      │
│  06-recursos         │           │  /Tecnico/*          │
│  07-criativo         │           │  /Projetos/*         │
│  08-revisor          │           │                      │
│  99-gerador-agentes  │           │  Memória permanente  │
│  explore             │           │  Sincronizado pós-   │
│  general             │           │  missão              │
└─────────────────────┘           └──────────────────────┘
```

## Fluxo Padrão (default flow)

```
GoalAnalyzer → StrategyEngine → RiskManager →
Planner → Executor → Validator →
LearningEngine → SuccessEvaluator → FinalAuditor
```

1. **GoalAnalyzer**: Recebe objetivo humano → gera `GoalSpecification` (requisitos, DoD, AC)
2. **StrategyEngine**: Gera 3+ estratégias, calcula score (custo/risco/tempo), seleciona melhor
3. **RiskManager**: Avalia riscos (6 categorias), define mitigação
4. **Planner**: Decompõe estratégia em passos executáveis ordenados
5. **Executor**: Executa cada passo via ferramenta apropriada
6. **Validator**: Valida saída de cada passo contra critérios
7. **LearningEngine**: Aprende com erros/acertos da iteração
8. **SuccessEvaluator**: Calcula score ponderado (requisitos 30%, testes 10%, DoD 10%, etc.)
9. **FinalAuditor**: Audita contra DoD + AC, gera relatório

## Fluxo de Falha (on_failure)

```
Validator → Recovery → LearningEngine → StrategyEngine (replan)
```

Se validação falha, Recovery tenta rollback/retry. Se falha persistir, replaneja.

## Fluxo de Revisão (on_audit)

```
FinalAuditor → 08-revisor → 04-etica → vault:reports
```

FinalAuditor pode delegar revisão de código para `08-revisor` e análise ética para `04-etica`.

## Fluxo de Estratégia (on_strategy)

```
StrategyEngine → 07-criativo → 05-futuro → RiskManager → 02-cetico
```

StrategyEngine consulta `07-criativo` para soluções inovadoras e `05-futuro` para tendências. RiskManager depois consulta `02-cetico` para desafiar hipóteses.

## Boundaries (limites de cada agente)

### LER Agents (orquestração)
| Agente | Faz | NÃO faz |
|--------|-----|---------|
| GoalAnalyzer | Analisar objetivos, extrair requisitos | Executar tarefas, validar código |
| StrategyEngine | Gerar estratégias, calcular scoring | Executar passos, auditar |
| RiskManager | Avaliar riscos, definir mitigação | Gerar estratégias, executar |
| Planner | Criar plano de passos | Executar comandos, validar |
| Executor | Executar comandos, tarefas | Planejar, definir estratégia |
| Validator | Validar saídas de cada passo | Executar, recuperar falhas |
| Recovery | Recuperar de falhas, retry | Validar, gerar estratégia |
| LearningEngine | Aprender padrões, consolidar | Executar, auditar |
| SuccessEvaluator | Calcular score de sucesso | Executar, aprender |
| FinalAuditor | Auditar entrega, gerar relatório | Executar, planejar |
| EvidenceCollector | Coletar evidências, logs | Auditar, validar |
| ToolSelector | Roteamento de ferramentas | Executar comandos |
| SelfImprovement | Detectar gargalos, sugerir melhorias | Executar, planejar |
| Supervisor | Monitorar saúde dos módulos | Executar, aprender |

### OpenCode Subagents (revisão especializada)
| Agente | Invocado por | Propósito |
|--------|-------------|-----------|
| 01-estrategista | GoalAnalyzer, StrategyEngine | Direção de alto nível |
| 02-cetico | RiskManager | Desafiar hipóteses |
| 03-realista | RiskManager, Recovery | Viabilidade prática |
| 04-etica | FinalAuditor | Conformidade, privacidade |
| 05-futuro | StrategyEngine | Tendências, escalabilidade |
| 06-recursos | Executor | Mapear recursos |
| 07-criativo | StrategyEngine, SelfImprovement | Soluções inovadoras |
| 08-revisor | Validator, FinalAuditor | Revisão de código |
| 99-gerador-agentes | SelfImprovement, usuário | Criar novos agentes |
| explore | Executor | Explorar codebase |
| general | Executor | Tarefas multi-passo |

### Plugins (sempre ativos)
| Plugin | Ação | Quando |
|--------|------|--------|
| Ponytail | Simplificar código, reduzir tokens, usar stdlib | Toda sessão, automaticamente |

### Recursos (MCP)
| Recurso | Agente que usa | Propósito |
|---------|---------------|-----------|
| Obsidian Vault | Todos LER agents | Memória permanente, conhecimento compartilhado |
| Provider Manager | Executor (via MCP) | Failover de provedores LLM |

## Regras do Ecossistema

1. **Nenhum overlap**: Cada responsabilidade tem UM dono. ConflictDetector bloqueia execução se detectar duplicidade.
2. **LER orquestra**: LER agents coordenam o fluxo. OpenCode agents são consultores - respondem quando chamados, não agem por conta própria.
3. **Vault é a verdade**: Todo conhecimento relevante vai para o Obsidian vault. LearningEngine sincroniza patterns/rules pós-missão.
4. **Ponytail revisa tudo**: Todo código gerado por qualquer agente passa pelo Ponytail (qualidade, simplicidade, token reduction).
5. **Delegação explícita**: LER agents delegam para OpenCode agents explicitamente via `task` tool. OpenCode agents não agem sem delegação.
6. **Auto-melhoria**: SelfImprovement analisa métricas pós-missão e sugere melhorias no ecossistema.
7. **Resiliência**: Supervisor monitora todos os módulos LER. Se um falha, tenta recuperar individualmente sem reiniciar a missão.

## Como os agentes se comunicam

```
LER → OpenCode: via task tool (subprocesso com contexto isolado)
LER → Obsidian: via VaultBridge (MCPVault ou escrita direta)
LER → LER: via Supervisor (registro e monitoramento de módulos)
OpenCode → Obsidian: via MCPVault (ferramentas nativas do MCP)
Ponytail → Todos: revisão de código no fluxo natural da sessão
```

## Instalação e Estado Atual

- **Ponytail**: ✅ Instalado em `~/.config/opencode/plugin/ponytail.mjs`
- **Obsidian MCP**: ✅ Instalado (`@bitbonsai/mcpvault@0.12.4`), vault em `C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau`
- **LER Governance**: ✅ Inicializado, 27 agentes registrados
- **VaultBridge**: ✅ Conectado, sincronização pós-missão ativa

## Próximas Melhorias (SelfImprovement)

1. OpenCode agents serem invocados automaticamente pelo LER Orchestrator (hoje precisam ser chamados manualmente)
2. Dashboards no Obsidian com status das missões
3. Agentes especializados por domínio (Android, MP3Player, etc.)
4. Templates de missão para tarefas repetitivas
