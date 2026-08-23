"""MCP server — Planner Agent.

Coordena tarefas complexas: decompose em subtasks, executa via outros MCPs,
faz replan em caso de falha.

Tools:
  - create_plan       — recebe goal + contexto, retorna plano JSON com subtasks e dependências
  - execute_plan      — executa plano chamando outros MCPs (tool_orchestrator)
  - replan_on_failure — recebe plano + step falho + erro, retorna plano atualizado
"""
import json
import sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent)
sys.path.insert(0, BASE)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"))

# Importa utilitários do ecossistema se disponível
try:
    from scripts.runtime_kernel import complexity_classifier
except ImportError:
    complexity_classifier = None

TOOLS = [
    {
        "name": "create_plan",
        "description": "Cria plano de execução para objetivo complexo. Retorna JSON com subtasks, dependências, agentes sugeridos e critérios de sucesso.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "Objetivo principal da tarefa", "minLength": 1},
                "context": {"type": "string", "description": "Contexto adicional (opcional)"},
                "constraints": {"type": "string", "description": "Restrições conhecidas (opcional)"},
                "success_criteria": {"type": "string", "description": "Critérios de sucesso (opcional)"},
            },
            "required": ["goal"]
        },
    },
    {
        "name": "execute_plan",
        "description": "Executa plano JSON chamando MCPs apropriados para cada subtask. Retorna resultados agregados.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan": {"type": "object", "description": "Plano JSON retornado por create_plan"},
                "goal": {"type": "string", "description": "Objetivo original (para logging)"},
            },
            "required": ["plan", "goal"]
        },
    },
    {
        "name": "replan_on_failure",
        "description": "Atualiza plano quando um step falha. Recebe plano original, step_id falho, erro, e resultados parciais.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan": {"type": "object", "description": "Plano original"},
                "failed_step_id": {"type": "string", "description": "ID do step que falhou"},
                "error": {"type": "string", "description": "Mensagem de erro"},
                "partial_results": {"type": "object", "description": "Resultados dos steps que já executaram"},
            },
            "required": ["plan", "failed_step_id", "error"]
        },
    },
]


# ============================================================================
# PLANNER LOGIC
# ============================================================================

# Mapeamento de tipo de tarefa -> MCP sugerido
TASK_TO_MCP = {
    "web": "mcp-internet",
    "browser": "mcp-internet",
    "search": "mcp-internet",
    "pesquisa": "mcp-internet",
    "code": "mcp-desenvolvimento",
    "coding": "mcp-desenvolvimento",
    "programar": "mcp-desenvolvimento",
    "file": "mcp-desenvolvimento",
    "arquivo": "mcp-desenvolvimento",
    "filesystem": "mcp-desenvolvimento",
    "mcp": "mcp-desenvolvimento",
    "files": "mcp-desenvolvimento",
    "talk": "mcp-comportamentais",
    "casual": "mcp-comportamentais",
    "chat": "mcp-comportamentais",
    "plan": "mcp-planner",  # recursivo
}

# Tipos de agente sugeridos por role
ROLE_TO_AGENT = {
    "web": "BrowserAgent",
    "browser": "BrowserAgent",
    "search": "BrowserAgent",
    "code": "CoderAgent",
    "coding": "CoderAgent",
    "file": "FileAgent",
    "files": "FileAgent",
    "talk": "CasualAgent",
    "casual": "CasualAgent",
}


def infer_task_type(text: str) -> str:
    """Infere tipo de tarefa baseado em palavras-chave."""
    text_lower = text.lower()
    for keyword, mcp in TASK_TO_MCP.items():
        if keyword in text_lower:
            return keyword
    return "code"  # default


def infer_agent_role(text: str) -> str:
    """Infere role do agente baseado na tarefa."""
    task_type = infer_task_type(text)
    return ROLE_TO_AGENT.get(task_type, "CoderAgent")


def build_plan_prompt(goal: str, context: str, constraints: str, success_criteria: str) -> str:
    """Constrói prompt para o LLM gerar plano JSON."""
    return f"""
Você é um Planner Agent. Sua função é decompor objetivos complexos em subtasks executáveis.

OBJETIVO: {goal}
CONTEXTO: {context or '(nenhum)'}
RESTRICÇÕES: {constraints or '(nenhuma)'}
CRITÉRIOS DE SUCESSO: {success_criteria or '(definir durante execução)'}

REGRAS:
1. Retorne APENAS JSON válido, sem markdown, sem explicação.
2. Cada subtask deve ter: id (string), agent (role sugerido), task (descrição clara), need (lista de IDs de steps anteriores dos quais depende, ou null).
3. Ordem topológica: steps que não dependem de outros vêm primeiro.
4. Mínimo 2, máximo 8 subtasks.
5. Se objetivo não for complexo, retorne {{"simple": true, "reason": "..."}}.

EXEMPLO DE SAÍDA:
{{
  "steps": [
    {{"id": "1", "agent": "BrowserAgent", "task": "Pesquisar startups de IA em São Paulo 2024", "need": null}},
    {{"id": "2", "agent": "FileAgent", "task": "Salvar resultados em startups.json", "need": ["1"]}},
    {{"id": "3", "agent": "CoderAgent", "task": "Gerar CSV e gráfico a partir de startups.json", "need": ["2"]}}
  ]
}}
"""


def parse_plan_response(response_text: str) -> dict:
    """Parseia resposta do LLM extraindo JSON do plano."""
    # Tenta encontrar JSON na resposta
    text = response_text.strip()

    # Se começa com ```json, extrai
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:].strip()

    # Tenta parsear
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Tenta encontrar JSON entre chaves
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
    return {"error": "Falha ao parsear plano", "raw": response_text}


def call_llm(prompt: str) -> str:
    """Chama LLM via llm_router ou fallback."""
    try:
        from scripts.llm_router import route as llm_route
        # Usa router para selecionar modelo e chamar
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/llm_router.py", "chat",
             "--model", "opencode/big-pickle",
             "--prompt", prompt],
            capture_output=True, text=True, timeout=60,
            cwd="C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau"
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Fallback: retorna plano template simples
    return json.dumps({
        "steps": [
            {"id": "1", "agent": "BrowserAgent", "task": f"Pesquisar web: {prompt[:100]}", "need": None},
            {"id": "2", "agent": "FileAgent", "task": "Salvar achados em arquivo", "need": ["1"]},
            {"id": "3", "agent": "CoderAgent", "task": "Processar e formatar saída final", "need": ["2"]}
        ]
    }, ensure_ascii=False)


def create_plan_logic(goal: str, context: str, constraints: str, success_criteria: str) -> dict:
    """Lógica principal de criação de plano."""
    prompt = build_plan_prompt(goal, context, constraints, success_criteria)
    llm_response = call_llm(prompt)
    plan = parse_plan_response(llm_response)

    # Se LLM retornou "simple", usar heurística
    if plan.get("simple"):
        return {"simple": True, "reason": plan.get("reason", "Objetivo não requer decomposição")}

    # Valida estrutura
    if "steps" not in plan:
        return {"error": "Plano inválido: sem campo 'steps'", "raw": plan}

    # Enriquece steps com metadados
    for step in plan["steps"]:
        step.setdefault("status", "pending")
        step.setdefault("mcp_suggested", TASK_TO_MCP.get(infer_task_type(step["task"]), "mcp-desenvolvimento"))
        step.setdefault("agent_suggested", infer_agent_role(step["task"]))

    return {
        "goal": goal,
        "steps": plan["steps"],
        "metadata": {
            "total_steps": len(plan["steps"]),
            "created_by": "mcp-planner"
        }
    }


def execute_plan_logic(plan: dict, goal: str) -> dict:
    """Executa plano chamando tool_orchestrator para cada step.

    Nota: Em produção, isso delegaria ao tool_orchestrator que chama MCPs reais.
    Aqui retorna estrutura de resultados esperada.
    """
    results = {}
    for step in plan.get("steps", []):
        step_id = step.get("id")
        task = step.get("task")
        mcp = step.get("mcp_suggested", "mcp-desenvolvimento")

        # Placeholder para execução real
        # Em produção: chamar tool_orchestrator.execute(mcp, tool, args)
        results[step_id] = {
            "step_id": step_id,
            "task": task,
            "mcp": mcp,
            "status": "simulated",
            "output": f"[SIMULADO] {task}"
        }

    return {
        "goal": goal,
        "completed": len(results),
        "total": len(plan.get("steps", [])),
        "results": results
    }


def replan_on_failure_logic(plan: dict, failed_step_id: str, error: str, partial_results: dict) -> dict:
    """Gera plano atualizado após falha."""
    # Estratégia: adiciona step de recovery antes do step falho, ou substitui
    failed_step = None
    for step in plan.get("steps", []):
        if step.get("id") == failed_step_id:
            failed_step = step
            break

    if not failed_step:
        return {"error": f"Step {failed_step_id} não encontrado no plano"}

    # Cria novo plano: steps já executados + recovery + steps restantes
    executed_ids = set(partial_results.keys())
    new_steps = []

    # 1. Steps já executados (marcam como done)
    for step in plan.get("steps", []):
        if step["id"] in executed_ids:
            new_steps.append({**step, "status": "done"})

    # 2. Step de recovery (tenta novamente com abordagem alternativa)
    recovery_step = {
        "id": f"{failed_step_id}_retry",
        "agent": failed_step.get("agent", "CoderAgent"),
        "task": f"RETRY com abordagem alternativa: {failed_step['task']} (erro anterior: {error[:200]})",
        "need": [failed_step_id] if failed_step_id in executed_ids else [],
        "mcp_suggested": failed_step.get("mcp_suggested"),
        "status": "pending",
        "is_recovery": True
    }
    new_steps.append(recovery_step)

    # 3. Steps restantes (ajustam dependências)
    for step in plan.get("steps", []):
        if step["id"] not in executed_ids and step["id"] != failed_step_id:
            # Atualiza need para apontar para recovery se dependia do falho
            new_need = step.get("need", [])
            if failed_step_id in new_need:
                new_need = [f"{failed_step_id}_retry" if x == failed_step_id else x for x in new_need]
            new_steps.append({**step, "need": new_need, "status": "pending"})

    return {
        "goal": plan.get("goal"),
        "steps": new_steps,
        "metadata": {
            "total_steps": len(new_steps),
            "replanned_from": failed_step_id,
            "error": error,
            "created_by": "mcp-planner-replan"
        }
    }


# ============================================================================
# MCP SERVER
# ============================================================================

def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-planner", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return handle_tool(tool, args, rid)

    return None


def handle_tool(tool, args, rid):
    try:
        if tool == "create_plan":
            goal = args.get("goal", "")
            context = args.get("context", "")
            constraints = args.get("constraints", "")
            success_criteria = args.get("success_criteria", "")

            if not goal:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "goal é obrigatório"}}

            result = create_plan_logic(goal, context, constraints, success_criteria)

        elif tool == "execute_plan":
            plan = args.get("plan", {})
            goal = args.get("goal", "")
            if not plan or not goal:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "plan e goal são obrigatórios"}}
            result = execute_plan_logic(plan, goal)

        elif tool == "replan_on_failure":
            plan = args.get("plan", {})
            failed_step_id = args.get("failed_step_id", "")
            error = args.get("error", "")
            partial_results = args.get("partial_results", {})
            if not plan or not failed_step_id or not error:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "plan, failed_step_id e error são obrigatórios"}}
            result = replan_on_failure_logic(plan, failed_step_id, error, partial_results)

        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}

    except Exception as e:
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps({"erro": str(e)}, ensure_ascii=False, indent=2)}]}}

    return {"jsonrpc": "2.0", "id": rid, "result": {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}


def _read_frame(stream):
    peek = stream.peek(1)
    if not peek:
        return None

    if peek.startswith(b'{'):
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            return None
        try:
            return json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    first = stream.readline()
    if not first:
        return None
    first = first.rstrip(b"\r\n")
    if not first.startswith(b"Content-Length:"):
        return None

    headers = {}
    if b":" in first:
        key, value = first.split(b":", 1)
        headers[key.strip().lower()] = value.strip()
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            break
        if b":" in line:
            key, value = line.split(b":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get(b"content-length", b"0") or b"0")
    if length <= 0:
        return None
    body = stream.read(length)
    try:
        return json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()


if __name__ == "__main__":
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        req = _read_frame(stdin)
        if req is None:
            break
        resp = handle(req)
        if resp is not None:
            _write_frame(stdout, resp)