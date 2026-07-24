# Loop Engineering Runtime (LER) v2.0

## Architecture

A LER is a mission-oriented autonomous engineering platform. It receives a goal and drives it to completion through 13 layers of coordinated execution with evidence-based scoring, autonomous replanning, and self-improvement.

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
| 10 - Evidence | `agent/evidence_collector` | Logs, files, hashes, tests, artifacts, timing |
| 11 - Tools | `agent/tool_selector` | Tool routing, feedback loop, success tracking |
| 12 - Self-Improvement | `agent/self_improvement` | Post-mission evaluation, bottleneck detection |
| 13 - Supervisor | `agent/supervisor` | Module monitoring, automatic recovery |

### Module Map

```
LoopEngineeringAgent/
  run.py                    -- Entry point (CLI)
  loop.py                   -- v1.0 legacy entry point
  config/
    config.json             -- System configuration (v2.0)
    agent_rules.json        -- Agent behavior rules
    routes.json             -- OmniRoute provider routing
    .env / .env.template    -- Environment variables
  runtime/                  -- Mission runtime
    kernel.py               -- System boot
    mission.py              -- MissionRuntime
    persistence.py          -- Checkpoint save/load
    security.py             -- SecurityEnforcer
  governance/               -- Agent Governance System
    agent_governance.py     -- AgentGovernance
    conflict_detector.py    -- ConflictDetector
    responsibility_map.json -- Agent responsibility definitions
  architecture/             -- Architecture Review Engine
    review_engine.py        -- ArchitectureReviewEngine
    validators.py           -- Validators
  agent/                    -- Core agent machinery (v1.0/v2.0)
    orchestrator.py         -- Orchestrator v2.0: goal-oriented loop
    planner.py              -- Plan creation
    executor.py             -- Step execution
    validator.py            -- Step validation
    goal_analyzer.py        -- GoalAnalyzer v2.0: GoalSpecification, DoD, AC
    strategy_engine.py      -- StrategyEngine v2.0: 3+ strategies, ranking, auto-select
    risk_manager.py         -- RiskManager v2.0: 6 risk categories, contingency
    learning_engine.py      -- LearningEngine v2.0: permanent memory, tool/arch patterns
    success_evaluator.py    -- SuccessEvaluator v2.0: weighted 6-category scoring
    final_auditor.py        -- FinalAuditor v2.0: expanded report with DoD, AC, evidence
    evidence_collector.py   -- NEW: evidence collection (logs, files, hashes, tests)
    tool_selector.py        -- NEW: tool routing + feedback loop
    self_improvement.py     -- NEW: post-mission evaluation
    supervisor.py           -- NEW: module monitoring and recovery
    recovery.py             -- Error recovery
  core/                     -- Foundation classes
  memory/                   -- Persistence files
    goal.md, plan.md        -- Current goal and plan
    decisions.md            -- Decision log
    progress.json           -- Step progress
    context.json            -- Execution context
    learned_rules.json      -- Learned rules
    successful_patterns.json, failed_patterns.json -- Pattern data
    tool_statistics.json    -- Tool performance stats
    architecture_patterns.json -- Architecture patterns
    projects/               -- Long-term project memory
    knowledge/              -- Cross-mission knowledge
    patterns/               -- Pattern archive
    solutions/              -- Archived solutions
    architectures/          -- Architecture references
    decisions/              -- Decision history
  integrations/             -- External integrations
    opencode/               -- OpenCode bridge
  tests/                    -- Test suite
    test_basic.py           -- 16 tests (v1.1)
    test_ler_v12.py         -- 13 tests (v1.2)
    test_ler_v20.py         -- 31 tests (v2.0 new modules)
```

### Goal Analyzer v2.0

Produces `GoalSpecification` with:
- `objective` - extracted objective
- `requirements` - explicit/implicit requirements
- `constraints` - technical/environmental constraints
- `dependencies` - required tools/libraries
- `assumptions` - assumed preconditions
- `acceptance_criteria` - verifiable criteria (AC)
- `definition_of_done` - completion checklist (DoD)
- `risks` - identified risks

Every goal MUST pass through GoalAnalyzer before Planner.

### Strategy Engine v2.0

Generates minimum 3 strategies (up to 5):
- **A - Directa**: Direct implementation by requirements
- **B - Alternativa**: Reduced scope, fast validation
- **C - Conservadora**: Maximum safety, extensive validation
- **D - Incremental** (if complexity >= 5): Iterative with partial deliveries
- **E - Paralela** (if requirements exist): Parallel independent modules

Each strategy has: `cost`, `risk`, `estimated_time`, `complexity`, `success_probability`, `score`.

Ranking algorithm selects best. Failed strategies are tracked and not repeated.

### Risk Manager v2.0

6 risk categories:
1. **Environment** - Tools, permissions, OS compatibility
2. **Goal** - Complexity, ambiguity, domain-specific
3. **Technical** - Technologies, integration complexity
4. **External** - Service availability, third-party issues
5. **Dependency** - Missing/incompatible dependencies
6. **API** - Rate limiting, auth, contract changes
7. **Permission** - Admin rights, write restrictions
8. **Strategy** - Risk level, parallel execution

Every risk has: `mitigation_plan` + `contingency` plan.

### Learning Engine v2.0

Permanent memory with:
- `learned_rules.json` - Error patterns with suggested fixes
- `successful_patterns.json` - Success patterns
- `failed_patterns.json` - Failure records
- `tool_statistics.json` - Per-tool performance metrics
- `architecture_patterns.json` - Architecture decision records
- `knowledge/mission_experience.json` - Cross-mission knowledge
- `patterns/` - Pattern archive directory

### Success Evaluator v2.0

Weighted scoring based on evidence:

| Category | Weight | Source |
|----------|--------|--------|
| Requirements | 40% | DoD/AC satisfaction |
| Functionality | 30% | Step completion rate |
| Tests | 15% | Test pass rate |
| Quality | 5% | Execution quality |
| Evidence | 5% | Evidence completeness |
| Audit | 5% | Audit checklist pass rate |

**Threshold: 95%** (configurable). Mission only ends when score >= threshold.

### Evidence Collector

Collects automatically:
- Logs (session files)
- Files (artifacts with SHA256 hashes)
- Test results (pass/fail per test file)
- Decisions (decision log)
- Timing (start/finish/elapsed)
- Generates: `reports/evidence.json` and `reports/evidence.md`

### Tool Selector

Routes tasks to appropriate tools:
- Programming/Coding → OpenCode
- LLM/Reasoning → NVIDIA
- Terminal/Filesystem → Shell
- Versioning → Git
- Testing/Scripting → Python

Tracks per-tool: avg duration, success rate, cost, latency.
Auto-fallback if tool success rate drops below 50%.

### Self Improvement

Post-mission evaluation detects:
- **Bottlenecks**: High avg time per iteration, low completion rate
- **Waste**: Uncompleted steps, excessive iterations
- **Rework**: High failure-to-completion ratio
- **Recurring failures**: Errors seen 3+ times without successful fix

Generates improvement suggestions. Saves report to `reports/self_improvement_*.json`.

### Supervisor

Monitors all modules continuously:
- `monitor_all()` - Check every module's health
- `recover_module()` - Restart failed modules individually
- `get_health_report()` - Aggregate health status
- `supervise_operation()` - Wrapped execution with error capture

Never restarts entire mission for a single module failure.

### Goal-Oriented Loop

```
while DoD not satisfied:
  Analyze Goal (GoalSpecification)
  Generate Strategies (3+)
  Assess Risks (mitigation + contingency)
  Plan (steps with DoD awareness)
  Execute (with ToolSelector routing)
  Validate
  Collect Evidence
  Learn (rules + patterns + tools)
  
  if score >= threshold:
    Audit
    Verify
    Complete
  else:
    Autonomous Replan:
      Analyze cause
      Consult memory
      Mark failed strategy
      Select next best strategy
      Replan
      Execute again
      Compare results
```

### Absolute Completion Criteria

Mission ONLY ends when ALL true:
- ✓ Definition of Done satisfied
- ✓ Acceptance Criteria satisfied
- ✓ Success Score >= Threshold (95%)
- ✓ Audit passed
- ✓ Evidence collected
- ✓ No critical errors remaining

Otherwise: **continue automatically** the Loop Engineering Runtime.

### Final Report (expanded)

Mandatory sections:
1. Objective
2. Definition of Done
3. Acceptance Criteria
4. Strategy chosen (with score, risk, success_prob)
5. Strategies discarded (with reason)
6. Risks and Mitigations (with contingency)
7. Execution (steps detail)
8. Failures and Corrections
9. Knowledge learned
10. Evidence (logs, files, hashes, tests, artifacts)
11. Success Score (breakdown per category)
12. Audit (checklist)
13. Justification for closure (criteria absolute)

### Tests

60 unit tests covering all layers:

| Test Suite | Tests | Coverage |
|-----------|-------|----------|
| `test_basic.py` | 16 | v1.1 core modules |
| `test_ler_v12.py` | 13 | v1.2 runtime, governance, architecture |
| `test_ler_v20.py` | 31 | v2.0: GoalSpec, StrategyRanking, Risk6Cat, LearningTools, Evidence, ToolSelect, SelfImprove, Supervisor, DoD, ExpandedReport |

Run all: `python tests\test_basic.py && python tests\test_ler_v12.py && python tests\test_ler_v20.py`

### CLI

```powershell
python run.py "Sua missao aqui"           # New mission
python run.py --status                     # System status
python run.py --resume                     # Resume from checkpoint
python run.py --inspect                    # Architecture + governance info
python run.py --version                    # Version info
python run.py --reset                      # Reset all state
python run.py --report                     # Generate final report
```

### Principles

1. **Missao nao termina ate objetivo comprovadamente atingido + validacao + auditoria + evidencias + persistencia**
2. Zero external dependencies (stdlib only for core)
3. Persistence survives power loss, server restart, model change, timeout
4. Every decision must have evidence (tests, logs, compilation, execution, hashes)
5. AI Providers are swappable engines without architecture changes
6. LER is never a chatbot -- it is a mission executor
7. Every error is a learning opportunity recorded in permanent memory
8. Failed strategies are never repeated without changes
