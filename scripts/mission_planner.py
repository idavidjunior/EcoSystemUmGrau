"""Mission Planner + LER Engine - Planejamento hierárquico + ciclo de aprendizado.

Mission Planner: Decompose missões complexas em estratégias, tarefas e passos executáveis
LER Engine: Learning → Execution → Reasoning loop para execução autônoma multi-passo
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
MISSION_DIR = os.path.join(RUNTIME_DIR, 'missions')
sys.path.insert(0, SCRIPTS)

try:
    from runtime_state import load_state, save_state
except ImportError:
    def load_state():
        return {}
    def save_state(state):
        pass


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class MissionTask:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # task IDs
    assignee: str = ""  # agent role or "human"
    estimated_effort: str = ""  # e.g., "2h", "1d"
    actual_effort: str = ""
    result: str = ""
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    subtasks: List['MissionTask'] = field(default_factory=list)


@dataclass
class Strategy:
    id: str
    name: str
    description: str
    tasks: List[MissionTask] = field(default_factory=list)
    rationale: str = ""
    risks: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class Mission:
    id: str
    name: str
    objective: str
    context: str
    strategies: List[Strategy] = field(default_factory=list)
    selected_strategy_id: str = ""
    status: str = "planning"  # planning, executing, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    completed_at: str = ""
    current_task_id: str = ""
    learnings: List[str] = field(default_factory=list)


@dataclass
class LERCycle:
    id: str
    mission_id: str
    task_id: str
    phase: str  # learn, execute, reason
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    insight: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))


class MissionPlanner:
    def __init__(self):
        self.missions: Dict[str, Mission] = {}
        self.ler_cycles: List[LERCycle] = []
        self.max_history = 50
        self._load()

    def _get_storage_path(self):
        return os.path.join(MISSION_DIR, 'missions.json')

    def _ensure_dirs(self):
        os.makedirs(MISSION_DIR, exist_ok=True)

    def _load(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    strategies = []
                    for s in item.get('strategies', []):
                        tasks = [self._deserialize_task(t) for t in s.get('tasks', [])]
                        strategies.append(Strategy(
                            id=s['id'],
                            name=s['name'],
                            description=s['description'],
                            tasks=tasks,
                            rationale=s.get('rationale', ''),
                            risks=s.get('risks', []),
                            success_criteria=s.get('success_criteria', []),
                        ))
                    mission = Mission(
                        id=item['id'],
                        name=item['name'],
                        objective=item['objective'],
                        context=item['context'],
                        strategies=strategies,
                        selected_strategy_id=item.get('selected_strategy_id', ''),
                        status=item.get('status', 'planning'),
                        created_at=item.get('created_at', ''),
                        updated_at=item.get('updated_at', ''),
                        completed_at=item.get('completed_at', ''),
                        current_task_id=item.get('current_task_id', ''),
                        learnings=item.get('learnings', []),
                    )
                    self.missions[mission.id] = mission
            except Exception as e:
                print(f"[MissionPlanner] Erro ao carregar: {e}")

    def _deserialize_task(self, data: Dict) -> MissionTask:
        task = MissionTask(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            status=TaskStatus(data.get('status', 'pending')),
            priority=TaskPriority(data.get('priority', 3)),
            dependencies=data.get('dependencies', []),
            assignee=data.get('assignee', ''),
            estimated_effort=data.get('estimated_effort', ''),
            actual_effort=data.get('actual_effort', ''),
            result=data.get('result', ''),
            error=data.get('error', ''),
            started_at=data.get('started_at', ''),
            completed_at=data.get('completed_at', ''),
            metadata=data.get('metadata', {}),
        )
        task.subtasks = [self._deserialize_task(st) for st in data.get('subtasks', [])]
        return task

    def _serialize_task(self, task: MissionTask) -> Dict:
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status.value,
            'priority': task.priority.value,
            'dependencies': task.dependencies,
            'assignee': task.assignee,
            'estimated_effort': task.estimated_effort,
            'actual_effort': task.actual_effort,
            'result': task.result,
            'error': task.error,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'metadata': task.metadata,
            'subtasks': [self._serialize_task(st) for st in task.subtasks],
        }

    def _save(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        try:
            tmp = path + '.tmp'
            data = []
            for m in list(self.missions.values())[-self.max_history:]:
                item = asdict(m)
                item['strategies'] = [
                    {
                        'id': s.id,
                        'name': s.name,
                        'description': s.description,
                        'tasks': [self._serialize_task(t) for t in s.tasks],
                        'rationale': s.rationale,
                        'risks': s.risks,
                        'success_criteria': s.success_criteria,
                    }
                    for s in m.strategies
                ]
                data.append(item)
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            print(f"[MissionPlanner] Erro ao salvar: {e}")

    def create_mission(self, name: str, objective: str, context: str = "") -> Mission:
        mission_id = str(uuid.uuid4())[:8]
        mission = Mission(
            id=mission_id,
            name=name,
            objective=objective,
            context=context,
        )
        self.missions[mission_id] = mission
        self._save()
        return mission

    def generate_strategies(self, mission_id: str, num_strategies: int = 3) -> List[Strategy]:
        mission = self.missions.get(mission_id)
        if not mission:
            return []

        strategies = []

        # Strategy 1: Conservative/Phased
        s1 = Strategy(
            id=f"{mission_id}_s1",
            name="Abordagem Conservadora (Fases)",
            description="Entregar em fases incrementais com validação contínua",
            rationale="Menor risco, feedback rápido, permite correção de curso",
            risks=["Pode ser mais lento no total", "Requer disciplina de fases"],
            success_criteria=["Cada fase entrega valor", "Testes passam em cada fase", "Zero regressões"],
        )
        s1.tasks = self._generate_phased_tasks(mission)
        strategies.append(s1)

        # Strategy 2: Parallel/Modular
        s2 = Strategy(
            id=f"{mission_id}_s2",
            name="Abordagem Paralela (Modular)",
            description="Desenvolver módulos independentes em paralelo",
            rationale="Mais rápido se equipe disponível, isolamento de falhas",
            risks=["Integração complexa", "Requer coordenação forte", "Possível duplicação"],
            success_criteria=["Módulos integrados com sucesso", "Interfaces estáveis", "Testes de integração passam"],
        )
        s2.tasks = self._generate_modular_tasks(mission)
        strategies.append(s2)

        # Strategy 3: MVP-First
        s3 = Strategy(
            id=f"{mission_id}_s3",
            name="MVP-First (Core Value)",
            description="Entregar valor central mínimo, evoluir depois",
            rationale="Valida hipótese rápido, evita over-engineering",
            risks=["MVP pode ser muito limitado", "Refatoração posterior necessária"],
            success_criteria=["Core functionality works", "Usuários validam valor", "Base extensível"],
        )
        s3.tasks = self._generate_mvp_tasks(mission)
        strategies.append(s3)

        mission.strategies = strategies[:num_strategies]
        mission.updated_at = datetime.now().isoformat(timespec='seconds')
        self._save()
        return strategies

    def _generate_phased_tasks(self, mission: Mission) -> List[MissionTask]:
        base_tasks = [
            ("Análise e Design", "Analisar requisitos, desenhar arquitetura, definir contratos", "01-estrategista", "4h"),
            ("Implementação Core", "Implementar funcionalidade principal", "11-ler-executor", "2d"),
            ("Testes e Validação", "Testes unitários, integração, validação de requisitos", "08-revisor", "1d"),
            ("Documentação", "Documentar arquitetura, decisões, guias de uso", "06-recursos", "4h"),
            ("Deploy e Monitoramento", "Deploy em staging, monitorar, rollback plan", "03-realista", "4h"),
        ]
        return self._create_task_chain(base_tasks)

    def _generate_modular_tasks(self, mission: Mission) -> List[MissionTask]:
        base_tasks = [
            ("Design de Interfaces", "Definir contratos entre módulos", "01-estrategista", "4h"),
            ("Módulo A - Core", "Implementar módulo central", "11-ler-executor", "1d"),
            ("Módulo B - Integração", "Implementar integrações externas", "11-ler-executor", "1d"),
            ("Módulo C - UI/API", "Implementar interface", "11-ler-executor", "1d"),
            ("Integração e Testes", "Integrar módulos, testes end-to-end", "08-revisor", "1d"),
        ]
        return self._create_task_chain(base_tasks, parallel_groups=[[1, 2, 3]])

    def _generate_mvp_tasks(self, mission: Mission) -> List[MissionTask]:
        base_tasks = [
            ("Definir MVP Scope", "Identificar funcionalidade mínima viável", "01-estrategista", "2h"),
            ("Implementar MVP", "Core functionality apenas", "11-ler-executor", "1d"),
            ("Validação com Usuário", "Testar com stakeholder real", "03-realista", "4h"),
            ("Iterar ou Pivotar", "Baseado em feedback", "07-criativo", "1d"),
        ]
        return self._create_task_chain(base_tasks)

    def _create_task_chain(self, task_defs: List[tuple], parallel_groups: List[List[int]] = None) -> List[MissionTask]:
        tasks = []
        for i, (title, desc, assignee, effort) in enumerate(task_defs):
            task = MissionTask(
                id=f"task_{i+1}",
                title=title,
                description=desc,
                assignee=assignee,
                estimated_effort=effort,
                priority=TaskPriority.HIGH if i == 0 else TaskPriority.MEDIUM,
            )
            if i > 0 and not (parallel_groups and any(i in g for g in parallel_groups)):
                task.dependencies = [f"task_{i}"]
            tasks.append(task)
        return tasks

    def select_strategy(self, mission_id: str, strategy_id: str) -> bool:
        mission = self.missions.get(mission_id)
        if not mission:
            return False
        if any(s.id == strategy_id for s in mission.strategies):
            mission.selected_strategy_id = strategy_id
            mission.status = "executing"
            mission.current_task_id = mission.strategies[0].tasks[0].id if mission.strategies[0].tasks else ""
            mission.updated_at = datetime.now().isoformat(timespec='seconds')
            self._save()
            return True
        return False

    def get_next_task(self, mission_id: str) -> Optional[MissionTask]:
        mission = self.missions.get(mission_id)
        if not mission or not mission.selected_strategy_id:
            return None
        strategy = next((s for s in mission.strategies if s.id == mission.selected_strategy_id), None)
        if not strategy:
            return None
        for task in strategy.tasks:
            if task.status == TaskStatus.PENDING:
                deps_met = all(
                    any(t.id == dep and t.status == TaskStatus.COMPLETED for t in strategy.tasks)
                    for dep in task.dependencies
                )
                if deps_met:
                    return task
        return None

    def start_task(self, mission_id: str, task_id: str) -> bool:
        mission = self.missions.get(mission_id)
        if not mission:
            return False
        strategy = next((s for s in mission.strategies if s.id == mission.selected_strategy_id), None)
        if not strategy:
            return False
        task = self._find_task(strategy.tasks, task_id)
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat(timespec='seconds')
            mission.current_task_id = task_id
            mission.updated_at = datetime.now().isoformat(timespec='seconds')
            self._save()
            return True
        return False

    def complete_task(self, mission_id: str, task_id: str, result: str = "", actual_effort: str = "") -> bool:
        mission = self.missions.get(mission_id)
        if not mission:
            return False
        strategy = next((s for s in mission.strategies if s.id == mission.selected_strategy_id), None)
        if not strategy:
            return False
        task = self._find_task(strategy.tasks, task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat(timespec='seconds')
            task.result = result
            task.actual_effort = actual_effort
            mission.updated_at = datetime.now().isoformat(timespec='seconds')
            self._save()
            return True
        return False

    def fail_task(self, mission_id: str, task_id: str, error: str) -> bool:
        mission = self.missions.get(mission_id)
        if not mission:
            return False
        strategy = next((s for s in mission.strategies if s.id == mission.selected_strategy_id), None)
        if not strategy:
            return False
        task = self._find_task(strategy.tasks, task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now().isoformat(timespec='seconds')
            mission.updated_at = datetime.now().isoformat(timespec='seconds')
            self._save()
            return True
        return False

    def _find_task(self, tasks: List[MissionTask], task_id: str) -> Optional[MissionTask]:
        for task in tasks:
            if task.id == task_id:
                return task
            found = self._find_task(task.subtasks, task_id)
            if found:
                return found
        return None

    def record_ler_cycle(self, mission_id: str, task_id: str, phase: str,
                         input_data: Dict, output_data: Dict, insight: str) -> LERCycle:
        cycle = LERCycle(
            id=str(uuid.uuid4())[:8],
            mission_id=mission_id,
            task_id=task_id,
            phase=phase,
            input_data=input_data,
            output_data=output_data,
            insight=insight,
        )
        self.ler_cycles.append(cycle)
        if len(self.ler_cycles) > 200:
            self.ler_cycles = self.ler_cycles[-200:]

        mission = self.missions.get(mission_id)
        if mission and insight:
            mission.learnings.append(f"[{phase}] {insight}")
            mission.updated_at = datetime.now().isoformat(timespec='seconds')
        self._save()
        return cycle

    def execute_ler_loop(self, mission_id: str, task_id: str,
                         learn_fn: Callable, execute_fn: Callable, reason_fn: Callable,
                         max_iterations: int = 3) -> Dict[str, Any]:
        """Executa loop LER: Learn → Execute → Reason"""
        results = {
            'iterations': [],
            'final_output': None,
            'learnings': [],
        }

        for iteration in range(max_iterations):
            # LEARN
            learn_input = {'mission_id': mission_id, 'task_id': task_id, 'iteration': iteration}
            learn_output = learn_fn(learn_input)
            self.record_ler_cycle(mission_id, task_id, 'learn', learn_input, learn_output,
                                f"Iteration {iteration}: learned {len(str(learn_output))} chars")

            # EXECUTE
            exec_input = {**learn_output, 'iteration': iteration}
            exec_output = execute_fn(exec_input)
            self.record_ler_cycle(mission_id, task_id, 'execute', exec_input, exec_output,
                                f"Iteration {iteration}: executed, result={exec_output.get('status', 'unknown')}")

            # REASON
            reason_input = {'learn': learn_output, 'execute': exec_output, 'iteration': iteration}
            reason_output = reason_fn(reason_input)
            self.record_ler_cycle(mission_id, task_id, 'reason', reason_input, reason_output,
                                f"Iteration {iteration}: reasoning complete")

            results['iterations'].append({
                'iteration': iteration,
                'learn': learn_output,
                'execute': exec_output,
                'reason': reason_output,
            })

            if reason_output.get('should_continue', True) is False:
                results['final_output'] = exec_output
                break

            results['learnings'].append(reason_output.get('insight', ''))

        results['final_output'] = results['final_output'] or exec_output
        return results

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        return self.missions.get(mission_id)

    def list_missions(self, limit: int = 20) -> List[Mission]:
        return list(self.missions.values())[-limit:]

    def render_mission(self, mission_id: str) -> str:
        mission = self.missions.get(mission_id)
        if not mission:
            return "Mission not found"

        lines = [f"=== MISSÃO: {mission.name} ===",
                 f"ID: {mission.id}",
                 f"Objetivo: {mission.objective}",
                 f"Status: {mission.status}",
                 f"Estratégia: {mission.selected_strategy_id or 'não selecionada'}",
                 ""]

        strategy = next((s for s in mission.strategies if s.id == mission.selected_strategy_id), None)
        if strategy:
            lines.append(f"--- ESTRATÉGIA: {strategy.name} ---")
            lines.append(f"Racional: {strategy.rationale}")
            lines.append("")
            for task in strategy.tasks:
                status_icon = {
                    TaskStatus.PENDING: "○",
                    TaskStatus.IN_PROGRESS: "◐",
                    TaskStatus.COMPLETED: "●",
                    TaskStatus.FAILED: "✗",
                    TaskStatus.BLOCKED: "⊘",
                }.get(task.status, "?")
                dep_str = f" (deps: {', '.join(task.dependencies)})" if task.dependencies else ""
                lines.append(f"  {status_icon} {task.id}: {task.title} [{task.assignee}] {task.estimated_effort}{dep_str}")
                if task.result:
                    lines.append(f"    → {task.result[:80]}")
                if task.error:
                    lines.append(f"    ✗ {task.error[:80]}")

        if mission.learnings:
            lines.append("")
            lines.append("--- APRENDIZADOS ---")
            for l in mission.learnings[-5:]:
                lines.append(f"  • {l}")

        return "\n".join(lines)

    def stats(self) -> Dict[str, Any]:
        total = len(self.missions)
        executing = sum(1 for m in self.missions.values() if m.status == "executing")
        completed = sum(1 for m in self.missions.values() if m.status == "completed")
        return {
            'total_missions': total,
            'executing': executing,
            'completed': completed,
            'ler_cycles': len(self.ler_cycles),
        }


planner = MissionPlanner()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Mission Planner + LER Engine')
    sub = parser.add_subparsers(dest='cmd')

    p_create = sub.add_parser('create')
    p_create.add_argument('name')
    p_create.add_argument('objective')
    p_create.add_argument('--context', default='')

    p_strat = sub.add_parser('strategies')
    p_strat.add_argument('mission_id')

    p_select = sub.add_parser('select')
    p_select.add_argument('mission_id')
    p_select.add_argument('strategy_id')

    p_next = sub.add_parser('next')
    p_next.add_argument('mission_id')

    p_start = sub.add_parser('start')
    p_start.add_argument('mission_id')
    p_start.add_argument('task_id')

    p_complete = sub.add_parser('complete')
    p_complete.add_argument('mission_id')
    p_complete.add_argument('task_id')
    p_complete.add_argument('--result', default='')
    p_complete.add_argument('--effort', default='')

    p_fail = sub.add_parser('fail')
    p_fail.add_argument('mission_id')
    p_fail.add_argument('task_id')
    p_fail.add_argument('error')

    p_show = sub.add_parser('show')
    p_show.add_argument('mission_id')

    p_list = sub.add_parser('list')
    p_list.add_argument('--limit', type=int, default=20)

    p_stats = sub.add_parser('stats')

    args = parser.parse_args()

    if args.cmd == 'create':
        m = planner.create_mission(args.name, args.objective, args.context)
        print(f"Created mission: {m.id} - {m.name}")

    elif args.cmd == 'strategies':
        strats = planner.generate_strategies(args.mission_id)
        for s in strats:
            print(f"\n{s.id}: {s.name}")
            print(f"  {s.description}")
            print(f"  Rationale: {s.rationale}")
            print(f"  Tasks: {len(s.tasks)}")

    elif args.cmd == 'select':
        ok = planner.select_strategy(args.mission_id, args.strategy_id)
        print(f"Strategy selected: {ok}")

    elif args.cmd == 'next':
        task = planner.get_next_task(args.mission_id)
        if task:
            print(f"Next task: {task.id} - {task.title} [{task.assignee}]")
        else:
            print("No pending tasks")

    elif args.cmd == 'start':
        ok = planner.start_task(args.mission_id, args.task_id)
        print(f"Task started: {ok}")

    elif args.cmd == 'complete':
        ok = planner.complete_task(args.mission_id, args.task_id, args.result, args.effort)
        print(f"Task completed: {ok}")

    elif args.cmd == 'fail':
        ok = planner.fail_task(args.mission_id, args.task_id, args.error)
        print(f"Task failed: {ok}")

    elif args.cmd == 'show':
        print(planner.render_mission(args.mission_id))

    elif args.cmd == 'list':
        for m in planner.list_missions(args.limit):
            print(f"{m.id} | {m.name[:40]} | {m.status} | strategy={m.selected_strategy_id or 'none'}")

    elif args.cmd == 'stats':
        print(json.dumps(planner.stats(), indent=2, ensure_ascii=False))

    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())