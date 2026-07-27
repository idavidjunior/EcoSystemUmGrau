---
name: ler
description: Loop Engineering Runtime (LER) v2.0 - Plataforma de engenharia autonoma orientada por missao com 13 camadas. Instalado globalmente via `ler` command. Ativa automaticamente quando o usuario pede para automatizar, executar, construir, criar, corrigir, testar, ou gerenciar qualquer projeto de engenharia de software. Trigger keywords: "LER", "Loop Engineering", "ler ", "ler --", "missao", "run.py", "engineer loop", "runtime mission", "autonomous engineering", "GoalSpecification", "DoD", "autonomo", "executar missao", "engenharia autonoma".
---

# Loop Engineering Runtime (LER) v2.0

## Instalacao Global

LER esta instalado globalmente via:

```powershell
ler "sua missao aqui"           # Executa missao de qualquer diretorio
ler --status                     # Status do sistema
ler --version                    # Versao
ler --resume                     # Retomar de checkpoint
ler --inspect                    # Arquitetura + governanca
ler --reset                      # Resetar estado
ler --report                     # Relatorio final
ler --audit                      # Escanear projeto atual (Python/flake8, Go vet, Kotlin/ktlint)
ler --audit "caminho"            # Escanear diretorio especifico
ler --fix                        # Escanear + aplicar correcoes auto-aplicaveis
ler --learn                      # Consolidar conhecimento (skills + memorias + git log)
```

**Localizacao:** `C:\Users\Playtec-bancada\.ler\` (independente do workspace)
**Launcher:** `C:\Users\Playtec-bancada\.local\bin\ler.bat` (ja no PATH)

## Princípios

- **Missão não termina até objetivo comprovadamente atingido + validação + auditoria + artefatos + persistência + confirmação do usuário**
- **Se usuário reportar falha no sucesso, LER aprende e reinicia a missão automaticamente**
- Zero dependências externas (stdlib only)
- Persistência sobrevive a queda de energia, servidor, restart, timeout, troca de modelo
- Toda decisão deve ter evidência (testes, logs, compilação, execução)
- LER nunca é um chatbot — é um executor de missões

## Localização

O código-fonte LER deve estar em um diretório `LoopEngineeringAgent/` dentro do workspace atual. Se não existir, está ausente. Execute dentro desse diretório.

## CLI

```powershell
ler "Sua missao aqui"           # Executar missao nova
ler --status                     # Status do sistema
ler --resume                     # Retomar de checkpoint
ler --inspect                    # Arquitetura + governanca
ler --version                    # Versao
ler --reset                      # Resetar estado
ler --report                     # Relatorio final
ler --audit                      # Escanear projeto atual (Python/flake8, Go vet, Kotlin/ktlint)
ler --audit "caminho"            # Escanear diretorio especifico
ler --fix                        # Escanear + aplicar correcoes auto-aplicaveis
ler --learn                      # Consolidar conhecimento (skills + memorias + git log)
```

## 13 Camadas (v2.0)

| # | Camada | Módulo | Função |
|---|--------|--------|--------|
| 1 | Governança | `governance/` | Registro de agentes, mapa de responsabilidades, detecção de conflitos |
| 2 | Arquitetura | `architecture/` | Validação estrutural, regras de compatibilidade |
| 3 | Planejamento | `agent/planner`, `agent/strategy_engine` | Decomposição de objetivo, geração de estratégia, criação de plano |
| 4 | Execução | `agent/executor`, `runtime/mission` | Execução de passos, ciclo de vida da missão |
| 5 | Validação | `agent/validator` | Verificação de saída, gates de qualidade |
| 6 | Recuperação | `agent/recovery` | Tratamento de erro, rollback, retry |
| 7 | Persistência | `runtime/persistence` | Checkpoints, estado da missão, sobrevivência a restart |
| 8 | Versionamento | `git` | Commits, histórico, rastreamento |
| 9 | Auditoria | `agent/final_auditor` | Checklist final, relatório expandido, DoD, AC |
| 10 | Evidências | `agent/evidence_collector` | Coleta de logs, hashes, artefatos, testes; gera evidence.json + evidence.md |
| 11 | Ferramentas | `agent/tool_selector` | Roteamento automático (OpenCode, NVIDIA, Shell, Git, Python), feedback loop |
| 12 | Auto-Melhoria | `agent/self_improvement` | Detecção de gargalos, desperdício, retrabalho, falhas recorrentes |
| 13 | Supervisor | `agent/supervisor` | Monitoramento contínuo de módulos, recuperação automática individual |

## Máquina de Estados

```
INIT -> ANALYZING_GOAL -> CREATING_STRATEGY -> PLANNING ->
EXECUTING -> VALIDATING -> (LEARNING -> REPLANNING)* ->
SUCCESS_EVALUATING -> FINAL_AUDITING -> SUCCESS_VERIFIED ->
COMPLETED -> USER_FEEDBACK -> (SUCCESS | RESTART)
```

Se usuário rejeitar: `RESTART` volta para `INIT` com aprendizado registrado.

## Modelo de Segurança

- `SecurityEnforcer.check_file_before_commit()` — detecta API keys, senhas, tokens
- `SecurityEnforcer.verify_no_destructive_op()` — bloqueia rm -rf, format, del /f
- `SecurityEnforcer.backup_before_modify()` — backup timestamped antes de modificar

## Modelo de Governança

- `AgentGovernance` gerencia `responsibility_map.json` com agentes e responsabilidades
- `initialize()` cria mapa default se vazio, detecta conflitos
- `get_all_agents()` retorna agentes registrados
- `ConflictDetector` verifica sobreposição de ownership, papéis duplicados, cobertura faltante

## Goal Analyzer v2.0

Produz `GoalSpecification` com objective, requirements, constraints, dependencies, assumptions, acceptance_criteria, definition_of_done, risks. Todo goal passa pelo GoalAnalyzer antes do Planner.

## Strategy Engine v2.0

Gera mínimo 3 estratégias (Directa A, Alternativa B, Conservadora C, Incremental D, Paralela E). Cada uma tem cost, risk, estimated_time, complexity, success_probability, score. Ranking seleciona a melhor. Estratégias falhas nunca repetidas sem alterações.

## Risk Manager v2.0

6 categorias: environment, technical, external, dependency, API, permission, strategy. Cada risco tem mitigation_plan + contingency. Mitigação executa antes de prosseguir.

## Learning Engine v2.0

Memória permanente: learned_rules.json, successful_patterns.json, failed_patterns.json, tool_statistics.json, architecture_patterns.json, knowledge/mission_experience.json. Erros viram regras reutilizáveis. Ferramentas têm tracking de duração/sucesso/custo.

## Success Evaluator v2.0

Score ponderado: Requisitos 30%, Funcionamento 30%, Testes 10%, DoD 10%, Evidências 10%, Auditoria 10%. Threshold 95%. Score < threshold SEMPRE vai para REPLANNING (nunca pula direto para SUCCESS_VERIFIED).

## Evidence Collector

Coleta automática: logs, arquivos (SHA256), testes, artefatos, decisões, timing. Gera `reports/evidence.json` e `reports/evidence.md`.

## Tool Selector

Roteamento automático: programação → OpenCode, LLM → NVIDIA, terminal → Shell, git → Git, test → Python. Tracking de sucesso/falha/tempo/custo. Fallback automático se taxa de sucesso < 50%.

## Self Improvement

Pós-missão: detecta gargalos (tempo/iteração alto), desperdício (passos não concluídos), retrabalho (falhas/completos), falhas recorrentes (3+ sem correção). Gera sugestões de melhoria.

## Knowledge Consolidator (Auto-Learning)

Mecanismo que extrai e persiste conhecimento automaticamente entre sessoes:

- **`ler --learn`** — consolida manualmente: extrai padroes de todas as SKILL.md, memorias LER, e git log
- **Auto-learn pos-missao** — toda missao que completa chama `KnowledgeConsolidator.auto_learn()` automaticamente
- **Auto-learn pos-sessao (IA)** — AO FINAL DE CADA SESSAO, a IA DEVE chamar `consolidate_from_session()` com os aprendizados da sessao. Isto e MANDATORIO, nao opcional.
- **Grafo de conhecimento** salvo em `knowledge/knowledge_graph.json` com secoes: patterns, decisions, bug_fixes, cognitive_patterns, heuristics, frameworks, projects, skill_references, mission_learnings
- **Skill auto-update** — `update_skill_file()` insere seccao `## Auto-Learned` no SKILL.md relevante com novos padroes
- **Merge inteligente** — similaridade Jaccard > 0.55 funde entradas similares automaticamente, combinando descricoes e mantendo historico de merges

### Estrutura do knowledge_graph.json (v2)
```json
{
  "version": 2,
  "projects": { "android-pure-sdk": {}, "mp3player": {}, "ler": {} },
  "patterns": [ { "source": "...", "title": "...", "action": "..." } ],
  "decisions": [ { "decision": "...", "rationale": "...", "source": "..." } ],
  "bug_fixes": [ { "issue": "...", "root_cause": "...", "fix": "...", "source": "..." } ],
  "cognitive_patterns": [ { "title": "...", "domain": "debugging", "body": "..." } ],
  "heuristics": [ { "title": "...", "description": "...", "domain": "..." } ],
  "frameworks": [ { "name": "...", "description": "...", "body": "..." } ],
  "mission_learnings": [ { "status": "completed", "steps_completed": 10, ... } ],
  "skill_references": [ { "skill": "android-pure-sdk", "hash": "md5..." } ]
}
```

### Protocolo Obrigatorio: Fim de Sessao

Toda sessao de IA (OpenCode, Claude, etc.) DEVE executar este protocolo antes de encerrar:

```python
from agent.knowledge_consolidator import KnowledgeConsolidator

kc = KnowledgeConsolidator(base_dir)
learnings = {
    "patterns": [
        # Padroes tecnicos descobertos nesta sessao
    ],
    "decisions": [
        {"decision": "Usei X em vez de Y", "rationale": "Porque Z", "source": "sessao_analise"},
    ],
    "bug_fixes": [
        {"issue": "Bug de encoding", "root_cause": "ASCII vs UTF-8", "fix": "...", "source": "sessao_correcao"},
    ],
    "cognitive_patterns": [
        # Estrategias de raciocinio, heuristicas validades, frameworks aplicados
    ],
    "heuristics": [
        {"title": "Regra que aprendi", "description": "Sempre fazer X quando Y", "domain": "debugging"},
    ],
    "session_summary": "Resumo do que foi feito, descoberto, e aprendido.",
    "tags": ["projeto_x", "android", "debugging"],
    "files_modified": ["src/MainActivity.java"],
}
kc.consolidate_from_session(learnings)
```

**Toda sessao que nao consolidar perde conhecimento.** Nao importa se foi uma correcao pequena ou uma analise grande — se foi util para voce, sera util no futuro.

### Seed Inicial
`tools/seed_knowledge.py` contem seed com:
- 8 bug fixes tecnicos
- 12 decisoes arquiteturais
- 8 padroes tecnicos
- 9 padroes cognitivos (debugging, system_design, algorithm, architecture, testing)
- 12 heuristicas (debugging, coding, persistence, architecture)
- 7 frameworks (PDCA, 5 Whys, MECE, FIRST, Arvore de Decisao, Persistencia, Auto-Learning)

Executado via `ler --learn`.

### Fontes de Extracao
- **Skills:** SKILL.md de cada projeto (padroes por cabecalhos ##/###, decisoes por regex, bug fixes por tabelas Known Issues)
- **LER Memory:** successful_patterns.json, failed_patterns.json, learned_rules.json, tool_statistics.json
- **Git Log:** commits recentes via `git log --oneline -50`
- **Pos-missao:** mission_report do LER (status, iteracoes, steps, learning_stats)
- **Pos-sessao:** `consolidate_from_session()` chamado pela IA ao final de cada sessao
- **Texto livre:** `extract_from_text()` extrai heuristicas e padroes cognitivos de blocos de texto

## Supervisor

Monitora todos os módulos: planner, executor, validator, recovery, learning, strategy, risk, auditor. Se módulo falha, tenta recuperar individualmente. Nunca reinicia missão inteira. Relatório de saúde.

## Goal-Oriented Loop

```
while DoD not satisfied:
  Analyze Goal → Generate Strategies → Assess Risks → Plan → Execute (ToolSelector)
  → Validate → Collect Evidence → Learn → Score
  if score >= threshold: Audit → Verify → Complete
  else: Autonomous Replan (analyze cause → consult memory → new strategy → execute)

After Complete → Ask User Confirmation:
  if user confirms success → Finalize (learn what worked)
  if user rejects → Log failure pattern → Restart from INIT
```

## User Feedback Loop

Após o score passar e a auditoria aprovar, o LER **pergunta ao usuário** antes de encerrar:

```python
user_ok = self._ask_user_feedback()  # input() no terminal
if not user_ok:
    self._learn_from_failure(...)     # registra padrão em failed_patterns.json
    return self._restart_mission()    # limpa estado, reaprende, recomeça
```

- Se usuário confirma → missão finaliza como sucesso, padrões de sucesso registrados
- Se usuário rejeita → padrão de falha registrado, missão reinicia automaticamente
- O feedback vira `failed_patterns.json` para aprendizado futuro

## Stagnation Detection

LER não usa `max_iterations` como critério de término. Usa detecção de estagnação:

- Conta passos completados por iteração
- Se 0 progresso por 30 iterações consecutivas → para com `stagnation` (não `completed`)
- Score < threshold SEMPRE replaneja, independente de ter steps falhos ou não
- Ciclo de estados repetido 4× → força replan automático

## Critério Absoluto

Missão só termina quando: ✓ DoD satisfeita, ✓ AC satisfeitos, ✓ Score >= 95%, ✓ Auditoria aprovada, ✓ Evidências coletadas, ✓ Nenhum erro crítico restante, ✓ Usuário confirma sucesso.

## Testes

```powershell
python tests\test_basic.py      # 16 testes (v1.1)
python tests\test_ler_v12.py    # 13 testes (v1.2: segurança, persistência, governança, arquitetura, missão)
python tests\test_ler_v20.py    # 31 testes (v2.0: GoalSpec, StrategyRanking, Risk6Cat, LearningTools, Evidence, ToolSelect, SelfImprove, Supervisor, DoD)
```

## Integração com OpenCode

O arquivo `integrations/opencode/opencode_bridge.py` contém `OpenCodeBridge` que permite:
- `delegate_goal(goal_text)` — delega missão para LER executar
- `get_status()` — consulta status atual
- `generate_report()` — gera relatório final

### Restrição Crítica: Formato do opencode.jsonc

O OpenCode **NÃO** carrega se o `~/.config/opencode/opencode.jsonc` contiver a chave `"plugins"` ou qualquer campo extra não suportado. O formato **UNICO** que funciona sem erros é:

```json
{
    "$schema": "https://opencode.ai/config.json",
    "model": "opencode/deepseek-v4-flash-free",
    "shell": "powershell",
    "instructions": [
        "C:\\Users\\Playtec-bancada\\.claude\\skills\\android-pure-sdk\\SKILL.md",
        "C:\\Users\\Playtec-bancada\\.claude\\skills\\mp3player-metadata-rescue\\SKILL.md",
        "C:\\Users\\Playtec-bancada\\.claude\\skills\\ler\\SKILL.md"
    ],
    "disabled_providers": [],
    "provider": {
        "nvidia": {
            "name": "NVIDIA",
            "npm": "@ai-sdk/openai-compatible",
            "env": ["NVIDIA_API_KEY"],
            "options": { "baseURL": "https://integrate.api.nvidia.com/v1" },
            "models": {
                "deepseek-ai/deepseek-v4-pro": { "name": "DeepSeek V4 Pro" },
                "nvidia/llama-3.1-nemotron-70b-instruct": { "name": "Llama 3.1 Nemotron 70B" },
                "meta/llama-3.1-405b-instruct": { "name": "Llama 3.1 405B" },
                "mistralai/mistral-large-2-instruct": { "name": "Mistral Large 2" }
            }
        },
        "openai": {
            "name": "OpenAI",
            "env": ["OPENAI_API_KEY"],
            "models": {
                "gpt-4o": { "name": "GPT-4o" },
                "gpt-4o-mini": { "name": "GPT-4o Mini" },
                "gpt-4-turbo": { "name": "GPT-4 Turbo" }
            }
        }
    },
    "mcp": {
        "provider-manager": {
            "type": "local",
            "command": ["python", "{{REPO_DIR}}\\LoopEngineeringAgent\\integrations\\opencode\\provider_mcp_server.py"],
            "enabled": true,
            "timeout": 30000
        },
        "mcpvault": {
            "type": "local",
            "command": ["cmd", "/c", "npx @bitbonsai/mcpvault \"{{VAULT_PATH}}\""],
            "enabled": true
        }
    }
}
```

**Regras:**
- NUNCA adicionar chave `"plugins"` — causa falha no carregamento
- NUNCA adicionar campos extras fora de `$schema`, `model`, `shell`, `instructions`, `disabled_providers`, `provider`, `mcp`
- O template oficial está em `opencode.template.json` no repo raiz
- O `setup.ps1` gera o config resolvendo placeholders `{{SKILLS_DIR}}`, `{{REPO_DIR}}`, `{{VAULT_PATH}}`
- Plugins como Ponytail são instalados em `~/.config/opencode/plugin/` mas NÃO referenciados no JSON

### Bootstrap em Maquina Nova (um comando)

Em uma máquina Windows nova (sem nada instalado além de Git, Node.js, PowerShell):

```powershell
powershell -c "iex (iwr -useb https://raw.githubusercontent.com/idavidjunior/EcoSystemUmGrau/opencode/mighty-meadow/bootstrap.ps1)"
```

O `bootstrap.ps1`:
1. Verifica pré-requisitos (Git, Node.js/npm, PowerShell 5.1+)
2. Instala OpenCode via `npm install -g opencode-ai`
3. Cria variável de ambiente `VAULT_PATH`
4. Clona o repositório `EcoSystemUmGrau`
5. Executa `setup.ps1` completo (skills, MCP, watcher, LER governance)
6. Exibe instruções finais

Após o bootstrap, o usuário precisa apenas configurar as chaves de API:
```powershell
[Environment]::SetEnvironmentVariable('NVIDIA_API_KEY', 'nvapi-...', 'User')
[Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-...', 'User')
```

E já pode executar `opencode` para começar.

## Persistência

- Checkpoints salvos antes de cada iteração
- Estado da missão persiste em `checkpoints/`
- `mission_survives_restart()` verifica se missão pode ser restaurada
- Dados sobrevivem a: queda de energia, restart de servidor, troca de modelo, timeout

## Responsabilidades dos Agentes

| Agente | Responsabilidade |
|--------|-----------------|
| Orchestrator | Loop principal, transições de estado |
| GoalAnalyzer | Análise do objetivo, extração de requisitos |
| StrategyEngine | Geração de estratégias, seleção da melhor |
| RiskManager | Avaliação e mitigação de riscos |
| Planner | Criação do plano, decomposição em passos |
| Executor | Execução de cada passo |
| Validator | Validação de saída de cada passo |
| Recovery | Recuperação de erro, retry, rollback |
| LearningEngine | Aprendizado de padrões |
| SuccessEvaluator | Avaliação global de sucesso |
| FinalAuditor | Auditoria final, geração de relatório |
