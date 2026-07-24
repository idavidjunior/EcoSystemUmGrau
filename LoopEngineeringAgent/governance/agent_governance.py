"""
Agent Governance System (AGS) - Camada 1
Controls ALL agents. Single responsibility per agent.
No duplicated responsibilities. No agent acts without defined ownership.
"""

import json
import os


class AgentGovernance:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.map_file = os.path.join(base_dir, "governance", "responsibility_map.json")
        self.responsibility_map = self._load_map()

    def initialize(self):
        self.session.log("[AGS] Initializing Agent Governance System...")
        map_data = self._load_map()

        if not map_data.get("agents"):
            self.session.log("[AGS] No agents registered. Creating default map.")
            self._create_default_map()
            map_data = self._load_map()

        self.responsibility_map = map_data
        conflicts = self._detect_conflicts(map_data)
        if conflicts:
            for c in conflicts:
                self.session.log(f"[AGS] CONFLICT: {c}", level="WARNING")
            self.session.record_decision(f"AGS detected {len(conflicts)} responsibility conflicts")

        self.session.log(f"[AGS] {len(map_data.get('agents', []))} agents registered, "
                        f"{len(conflicts)} conflicts")
        return {"ready": True, "agents": len(map_data.get("agents", [])), "conflicts": conflicts}

    def _load_map(self):
        if os.path.exists(self.map_file):
            with open(self.map_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _create_default_map(self):
        default_map = {
            "version": "1.2",
            "principle": "Cada responsabilidade possui um unico proprietario",
            "agents": [
                {
                    "name": "GoalAnalyzer",
                    "module": "agent.goal_analyzer",
                    "class": "GoalAnalyzer",
                    "responsibility": "Analisar e traduzir objetivos humanos em requisitos tecnicos",
                    "ownership": ["goal_analysis"],
                    "can_delegate_to": []
                },
                {
                    "name": "StrategyEngine",
                    "module": "agent.strategy_engine",
                    "class": "StrategyEngine",
                    "responsibility": "Gerar e avaliar multiplas estrategias de execucao",
                    "ownership": ["strategy_generation", "strategy_scoring"],
                    "can_delegate_to": []
                },
                {
                    "name": "RiskManager",
                    "module": "agent.risk_manager",
                    "class": "RiskManager",
                    "responsibility": "Avaliar riscos tecnicos antes da execucao",
                    "ownership": ["risk_assessment"],
                    "can_delegate_to": []
                },
                {
                    "name": "Planner",
                    "module": "agent.planner",
                    "class": "Planner",
                    "responsibility": "Transformar estrategia em plano de passos executaveis",
                    "ownership": ["plan_creation", "step_management"],
                    "can_delegate_to": []
                },
                {
                    "name": "Executor",
                    "module": "agent.executor",
                    "class": "Executor",
                    "responsibility": "Executar tarefas e comandos",
                    "ownership": ["task_execution", "command_execution"],
                    "can_delegate_to": ["OpenCode"]
                },
                {
                    "name": "Validator",
                    "module": "agent.validator",
                    "class": "Validator",
                    "responsibility": "Validar resultados de cada etapa",
                    "ownership": ["result_validation", "step_validation"],
                    "can_delegate_to": []
                },
                {
                    "name": "Recovery",
                    "module": "agent.recovery",
                    "class": "Recovery",
                    "responsibility": "Recuperacao de falhas e erros de execucao",
                    "ownership": ["error_recovery", "failure_diagnosis"],
                    "can_delegate_to": []
                },
                {
                    "name": "LearningEngine",
                    "module": "agent.learning_engine",
                    "class": "LearningEngine",
                    "responsibility": "Aprender com erros e sucessos",
                    "ownership": ["pattern_learning", "rule_memory"],
                    "can_delegate_to": []
                },
                {
                    "name": "SuccessEvaluator",
                    "module": "agent.success_evaluator",
                    "class": "SuccessEvaluator",
                    "responsibility": "Avaliar pontuacao de sucesso da missao",
                    "ownership": ["success_scoring", "outcome_evaluation"],
                    "can_delegate_to": []
                },
                {
                    "name": "FinalAuditor",
                    "module": "agent.final_auditor",
                    "class": "FinalAuditor",
                    "responsibility": "Auditar entrega final e gerar relatorio",
                    "ownership": ["final_audit", "report_generation"],
                    "can_delegate_to": []
                },
                {
                    "name": "OpenCodeBridge",
                    "module": "integrations.opencode.opencode_bridge",
                    "class": "OpenCodeBridge",
                    "responsibility": "Interface entre LER e OpenCode",
                    "ownership": ["opencode_integration", "external_delegation"],
                    "can_delegate_to": ["OpenCode"]
                }
            ],
            "governance_rules": [
                "Nenhum agente pode possuir responsabilidades duplicadas",
                "Nenhum agente pode executar tarefas sem responsabilidade definida",
                "Toda responsabilidade deve possuir um unico proprietario",
                "Conflitos devem ser detectados antes da execucao"
            ]
        }
        os.makedirs(os.path.dirname(self.map_file), exist_ok=True)
        with open(self.map_file, "w", encoding="utf-8") as f:
            json.dump(default_map, f, indent=2, ensure_ascii=False)

    def _detect_conflicts(self, map_data):
        conflicts = []
        ownership = {}
        for agent in map_data.get("agents", []):
            for resp in agent.get("ownership", []):
                if resp in ownership:
                    conflicts.append(f"Responsabilidade '{resp}' pertence a "
                                   f"{ownership[resp]} e {agent['name']}")
                ownership[resp] = agent["name"]
        return conflicts

    def get_agent_by_responsibility(self, responsibility):
        for agent in self.responsibility_map.get("agents", []):
            if responsibility in agent.get("ownership", []):
                return agent
        return None

    def get_all_agents(self):
        return self.responsibility_map.get("agents", [])
