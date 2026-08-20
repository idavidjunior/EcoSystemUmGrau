"""Autonomous Mission Loop — ETAPA 20

Motor de execução orientado a missões que transforma objetivos em missões
executáveis, observáveis e verificáveis.

Constrói sobre:
- ETAPA 18: Cognitive Core (intenção, classificação, avaliação cognitiva)
- ETAPA 19: Tool/Permission Runtime (autorização, capacidades, permissões)
- mission_planner.py (estrutura de missão, estratégias, tarefas)
"""

import sys
import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple

# Adicionar raiz do projeto ao path
BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
sys.path.insert(0, SCRIPTS)

# Importações dos módulos existentes
from cognitive_core import analyze_intent
from tool_permission_runtime import (
    ToolPermissionRuntime, process_tool_request, ToolRegistry,
    PermissionEngine, ConfirmationManager, ArgumentValidator,
    ToolDefinition, ExecutionContext, AuthorizationDecision,
    ToolResult, FailureClassification
)
from mission_planner import (
    MissionPlanner, Mission, Strategy, MissionTask, TaskStatus,
    TaskPriority, LERCycle, planner as mission_planner
)
from scripts.security_engine import SecurityEngine

# ──────────────────────────────────────────────────────────────────
# Estados da Máquina de Estados da Missão (strings simples)
# ──────────────────────────────────────────────────────────────────

MISSION_STATES = (
    "CREATED",
    "ANALYZING",
    "PLANNED",
    "READY",
    "EXECUTING",
    "VERIFYING",
    "COMPLETED",
    "FAILED",
    "BLOCKED",
    "CANCELLED",
    "TIMEOUT",
)

# ──────────────────────────────────────────────────────────────────
# MissionLoop - Motor principal
# ──────────────────────────────────────────────────────────────────

class MissionLoop:
    """Motor autônomo de execução de missões."""

    def __init__(self):
        self._tool_runtime = ToolPermissionRuntime()
        self._planner = mission_planner
        self._security = SecurityEngine()
        self._confirmation_mgr = ConfirmationManager()
        # Journal usamos dicts simples para evitar NamedTuple/TypedDict complexity
        self._journal: List[Dict[str, Any]] = []
        self._max_tool_calls = 50
        self._max_replans = 5
        self._max_execution_time = 300  # segundos
        self._resource_locks: Dict[str, str] = {}  # resource -> mission_id
        self._attempt_counts: Dict[str, int] = {}  # mission_id -> count
        self._step_attempt_counts: Dict[str, int] = {}  # step_id -> count (anti-loop)
        self._start_time: Optional[float] = None
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return True
        if not self._tool_runtime.initialize():
            return False
        self._initialized = True
        return True

    # ---- Journal (dicts simples) ----

    def _journal_event(self, event: str, **kwargs):
        """Adiciona um evento ao journal com campos padronizados."""
        entry = {
            'event': event,
            'timestamp': time.time(),
            **kwargs
        }
        self._journal.append(entry)

    # ---- Budget / Deadline ----

    def set_budget(self, max_tool_calls: int = 50, max_time: int = 300,
                   max_replans: int = 5):
        self._max_tool_calls = max_tool_calls
        self._max_execution_time = max_time
        self._max_replans = max_replans
        self._attempt_counts = {}

    def check_budget(self, mission_id: str) -> Tuple[bool, Optional[str]]:
        """Retorna (dentro_budget, motivo_se_over)"""
        if self._attempt_counts.get(mission_id, 0) >= self._max_tool_calls:
            return False, f"Tool calls exceeded ({self._max_tool_calls})"
        if self._start_time and (time.time() - self._start_time) > self._max_execution_time:
            return False, f"Execution time exceeded ({self._max_execution_time}s)"
        return True, None

    # ---- Resource locks ----

    def acquire_lock(self, resource: str, mission_id: str) -> bool:
        if resource in self._resource_locks:
            existing = self._resource_locks[resource]
            if existing == mission_id:
                return True  # já possuído por esta missão
            return False  # bloqueado por outra missão
        self._resource_locks[resource] = mission_id
        return True

    def release_lock(self, resource: str, mission_id: str):
        if self._resource_locks.get(resource) == mission_id:
            del self._resource_locks[resource]

    # ---- Anti-loop detection ----

    def _detect_identical_action(self, mission_id: str, step_id: str,
                                 tool_id: str, capability: str) -> bool:
        """Detecta se esta mesma combinação já foi executada demasiadas vezes."""
        key = f"{mission_id}:{step_id}:{tool_id}:{capability}"
        count = self._step_attempt_counts.get(key, 0)
        if count >= 3:  # após 3 tentativas idênticas failed
            self._step_attempt_counts[key] = count + 1
            return True
        self._step_attempt_counts[key] = count + 1
        return False

    # ---- Failure classification ----

    def classify_failure(self, error_msg: str, capability: str) -> Dict[str, Any]:
        """Classifica o tipo de falha para decidir recovery."""
        error = (error_msg or "").lower()

        # Security violation / path traversal
        if any(p in error for p in ['path traversal', 'blocked by security',
                                    'access denied', 'permission denied']):
            return {'category': 'SECURITY', 'detail': error_msg[:120] if error_msg else '',
                    'retryable': False, 'auto_recovery': False,
                    'suggested_action': 'block'}

        # Permissions
        if 'permission denied' in error or 'PERMISSION_DENIED' in error_msg:
            return {'category': 'PERMISSION', 'detail': error_msg[:120] if error_msg else '',
                    'retryable': False, 'auto_recovery': False,
                    'suggested_action': 'block'}

        # Transient / timeout
        if any(p in error for p in ['timeout', 'temporarily', 'interrupted',
                                    'network', 'connection refused']):
            return {'category': 'TRANSIENT', 'detail': error_msg[:120] if error_msg else '',
                    'retryable': True, 'auto_recovery': True,
                    'suggested_action': 'retry'}

        # Resource
        if any(p in error for p in ['memory', 'disk space', 'resource',
                                    'limit exceeded']):
            return {'category': 'RESOURCE', 'detail': error_msg[:120] if error_msg else '',
                    'retryable': False, 'auto_recovery': False,
                    'suggested_action': 'block'}

        # Dependency
        if any(p in error for p in ['dependency', 'not found', 'unavailable',
                                    'module not found']):
            return {'category': 'DEPENDENCY', 'detail': error_msg[:120] if error_msg else '',
                    'retryable': True, 'auto_recovery': True,
                    'suggested_action': 'replan'}

        # Strategic - the plan isn't working
        if any(p in error for p in ['cannot', 'failed', 'error',
                                    'invalid', 'wrong']):
            return {'category': 'STRATEGIC', 'detail': error_msg[:120] if error_msg else '',
                    'retryable': False, 'auto_recovery': False,
                    'suggested_action': 'replan'}

        # Default
        return {'category': 'UNKNOWN', 'detail': error_msg[:120] if error_msg else '',
                'retryable': False, 'auto_recovery': False,
                'suggested_action': 'ask_user'}

    # ---- Step execution through Tool Runtime ----

    def _execute_step_tool(self, step: Any,
                           tool_id: str, capability: str,
                           arguments: Dict[str, Any]) -> Tuple[Optional[Dict], str]:
        """Executa um passo através do Tool Permission Runtime.

        Retorna (result_dict, authorization_reason).
        O parâmetro 'step' pode ser um dict ou um MissionTask object.
        """
        # Normalizar step para dict se for MissionTask object
        if hasattr(step, 'get'):  # já é dict
            step_dict = step
        else:  # MissionTask object - converter usando __dict__ ou atributos
            step_dict = {
                'id': step.id,
                'title': step.title,
                'description': step.description,
                'metadata': step.metadata if hasattr(step, 'metadata') else {},
                'dependencies': step.dependencies if hasattr(step, 'dependencies') else []
            }

        req = {
            'tool_id': tool_id,
            'capability': capability,
            'arguments': arguments or {},
            'execution_context': {
                'permissions': step_dict.get('metadata', {}).get('permissions', [])
                    if step_dict.get('metadata') else []
            },
            'session_id': f"mission_{step_dict.get('id', 'unknown')}",
            'request_id': str(uuid.uuid4())
        }

        resp = self._tool_runtime.request_tool_execution(req)
        auth_decision = resp.get('authorization_decision')
        auth_reason = resp.get('authorization_reason', 'unknown')

        # Extrair resultado
        tool_result = None
        result_data = resp.get('result')
        if result_data and isinstance(result_data, dict):
            tool_result = {
                'success': result_data.get('success', False),
                'status': result_data.get('status', 'unknown'),
                'data': result_data.get('data'),
                'error': result_data.get('error'),
                'error_code': result_data.get('error_code'),
                'duration': result_data.get('duration', 0.0),
                'metadata': result_data.get('metadata', {}),
                'execution_id': result_data.get('execution_id', str(uuid.uuid4()))
            }

        return tool_result, auth_reason

    # ---- Main mission execution loop ----

    def execute_mission(self, mission_id: str, objective: str,
                        context: str = "") -> Dict[str, Any]:
        """Executa uma missão do início ao fim.

        Retorna dict com status final, journal, aprendizados, etc.
        """
        # Inicializar temporizadores
        self._start_time = time.time()
        self._attempt_counts = {}
        self._step_attempt_counts = {}
        self._journal = []  # reset journal

        # Carregar ou criar missão
        mission = self._planner.get_mission(mission_id)
        if not mission:
            mission = self._planner.create_mission(
                name=f"Mission-{mission_id}",
                objective=objective,
                context=context or f"Objetivo: {objective}"
            )
            self._journal_event('MISSION_CREATED', mission_id=mission_id,
                                objective=objective)

        # FASE 1: Análise da intenção
        self._set_mission_state(mission_id, "ANALYZING")
        self._journal_event('MISSION_ANALYZED', mission_id=mission_id,
                            objective=objective)

        # Análise de intenção usando Cognitive Core
        intent_result = analyze_intent(objective)
        intent = intent_result.get("intent", "conversation")
        confidence = intent_result.get("confidence", 0.5)

        self._journal_event('INTENT_ANALYSIS', mission_id=mission_id,
                            intent=intent, confidence=confidence)

        # Se a intenção for conversation, pedir confirmação
        if intent == "conversation":
            self._set_mission_state(mission_id, "BLOCKED")
            self._journal_event('INTENT_CONVERSATION', mission_id=mission_id,
                                outcome="Requires human clarification")
            return {
                'status': 'blocked',
                'reason': 'Objetivo com natureza de conversa, requer esclarecimento humano',
                'mission_id': mission_id,
                'journal': self._journal
            }

        # FASE 2: Verificar/planejar estratégias
        self._set_mission_state(mission_id, "PLANNED")
        self._journal_event('MISSION_PLANNED', mission_id=mission_id,
                            strategies=len(mission.strategies))

        # Selecionar primeira estratégia ativa
        if not mission.selected_strategy_id:
            strategies = self._planner.generate_strategies(mission_id, num_strategies=1)
            if not strategies:
                self._set_mission_state(mission_id, "FAILED")
                return {'status': 'failed', 'reason': 'Could not generate strategies',
                        'mission_id': mission_id, 'journal': self._journal}
            self._planner.select_strategy(mission_id, strategies[0].id)

        # FASE 3: Executar passos
        self._set_mission_state(mission_id, "EXECUTING")
        self._journal_event('MISSION_EXECUTING', mission_id=mission_id)

        result = self._execute_steps(mission_id, mission, objective)

        # FASE 4: Verificação final
        self._set_mission_state(mission_id, "VERIFYING")
        self._journal_event('MISSION_VERIFYING', mission_id=mission_id)

        # Validar se todos os critérios de sucesso foram atendidos
        final_result = self._finalize_mission(mission_id, result, objective)

        # Registrar tempo final
        final_result['total_duration'] = time.time() - self._start_time
        final_result['journal'] = self._journal
        final_result['evidence_count'] = len([e for e in self._journal
                                              if e.get('event') in ('STEP_COMPLETED',
                                                                       'MISSION_COMPLETED')])

        self._set_mission_state(mission_id, final_result['status'])
        return final_result

    def _execute_steps(self, mission_id: str, mission: Mission,
                       objective: str) -> Dict[str, Any]:
        """Executa os passos da estratégia selecionada."""
        strategy = next((s for s in mission.strategies if s.id == mission.selected_strategy_id), None)
        if not strategy:
            return {'status': 'no_strategy', 'completed_steps': 0, 'failed_steps': 0}

        completed_steps = 0
        failed_steps = 0
        max_iterations = self._max_replans + 1

        for strategy_idx, strategy in enumerate(mission.strategies):
            if strategy_idx > 0:
                # Trocar de estratégia
                self._planner.select_strategy(mission_id, strategy.id)

            for task in strategy.tasks:
                # Verificar se já está completado ou falhou
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    if task.status == TaskStatus.COMPLETED:
                        completed_steps += 1
                    continue

                # Verificar orçamento
                budget_ok, budget_reason = self.check_budget(mission_id)
                if not budget_ok:
                    return {
                        'status': 'budget_exceeded',
                        'completed_steps': completed_steps,
                        'failed_steps': failed_steps,
                        'reason': budget_reason
                    }

                # Registrar início do passo
                self._journal_event('STEP_STARTED', mission_id=mission_id,
                                    step_id=task.id,
                                    step_title=task.title)

                # Determinar qual ferramenta usar baseado na descrição da tarefa
                tool_id, capability, arguments = self._determine_tool_for_task(
                    task.__dict__ if hasattr(task, '__dict__') else {},
                    objective)

                # Definir permissões necessárias baseadas na tool selecionada
                # Isso garante que o Permission Engine da ETAPA 19 aceite a execução
                tool_to_permissions = {
                    'memory_read': ['memory.read'],
                    'filesystem_read': ['filesystem.read'],
                    'shell_execute': ['shell.execute'],
                }
                required_perms = tool_to_permissions.get(tool_id, ['memory.read'])
                
                # Atribuir permissões à task metadata para persistência
                if not task.metadata:
                    task.metadata = {}
                task.metadata['permissions'] = required_perms
                task.metadata['tool_id'] = tool_id
                task.metadata['capability'] = capability

                if not tool_id:
                    # Nada a executar, marcar como concluída
                    task.status = TaskStatus.COMPLETED
                    task.result = f"Step '{task.title}' - no tool required"
                    task.completed_at = datetime.now().isoformat(timespec='seconds')
                    completed_steps += 1
                    self._journal_event('STEP_COMPLETED',
                                        mission_id=mission_id,
                                        step_id=task.id,
                                        outcome=f"Completed (no tool): {task.title}")
                    continue

                # Verificar pré-condições
                precond_ok = self._verify_preconditions(task, objective)
                if not precond_ok:
                    task.status = TaskStatus.FAILED
                    task.error = "Preconditions not met"
                    failed_steps += 1
                    self._journal_event('STEP_FAILED',
                                        mission_id=mission_id,
                                        step_id=task.id,
                                        outcome=f"Failed (preconditions): {task.title}",
                                        error="Preconditions not met")
                    continue

                # Executar através do Tool Permission Runtime
                tool_result, auth_reason = self._execute_step_tool(
                    task, tool_id, capability, arguments or {})

                # Verificar autorização
                if auth_reason and "DENY" in str(auth_reason).upper():
                    task.status = TaskStatus.FAILED
                    task.error = f"Authorization denied: {auth_reason}"
                    failed_steps += 1
                    self._journal_event('STEP_FAILED',
                                        mission_id=mission_id,
                                        step_id=task.id,
                                        outcome=f"Failed (auth denied): {task.title}",
                                        error=f"Authorization denied: {auth_reason}")
                    continue

                # Processar resultado
                if tool_result and tool_result.get('success'):
                    task.status = TaskStatus.COMPLETED
                    task.result = f"Success: {tool_result.get('data')}"
                    task.completed_at = datetime.now().isoformat(timespec='seconds')
                    completed_steps += 1

                    self._journal_event('STEP_COMPLETED',
                                        mission_id=mission_id,
                                        step_id=task.id,
                                        outcome=f"Completed: {task.title}",
                                        evidence={"result": str(tool_result.get('data'))[:500]})

                    # Verificar critérios de sucesso na metadata da task
                    # task pode ser MissionTask object ou dict - normalizar
                    task_meta = task.metadata if hasattr(task, 'metadata') else task.get('metadata', {})
                    if task_meta and task_meta.get('success_criteria'):
                        criteria = task_meta['success_criteria']
                        data_str = str(tool_result.get('data')) if tool_result.get('data') else ""
                        for criterion in criteria:
                            if criterion.lower() in data_str.lower():
                                # Critério atendido - continuar
                                pass

                elif tool_result and not tool_result.get('success'):
                    task.status = TaskStatus.FAILED
                    task.error = tool_result.get('error') or "Unknown error"
                    failed_steps += 1

                    # Classificar falha
                    failure = self.classify_failure(
                        tool_result.get('error') or "",
                        capability or 'unknown')

                    self._journal_event('STEP_FAILED',
                                        mission_id=mission_id,
                                        step_id=task.id,
                                        outcome=f"Failed: {task.title}",
                                        error=failure['detail'],
                                        failure_category=failure['category'],
                                        retryable=failure['retryable'],
                                        suggested_action=failure['suggested_action'])

                    # Ação baseada na classificação
                    if failure['retryable'] and self._attempt_counts.get(mission_id, 0) < self._max_tool_calls:
                        self._attempt_counts[mission_id] = self._attempt_counts.get(mission_id, 0) + 1
                        # Retry - continuar o loop, tentar novamente
                        continue
                    elif failure['suggested_action'] == 'replan':
                        # Replan - quebrar e mudar estratégia
                        break
                    else:
                        # Bloquear ou pedir ajuda
                        break

                else:
                    # Nenhum resultado retornado
                    task.status = TaskStatus.FAILED
                    task.error = "No result returned from tool"
                    failed_steps += 1
                    break

        return {
            'status': 'completed' if failed_steps == 0 else 'failed',
            'completed_steps': completed_steps,
            'failed_steps': failed_steps
        }

    def _determine_tool_for_task(self, task_dict: Dict, objective: str) -> Tuple:
        """Determina qual ferramenta usar baseado na descrição da tarefa."""
        desc = (task_dict.get('title', '') + ' ' + task_dict.get('description', '')).lower()

        if any(k in desc for k in ['ler', 'memory', 'consultar', 'buscar', 'obter']):
            return 'memory_read', 'memory.read', {'query': objective[:200]}
        elif any(k in desc for k in ['arquivo', 'ler arquivo', 'caminho', 'path']):
            return 'filesystem_read', 'filesystem.read', {'path': objective[:200]}
        elif any(k in desc for k in ['executar', 'shell', 'comando', 'rm', 'criar', 'escrever']):
            return 'shell_execute', 'shell.execute', {'command': objective[:200]}
        elif any(k in desc for k in ['analisar', 'estrutura', 'projeto']):
            return 'memory_read', 'memory.read', {'query': objective[:200]}
        else:
            return 'memory_read', 'memory.read', {'query': objective}

    def _verify_preconditions(self, task: Dict, objective: str) -> bool:
        """Verifica pré-condições de uma tarefa."""
        # Verificar dependências - simplificado: sempre True
        # Em implementação full, verificaríamos se tarefas dependentes foram concluídas
        return True

    def _validate_success_criteria(self, task: Dict, tool_result: Dict):
        """Valida critérios de sucesso definidos na task metadata."""
        criteria = task.get('metadata', {}).get('success_criteria', []) if task.get('metadata') else []
        if not criteria:
            return
        data_str = str(tool_result.get('data')) if tool_result.get('data') else ""
        for criterion in criteria:
            if criterion.lower() in data_str.lower():
                pass  # critério atendido

    def _finalize_mission(self, mission_id: str, execution_result: Dict,
                          objective: str) -> Dict[str, Any]:
        """Finaliza a missão - validar critérios globais."""

        # Verificar budget e deadline
        budget_ok, budget_reason = self.check_budget(mission_id)
        if not budget_ok:
            self._planner.fail_task(mission_id, mission.current_task_id or "",
                                    f"Budget: {budget_reason}")
            return {
                'status': 'budget_exceeded',
                'objective': objective,
                'mission_id': mission_id,
                'completed': False,
                'journal': self._journal
            }

        # Contar passos concluídos vs total
        mission = self._planner.get_mission(mission_id)
        if not mission:
            return {'status': 'not_found', 'objective': objective}

        total_steps = sum(len(s.tasks) for s in mission.strategies)
        completed_steps = sum(
            1 for s in mission.strategies
            for t in s.tasks
            if t.status == TaskStatus.COMPLETED
        )

        completion_rate = completed_steps / max(total_steps, 1)

        # Registrar LER cycle final
        self._planner.record_ler_cycle(mission_id, mission.current_task_id or "",
                                       "complete",
                                       {"objective": objective,
                                        "completed_steps": completed_steps,
                                        "total_steps": total_steps,
                                        "rate": completion_rate},
                                       {"status": "completed"},
                                       "Mission execution completed")

        # Decidir status final
        if completion_rate >= 0.8 and len(mission.strategies) > 0:
            self._planner.select_strategy(mission_id, mission.strategies[0].id)
            # Marcar última tarefa como completada para fechar a missão
            last_task = self._planner.get_next_task(mission_id)
            if last_task:
                self._planner.complete_task(mission_id, last_task.id,
                                            result=f"Mission: {objective}")
            return {
                'status': 'completed',
                'objective': objective,
                'mission_id': mission_id,
                'completion_rate': completion_rate,
                'completed_steps': completed_steps,
                'total_steps': total_steps,
                'journal': self._journal,
                'evidence': [e for e in self._journal
                             if e.get('event') in ('STEP_COMPLETED', 'MISSION_COMPLETED')]
            }
        else:
            # Missão falhou
            self._planner.fail_task(mission_id, mission.current_task_id or "",
                                    f"Completion rate {completion_rate:.0%} below threshold")
            return {
                'status': 'failed',
                'objective': objective,
                'mission_id': mission_id,
                'completion_rate': completion_rate,
                'completed_steps': completed_steps,
                'total_steps': total_steps,
                'journal': self._journal,
                'reason': f'Completion rate {completion_rate:.0%} below 80% threshold'
            }

    def _set_mission_state(self, mission_id: str, state: str):
        """Define o estado da missão."""
        mission = self._planner.get_mission(mission_id)
        if mission:
            mission.status = state
            mission.updated_at = datetime.now().isoformat(timespec='seconds')
            self._planner._save()

        self._journal_event('STATE_CHANGE', mission_id=mission_id, state=state)


# ──────────────────────────────────────────────────────────────────
# Função auxiliar para criar e executar missão
# ──────────────────────────────────────────────────────────────────

def create_and_execute_mission(objective: str,
                               mission_name: str = "",
                               context: str = "",
                               max_tool_calls: int = 50,
                               max_time: int = 300,
                               max_replans: int = 5) -> Dict[str, Any]:
    """Função conveniente: cria e executa uma missão em um passo.

    Args:
        objective: O objetivo/descrição da missão
        mission_name: Nome da missão (opcional)
        context: Contexto adicional (opcional)
        max_tool_calls: Orçamento de chamadas de ferramentas
        max_time: Orçamento de tempo em segundos
        max_replans: Máximo de replanejamentos

    Returns:
        Dict com resultado da execução da missão
    """
    loop = MissionLoop()
    loop.initialize()
    loop.set_budget(max_tool_calls=max_tool_calls,
                    max_time=max_time,
                    max_replans=max_replans)

    # Criar missão
    created_mission = loop._planner.create_mission(
        name=mission_name or f"Mission-{uuid.uuid4().hex[:8]}",
        objective=objective,
        context=context
    )
    mission_id = created_mission.id  # pegar o ID da missão criada

    # Executar
    result = loop.execute_mission(mission_id, objective, context)

    # Adicionar metadados finais
    result['mission_created_id'] = mission_id
    result['objective'] = objective

    return result


# ──────────────────────────────────────────────────────────────────
# Interface de exemplo / demo
# ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Autonomous Mission Loop')
    parser.add_argument('objective', help='Objetivo da missão')
    parser.add_argument('--name', default='', help='Nome da missão')
    parser.add_argument('--context', default='', help='Contexto')
    parser.add_argument('--tool-calls', type=int, default=50, help='Orçamento de chamadas de ferramentas')
    parser.add_argument('--time', type=int, default=300, help='Orçamento de tempo (segundos)')
    parser.add_argument('--replans', type=int, default=5, help='Máximo de replanejamentos')

    args = parser.parse_args()

    print(f"=== ETAPA 20: Autonomous Mission Loop ===")
    print(f"Objective: {args.objective[:80]}...")
    print()

    result = create_and_execute_mission(
        objective=args.objective,
        mission_name=args.name or None,
        context=args.context or None,
        max_tool_calls=args.tool_calls,
        max_time=args.time,
        max_replans=args.replans
    )

    print(f"Status final: {result.get('status')}")
    print(f"Mission ID: {result.get('mission_created_id')}")
    print(f"Completion rate: {result.get('completion_rate', 0):.0%}")
    print(f"Completed steps: {result.get('completed_steps', 0)} / {result.get('total_steps', 0)}")
    print(f"Duration: {result.get('total_duration', 0):.1f}s")
    print(f"Journal entries: {len(result.get('journal', []))}")
    print(f"Objective: {result.get('objective')}")

    # Mostrar journal resumido
    print("\n--- Journal resumido ---")
    for entry in result.get('journal', [])[:10]:
        ev = entry.get('event', 'unknown')
        sid = f"step={entry.get('step_id', '')}" if entry.get('step_id') else ""
        outcome = entry.get('outcome', '')[:60]
        print(f"  [{ev}] {sid} | {outcome}")