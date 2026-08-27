"""Council Orchestrator - Ponte entre deliberação do conselho e execução.

Recebe um pedido do usuario, roda o conselho com LLM real, e gera
um plano de execucao estruturado que pode ser despachado para:
  - LER (tarefas autonomas)
  - parallel_dispatcher (tarefas paralelas)
  - Task tool do opencode (execucao direta)

Uso:
  python council_orchestrator.py "Adicionar autenticacao JWT na API"
  python council_orchestrator.py "Refatorar modulo de pagamentos" --context "FastAPI, 5 endpoints"
  python council_orchestrator.py "Criar dashboard" --dispatch
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
sys.path.insert(0, SCRIPTS)

from agent_council import AgentCouncil, AgentRole, council


class CouncilOrchestrator:
    """Orquestra deliberacao + geracao de plano + despacho."""

    def __init__(self):
        self.council = council

    def plan(
        self,
        request: str,
        context: str = "",
        dispatch: bool = False,
        max_rounds: int = 2,
    ) -> Dict[str, Any]:
        """Executa pipeline completo: delibera + planeja + despacha.

        Args:
            request: Pedido do usuario
            context: Contexto adicional
            dispatch: Se True, despacha tarefas automaticamente
            max_rounds: Maximo de rodadas de deliberacao

        Returns:
            Dict com deliberacao, plano e resultado do despacho
        """
        # 1. Deliberacao com LLM real
        print(f"[Orchestrator] Deliberando sobre: {request[:80]}...")
        deliberation = self.council.deliberate(
            topic=request,
            context=context or "Sem contexto adicional.",
            max_rounds=max_rounds,
            use_llm=True,
        )

        # 2. Gera plano de execucao estruturado
        execution_plan = self._generate_plan(deliberation, request, context)

        # 3. Despacha se solicitado
        dispatch_result = None
        if dispatch and execution_plan["tasks"]:
            dispatch_result = self._dispatch(execution_plan)

        return {
            "deliberation_id": deliberation.id,
            "topic": request,
            "status": deliberation.status.value,
            "consensus": deliberation.consensus_reached,
            "votes": deliberation.structured_output.get("votes", {}),
            "execution_plan": execution_plan,
            "dispatch_result": dispatch_result,
            "recommendation": deliberation.final_recommendation,
        }

    def _generate_plan(
        self, deliberation, request: str, context: str
    ) -> Dict[str, Any]:
        """Converte deliberacao em plano de execucao estruturado."""
        so = deliberation.structured_output
        approved = so.get("approved", False)
        action_items = so.get("action_items", [])
        concerns = so.get("concerns", [])
        suggestions = so.get("suggestions", [])

        # Classifica a tarefa
        task_type = self._classify_task(request)

        # Gera tarefas executaveis a partir dos action items
        tasks = self._action_items_to_tasks(action_items, request, task_type)

        # Identifica riscos bloqueantes
        blockers = self._identify_blockers(concerns)

        # Monta plano
        plan = {
            "approved": approved,
            "task_type": task_type,
            "total_tasks": len(tasks),
            "tasks": tasks,
            "blockers": blockers,
            "suggestions": suggestions[:5],
            "concerns": concerns[:5],
            "parallelizable": self._can_parallelize(tasks),
            "estimated_complexity": self._estimate_complexity(tasks, concerns),
        }

        return plan

    def _classify_task(self, request: str) -> str:
        """Classifica o tipo de tarefa."""
        request_lower = request.lower()
        if any(w in request_lower for w in ["criar", "novo", "adicionar", "implementar", "desenvolver"]):
            return "novo_recurso"
        elif any(w in request_lower for w in ["corrigir", "bug", "erro", "fix"]):
            return "correcao"
        elif any(w in request_lower for w in ["refatorar", "melhorar", "otimizar", "limpar"]):
            return "refatoracao"
        elif any(w in request_lower for w in ["testar", "teste", "validar"]):
            return "teste"
        elif any(w in request_lower for w in ["documentar", "documentacao", "ler"]):
            return "documentacao"
        elif any(w in request_lower for w in ["deploy", "publicar", "lançar"]):
            return "deploy"
        else:
            return "geral"

    def _action_items_to_tasks(
        self, action_items: List[str], request: str, task_type: str
    ) -> List[Dict[str, Any]]:
        """Converte action items em tarefas executaveis."""
        tasks = []
        for i, item in enumerate(action_items):
            task_id = f"task-{i+1}"
            task = {
                "id": task_id,
                "description": item,
                "status": "pending",
                "type": task_type,
                "write_files": self._infer_files(item),
                "depends_on": [],
                "command": self._suggest_command(item, task_type),
            }
            tasks.append(task)

        # Adiciona dependencias baseadas em ordem logica
        self._add_logical_dependencies(tasks)

        return tasks

    def _infer_files(self, action: str) -> List[str]:
        """Tenta inferir quais arquivos serao afetados."""
        action_lower = action.lower()
        files = []
        if "security" in action_lower or "auth" in action_lower:
            files.append("security.py")
        if "middleware" in action_lower:
            files.append("middleware.py")
        if "endpoint" in action_lower or "rota" in action_lower:
            files.append("routes.py")
        if "test" in action_lower:
            files.append("test_*.py")
        if "config" in action_lower or ".env" in action_lower:
            files.append(".env")
        if "requirements" in action_lower:
            files.append("requirements.txt")
        if "document" in action_lower:
            files.append("README.md")
        return files

    def _suggest_command(self, action: str, task_type: str) -> str:
        """Sugere comando de execucao."""
        action_lower = action.lower()
        if "test" in action_lower:
            return "python -m pytest"
        if "install" in action_lower or "requirements" in action_lower:
            return "pip install -r requirements.txt"
        if "lint" in action_lower:
            return "python -m flake8"
        return ""

    def _add_logical_dependencies(self, tasks: List[Dict]):
        """Adiciona dependencias logicas entre tarefas."""
        for i, task in enumerate(tasks):
            desc_lower = task["description"].lower()
            # Tarefas de teste dependem de implementacao
            if "test" in desc_lower:
                for j, other in enumerate(tasks):
                    if j != i and "test" not in other["description"].lower():
                        if other["id"] not in task["depends_on"]:
                            task["depends_on"].append(other["id"])

    def _can_parallelize(self, tasks: List[Dict]) -> bool:
        """Verifica se ha tarefas que podem rodar em paralelo."""
        independent = [t for t in tasks if not t["depends_on"]]
        return len(independent) > 1

    def _estimate_complexity(self, tasks: List[Dict], concerns: List[str]) -> str:
        """Estima complexidade da tarefa."""
        n = len(tasks)
        n_concerns = len(concerns)
        if n <= 2 and n_concerns <= 3:
            return "baixa"
        elif n <= 5 and n_concerns <= 6:
            return "media"
        else:
            return "alta"

    def _identify_blockers(self, concerns: List[str]) -> List[str]:
        """Identifica preocupacoes que podem bloquear execucao."""
        blocker_keywords = [
            "seguranca", "permissao", "acesso", "token", "chave",
            "irreversivel", "destructivo", "perda de dados",
        ]
        blockers = []
        for c in concerns:
            if any(kw in c.lower() for kw in blocker_keywords):
                blockers.append(c)
        return blockers

    def _dispatch(self, plan: Dict) -> Dict[str, Any]:
        """Despacha tarefas para execucao."""
        tasks = plan.get("tasks", [])
        if not tasks:
            return {"dispatched": 0, "method": "none"}

        # Para tarefas simples, gera formato para LER
        if len(tasks) <= 2:
            return self._dispatch_to_ler(tasks)

        # Para tarefas paralelas, usa parallel_dispatcher format
        if plan.get("parallelizable"):
            return self._dispatch_parallel(tasks)

        # Fallback: lista sequencial
        return self._dispatch_sequential(tasks)

    def _dispatch_to_ler(self, tasks: List[Dict]) -> Dict:
        """Gera formato de saida para LER."""
        mission = "; ".join(t["description"] for t in tasks)
        return {
            "method": "ler",
            "mission": mission,
            "tasks_count": len(tasks),
            "command": f'ler "{mission}"',
        }

    def _dispatch_parallel(self, tasks: List[Dict]) -> Dict:
        """Gera formato para parallel_dispatcher."""
        dispatcher_tasks = []
        for t in tasks:
            dispatcher_tasks.append({
                "name": t["id"],
                "command": t.get("command", f'echo "{t["description"]}"'),
                "read_files": [],
                "write_files": t.get("write_files", []),
                "depends_on": t.get("depends_on", []),
            })
        return {
            "method": "parallel_dispatcher",
            "tasks_count": len(dispatcher_tasks),
            "tasks_json": dispatcher_tasks,
            "command": f'python scripts/parallel_dispatcher.py tasks.json',
        }

    def _dispatch_sequential(self, tasks: List[Dict]) -> Dict:
        """Gera lista sequencial de comandos."""
        commands = []
        for t in tasks:
            cmd = t.get("command", "")
            if cmd:
                commands.append(cmd)
        return {
            "method": "sequential",
            "tasks_count": len(tasks),
            "commands": commands,
        }


orchestrator = CouncilOrchestrator()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Council Orchestrator - Delibera e planeja execucao'
    )
    parser.add_argument('request', help='Pedido do usuario')
    parser.add_argument('--context', default='', help='Contexto adicional')
    parser.add_argument('--dispatch', action='store_true', help='Despacha tarefas')
    parser.add_argument('--rounds', type=int, default=2, help='Max rodadas de deliberacao')
    parser.add_argument('--json', action='store_true', help='Saida em JSON')

    args = parser.parse_args()

    result = orchestrator.plan(
        request=args.request,
        context=args.context,
        dispatch=args.dispatch,
        max_rounds=args.rounds,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"COUNCIL ORCHESTRATOR - Plano de Execucao")
        print(f"{'='*60}")
        print(f"Topico: {result['topic']}")
        print(f"Status: {result['status']}")
        print(f"Consenso: {result['consensus']}")
        print(f"Votos: {result['votes']}")

        plan = result["execution_plan"]
        print(f"\nPlano:")
        print(f"  Tipo: {plan['task_type']}")
        print(f"  Tarefas: {plan['total_tasks']}")
        print(f"  Complexidade: {plan['estimated_complexity']}")
        print(f"  Paralelizavel: {plan['parallelizable']}")

        if plan["blockers"]:
            print(f"\n  BLOQUEADORES:")
            for b in plan["blockers"]:
                print(f"    ! {b}")

        if plan["tasks"]:
            print(f"\n  Tarefas:")
            for t in plan["tasks"]:
                deps = f" (depende de: {', '.join(t['depends_on'])})" if t["depends_on"] else ""
                print(f"    [{t['id']}] {t['description']}{deps}")

        if result["dispatch_result"]:
            dr = result["dispatch_result"]
            print(f"\n  Despacho: {dr['method']} ({dr['tasks_count']} tarefas)")

        print(f"\n{'='*60}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
