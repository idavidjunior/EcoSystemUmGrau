# Loop Engineering Runtime (LER) v1.2

## Architecture

A LER is a mission-oriented autonomous engineering platform. It receives a goal and drives it to completion through 9 layers of coordinated execution.

### Layer Stack

| Layer | Module | Responsibility |
|-------|--------|---------------|
| 1 - Governance | `governance/` | Agent registration, role assignment, conflict detection |
| 2 - Architecture | `architecture/` | Structural validation, compatibility, rules enforcement |
| 3 - Planning | `agent/planner`, `agent/strategy_engine` | Goal decomposition, strategy generation, plan creation |
| 4 - Execution | `agent/executor`, `runtime/mission` | Step execution, mission lifecycle, iteration loop |
| 5 - Validation | `agent/validator` | Output verification, quality gates, criteria checking |
| 6 - Recovery | `agent/recovery` | Error handling, rollback, retry, state restoration |
| 7 - Persistence | `runtime/persistence` | Checkpoints, mission state, survival across restarts |
| 8 - Versioning | `git` | Code commits, history, change tracking |
| 9 - Audit | `agent/final_auditor` | Final checklist, report generation, evidence collection |

### Module Map

```
LoopEngineeringAgent/
  run.py                    -- Entry point (CLI)
  loop.py                   -- v1.0 legacy entry point
  config/
    config.json             -- System configuration (v1.2)
    agent_rules.json        -- Agent behavior rules
    routes.json             -- OmniRoute provider routing
    .env / .env.template    -- Environment variables
  runtime/                  -- v1.2: Mission runtime
    kernel.py               -- System boot: persistence -> security -> governance -> architecture -> session -> mission
    mission.py              -- MissionRuntime: goal -> orchestration -> completion/failure
    persistence.py          -- Checkpoint save/load, mission state persistence, survival detection
    security.py             -- SecurityEnforcer: sensitive data scan, destructive op detection, backup
  governance/               -- v1.2: Agent Governance System
    agent_governance.py     -- AgentGovernance: register agents, responsibility map, initialize
    conflict_detector.py    -- ConflictDetector: ownership overlaps, role conflicts
    responsibility_map.json -- Agent responsibility definitions (10 agents, 0 conflicts)
  architecture/             -- v1.2: Architecture Review Engine
    review_engine.py        -- ArchitectureReviewEngine: validate, report, rules
    validators.py           -- Validators: module existence, layer order, compatibility checks
  agent/                    -- Core agent machinery (v1.0/v1.1)
    orchestrator.py         -- Orchestrator: main loop (INIT -> ANALYZE -> STRATEGY -> PLAN -> EXECUTE -> VALIDATE -> LEARN -> SUCCESS_EVALUATE -> AUDIT)
    planner.py              -- Plan creation from goal analysis
    executor.py             -- Step execution
    validator.py            -- Step validation
    goal_analyzer.py        -- Goal analysis, requirement extraction, domain detection
    strategy_engine.py      -- Strategy generation, risk assessment
    recovery.py             -- Error recovery and state restoration
    learning_engine.py      -- Pattern learning from successes and failures
    success_evaluator.py    -- Overall success evaluation
    final_auditor.py        -- Final audit, evidence collection, report generation
    risk_manager.py         -- Risk assessment and mitigation
  core/                     -- Foundation classes
    session.py              -- Session: logging, progress, context, decisions
    state.py                -- StateMachine: state management, transitions, history
    checkpoint.py           -- Checkpoint: save/restore, automatic checkpointing
  memory/                   -- Persistence files
    goal.md, plan.md        -- Current goal and plan
    decisions.md            -- Decision log
    errors.log              -- Error history
    progress.json           -- Step progress
    context.json            -- Execution context
    learned_rules.json      -- Learned patterns (learning engine)
    successful_patterns.json, failed_patterns.json -- Pattern data
  omni_route/               -- Provider routing
    router.py               -- Request routing to AI providers
    providers.py            -- Provider implementations
  integrations/             -- External integrations
    opencode/               -- OpenCode bridge
  tests/                    -- Test suite
    test_basic.py           -- 16 tests (v1.1 core: states, goal analyzer, strategy, risk, learning, success, audit, bridge)
    test_integration.py     -- Integration tests
    test_ler_v12.py         -- 13 tests (v1.2: security, persistence, governance, architecture, mission)
```

### Architecture Rules

1. Each module owns its directory; no cross-directory writes
2. Every layer depends only on lower-numbered layers
3. All state transitions are auditable
4. Tests must pass before commit
5. Security violations block execution
6. Persistence enables survival across interruptions
7. Governance ensures clear agent responsibilities
8. Architecture validation precedes mission execution

### State Machine

```
INIT -> ANALYZING_GOAL -> CREATING_STRATEGY -> PLANNING ->
EXECUTING -> VALIDATING -> (LEARNING -> REPLANNING -> EXECUTING)* ->
SUCCESS_EVALUATING -> FINAL_AUDITING -> SUCCESS_VERIFIED
```

Transitions are triggered by the Orchestrator based on phase completion, validation results, and recovery needs.

### Mission Lifecycle

1. `MissionRuntime.execute(goal)` receives a goal string
2. Bootstraps governance (agent registration, conflict check)
3. Validates architecture
4. Delegates to Orchestrator for iterative execution
5. Each iteration: analyze -> strategize -> plan -> execute -> validate -> learn
6. Checkpoint persisted before each iteration
7. Security enforced before each file write
8. On failure: recovery attempted, else replan
9. On max_iterations: mission ends with partial results
10. Final result persisted and reported

### Security Model

- `SecurityEnforcer.check_file_before_commit()` -- scans for API keys, passwords, tokens
- `SecurityEnforcer.verify_no_destructive_op()` -- blocks rm -rf, format, del /f
- `SecurityEnforcer.backup_before_modify()` -- creates timestamped backups
- All enforced at runtime/mission level before any file operation

### Governance Model

- `AgentGovernance` manages a `responsibility_map.json` with agent names and responsibilities
- `initialize()` creates a default map if empty, detects conflicts
- `get_all_agents()` returns registered agents
- `ConflictDetector` checks for ownership overlaps, duplicate roles, missing coverage
- Responsibility ownership is unique: each area has exactly one owner

### Persistence Model

- `Persistence.save_mission_state()` persists mission state to JSON
- `Persistence.save_checkpoint()` creates iteration-level checkpoints
- `Persistence.mission_survives_restart()` checks if mission state + checkpoint can be restored
- Data survives power loss, server restart, model change, timeout
- Base directory: `checkpoints/` and `memory/` at project root

### Configuration (config.json v1.2)

- 9 layers defined with paths
- Mission parameters: max_iterations, checkpoint_enabled, auto_recovery, validation_required, adaptive_replanning, learning_enabled, success_threshold, audit_required, survive_interruptions
- Git integration: auto_commit with prefix
- Memory layout: goal, plan, progress, context, decisions, errors, long-term storage
- Learning: enabled with max_rules cap
- Governance: strict enforcement with conflict detection
- Architecture: validation preserving compatibility, simplicity, stability, testability, auditability

### Tests

29 unit tests covering all layers:

| Test Suite | Tests | Coverage |
|-----------|-------|----------|
| `test_basic.py` | 16 | States, GoalAnalyzer, StrategyEngine, RiskManager, LearningEngine, SuccessEvaluator, FinalAuditor, OpenCode bridge |
| `test_ler_v12.py` | 13 | SecurityEnforcer (3), Persistence (4), AgentGovernance (3), ArchitectureReview (2), MissionRuntime (1) |

Run all: `python tests/test_basic.py && python tests/test_ler_v12.py`

### Entry Points

```powershell
python run.py "Criar um aplicativo Android"     # New mission
python run.py --status                           # System status
python run.py --resume                           # Resume from checkpoint
python run.py --inspect                          # Architecture + governance info
python run.py --version                          # Version info
python run.py --reset                            # Reset all state
python run.py --report                           # Generate final report
```

### Principles

1. **Missao nao termina ate objetivo comprovadamente atingido + validacao + auditoria + artefatos + persistencia**
2. Zero external dependencies (stdlib only for core; optional AI providers)
3. Persistence must survive power loss, server restart, model change, timeout, model swap
4. Every decision must have evidence (tests, logs, compilation, execution)
5. Primary source = local machine, secondary = Git, tertiary = GitHub
6. AI Providers (NVIDIA, OpenAI) are swappable engines without architecture changes
7. LER is never a chatbot -- it is a mission executor
