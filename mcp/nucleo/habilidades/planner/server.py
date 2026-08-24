# Complete rewrite of server.py with fixed f-string
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
import os
import asyncio
import subprocess
import shlex
import re
from pathlib import Path

BASE = str(Path(__file__).resolve().parent)
sys.path.insert(0, BASE)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

# Importa utilitários do ecossistema se disponível
try:
    from scripts.runtime_kernel import complexity_classifier
except ImportError:
    complexity_classifier = None

TOOLS = [
    {
        "name": "create_plan",
        "description": "Cria plano de execução para objetivo complexo. Retorna plano JSON com subtasks, dependências, agentes sugeridos e critérios de sucesso.",
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
        "description": "Atualiza plano quando step falha. Recebe plano original, step_id falho, erro, e resultados parciais.",
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


# Mapeamento de tipo de tarefa -> MCP sugerido
TASK_TO_MCP = {
    "web": "mcp-internet",
    "browser": "mcp-internet",
    "search": "mcp-internet",
    "pesquisa": "mcp-internet",
    "code": "mcp-desenvolvimento",
    "coding": "mcp-desenvolvimento",
    "programar": "mcp-desenvolvimento",
    "file": "mcp-dev-tools",
    "arquivo": "mcp-dev-tools",
    "write_file": "mcp-dev-tools",
    "read_file": "mcp-dev-tools",
    "list_files": "mcp-dev-tools",
    "glob": "mcp-dev-tools",
    "delete_file": "mcp-dev-tools",
    "execute_python": "mcp-dev-tools",
    "execute_shell": "mcp-dev-tools",
    "filesystem": "mcp-dev-tools",
    "mcp": "mcp-desenvolvimento",
    "files": "mcp-dev-tools",
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
    "chat": "CasualAgent",
    "plan": "FileAgent",  # default para planejamento
}


def _extract_user_goal(prompt: str) -> str:
    """Extrai o objetivo do usuário do prompt do Planner Agent."""
    import re
    match = re.search(r'OBJETIVO:\s*([^\n]+)', prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: pega a primeira linha que não parece instrução do sistema
    lines = prompt.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('VOCÊ') and not line.startswith('REGRAS') and not line.startswith('EXEMPLO') and not line.startswith('{') and len(line) > 10:
            return line
    return ""


def _generate_smart_fallback_plan(prompt: str) -> str:
    """Gera plano inteligente baseado no tipo de tarefa detectado no objetivo do usuário."""
    import re
    # Extrai o objetivo real do usuário (ignora o system prompt)
    user_goal = _extract_user_goal(prompt)
    prompt_lower = user_goal.lower() if user_goal else prompt.lower()
    
    # Detecta tipo de tarefa
    task_type = "generic"
    if any(kw in prompt_lower for kw in ["pesquis", "busca", "search", "web", "internet", "startup", "empresa", "mercado"]):
        task_type = "research"
    elif any(kw in prompt_lower for kw in ["code", "programa", "script", "python", "java", "go", "rust", "javascript", "typescript", "api", "servidor", "web app", "frontend", "backend"]):
        task_type = "coding"
    elif any(kw in prompt_lower for kw in ["arquivo", "file", "salva", "save", "csv", "json", "excel", "planilha", "gráfico", "chart", "plot"]):
        task_type = "file_processing"
    elif any(kw in prompt_lower for kw in ["planeje", "plan", "organize", "organizar", "estratégia", "roadmap", "cronograma"]):
        task_type = "planning"
    elif any(kw in prompt_lower for kw in ["audit", "auditoria", "bug", "erro", "review", "revisão", "código", "code review"]):
        task_type = "audit"
    
    # Planos por tipo de tarefa
    plans = {
        "research": {
            "steps": [
                {"id": "1", "agent": "BrowserAgent", "task": f"Pesquisar web: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "FileAgent", "task": "Extrair e estruturar dados encontrados em formato estruturado (JSON/CSV)", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Gerar relatório final com insights, fontes e formatação solicitada", "need": ["2"]}
            ]
        },
        "coding": {
            "steps": [
                {"id": "1", "agent": "CoderAgent", "task": f"Analisar requisitos e projetar arquitetura: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "CoderAgent", "task": "Implementar código principal seguindo boas práticas e testes", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Escrever testes unitários e de integração, validar funcionamento", "need": ["2"]},
                {"id": "4", "agent": "FileAgent", "task": "Organizar arquivos, documentar API e criar README", "need": ["3"]}
            ]
        },
        "file_processing": {
            "steps": [
                {"id": "1", "agent": "FileAgent", "task": f"Criar arquivo e salvar conteúdo: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "CoderAgent", "task": "Processar, transformar e validar dados conforme especificação", "need": ["1"]},
                {"id": "3", "agent": "FileAgent", "task": "Listar arquivos e validar resultado", "need": ["2"]}
            ]
        },
        "planning": {
            "steps": [
                {"id": "1", "agent": "CoderAgent", "task": f"Analisar objetivo e decompor em marcos: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "BrowserAgent", "task": "Pesquisar referências, benchmarks e melhores práticas", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Criar roadmap detalhado com marcos, dependências e riscos", "need": ["2"]},
                {"id": "4", "agent": "FileAgent", "task": "Gerar documento de planejamento executável (markdown/JSON)", "need": ["3"]}
            ]
        },
        "audit": {
            "steps": [
                {"id": "1", "agent": "CoderAgent", "task": f"Escanear código/arquitetura alvo: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "CoderAgent", "task": "Aplicar pipeline de auditoria (fluxo, ferramentas autoritativas, correção no fonte)", "need": ["1"]},
                {"id": "3", "agent": "FileAgent", "task": "Gerar relatório de auditoria com achados, riscos e plano de correção", "need": ["2"]}
            ]
        },
        "generic": {
            "steps": [
                {"id": "1", "agent": "BrowserAgent", "task": f"Pesquisar contexto: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "FileAgent", "task": "Salvar achados em arquivo estruturado", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Processar e formatar saída final", "need": ["2"]}
            ]
        }
    }
    
    plan = plans.get(task_type, plans["generic"])
    return json.dumps(plan, ensure_ascii=False)


def _extract_user_goal(prompt: str) -> str:
    """Extrai o objetivo do usuário do prompt do Planner Agent."""
    import re
    match = re.search(r'OBJETIVO:\s*([^\n]+)', prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: pega a primeira linha que não parece instrução do sistema
    lines = prompt.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('VOCÊ') and not line.startswith('REGRAS') and not line.startswith('EXEMPLO') and not line.startswith('{') and len(line) > 10:
            return line
    return ""


def call_llm(prompt: str) -> str:
    """Chama LLM via opencode run (com fallback inteligente se falhar)."""
    import subprocess
    import shlex
    import json

    # Tenta opencode run com --interactive false
    escaped_prompt = shlex.quote(prompt)
    cmd = [
        "opencode", "run",
        "--model", "opencode/big-pickle",
        "--interactive", "false",
        "--print-logs",
        escaped_prompt
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=180,
            cwd="C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau"
        )
        if result.returncode == 0 and result.stdout.strip():
            # Extrai apenas a resposta do agente (última linha não-vazia que não seja log)
            lines = result.stdout.strip().split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith('timestamp=') and not line.startswith('panic') and not line.startswith('oh no:') and not line.startswith('Segmentation fault'):
                    return line
    except Exception:
        pass

    # Fallback inteligente: gera plano baseado no tipo de tarefa detectado
    return _generate_smart_fallback_plan(prompt)


def _generate_smart_fallback_plan(prompt: str) -> str:
    """Gera plano inteligente baseado no tipo de tarefa detectado no prompt."""
    # Extrai o objetivo real do usuário (ignora o system prompt)
    user_goal = _extract_user_goal(prompt)
    prompt_lower = user_goal.lower() if user_goal else prompt.lower()
    
    # Detecta tipo de tarefa
    task_type = "generic"
    if any(kw in prompt_lower for kw in ["pesquis", "busca", "search", "web", "internet", "startup", "empresa", "mercado"]):
        task_type = "research"
    elif any(kw in prompt_lower for kw in ["code", "programa", "script", "python", "java", "go", "rust", "javascript", "typescript", "api", "servidor", "web app", "frontend", "backend"]):
        task_type = "coding"
    elif any(kw in prompt_lower for kw in ["arquivo", "file", "salva", "save", "csv", "json", "excel", "planilha", "gráfico", "chart", "plot"]):
        task_type = "file_processing"
    elif any(kw in prompt_lower for kw in ["planeje", "plan", "organize", "organizar", "estratégia", "roadmap", "cronograma"]):
        task_type = "planning"
    elif any(kw in prompt_lower for kw in ["audit", "auditoria", "bug", "erro", "review", "revisão", "código", "code review"]):
        task_type = "audit"
    
    # Planos por tipo de tarefa
    plans = {
        "research": {
            "steps": [
                {"id": "1", "agent": "BrowserAgent", "task": f"Pesquisar web: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "FileAgent", "task": "Extrair e estruturar dados encontrados em formato estruturado (JSON/CSV)", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Gerar relatório final com insights, fontes e formatação solicitada", "need": ["2"]}
            ]
        },
        "coding": {
            "steps": [
                {"id": "1", "agent": "CoderAgent", "task": f"Analisar requisitos e projetar arquitetura: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "CoderAgent", "task": "Implementar código principal seguindo boas práticas e testes", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Escrever testes unitários e de integração, validar funcionamento", "need": ["2"]},
                {"id": "4", "agent": "FileAgent", "task": "Organizar arquivos, documentar API e criar README", "need": ["3"]}
            ]
        },
        "file_processing": {
            "steps": [
                {"id": "1", "agent": "FileAgent", "task": f"Criar arquivo e salvar conteúdo: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "CoderAgent", "task": "Processar, transformar e validar dados conforme especificação", "need": ["1"]},
                {"id": "3", "agent": "FileAgent", "task": "Listar arquivos e validar resultado", "need": ["2"]}
            ]
        },
        "planning": {
            "steps": [
                {"id": "1", "agent": "CoderAgent", "task": f"Analisar objetivo e decompor em marcos: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "BrowserAgent", "task": "Pesquisar referências, benchmarks e melhores práticas", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Criar roadmap detalhado com marcos, dependências e riscos", "need": ["2"]},
                {"id": "4", "agent": "FileAgent", "task": "Gerar documento de planejamento executável (markdown/JSON)", "need": ["3"]}
            ]
        },
        "audit": {
            "steps": [
                {"id": "1", "agent": "CoderAgent", "task": f"Escanear código/arquitetura alvo: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "CoderAgent", "task": "Aplicar pipeline de auditoria (fluxo, ferramentas autoritativas, correção no fonte)", "need": ["1"]},
                {"id": "3", "agent": "FileAgent", "task": "Gerar relatório de auditoria com achados, riscos e plano de correção", "need": ["2"]}
            ]
        },
        "generic": {
            "steps": [
                {"id": "1", "agent": "BrowserAgent", "task": f"Pesquisar contexto: {user_goal[:200]}", "need": None},
                {"id": "2", "agent": "FileAgent", "task": "Salvar achados em arquivo estruturado", "need": ["1"]},
                {"id": "3", "agent": "CoderAgent", "task": "Processar e formatar saída final", "need": ["2"]}
            ]
        }
    }
    
    plan = plans.get(task_type, plans["generic"])
    return json.dumps(plan, ensure_ascii=False)


def _extract_user_goal(prompt: str) -> str:
    """Extrai o objetivo do usuário do prompt do Planner Agent."""
    import re
    match = re.search(r'OBJETIVO:\s*([^\n]+)', prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: pega a primeira linha que não parece instrução do sistema
    lines = prompt.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('VOCÊ') and not line.startswith('REGRAS') and not line.startswith('EXEMPLO') and not line.startswith('{') and len(line) > 10:
            return line
    return ""


def call_llm(prompt: str) -> str:
    """Chama LLM via opencode run (com fallback inteligente se falhar)."""
    import subprocess
    import shlex
    import json

    # Tenta opencode run com --interactive false
    escaped_prompt = shlex.quote(prompt)
    cmd = [
        "opencode", "run",
        "--model", "opencode/big-pickle",
        "--interactive", "false",
        "--print-logs",
        escaped_prompt
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=180,
            cwd="C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau"
        )
        if result.returncode == 0 and result.stdout.strip():
            # Extrai apenas a resposta do agente (última linha não-vazia que não seja log)
            lines = result.stdout.strip().split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith('timestamp=') and not line.startswith('panic') and not line.startswith('oh no:') and not line.startswith('Segmentation fault'):
                    return line
    except Exception:
        pass

    # Fallback inteligente: gera plano baseado no tipo de tarefa detectado
    return _generate_smart_fallback_plan(prompt)


def parse_plan_response(response_text: str) -> dict:
    """Parseia resposta do LLM extraindo JSON do plano."""
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


def build_plan_prompt(goal: str, context: str, constraints: str, success_criteria: str) -> str:
    """Constrói prompt para o Planner Agent."""
    return f"""Você é um Planner Agent. Sua função é decompor objetivos complexos em subtasks executáveis.

OBJETIVO: {goal}
CONTEXTO: {context or '(nenhum)'}
RESTRICÇÕES: {constraints or '(nenhuma)'}
CRITÉRIOS DE SUCESSO: {success_criteria or '(definir durante execução)'}

REGRAS:
1. Retorne APENAS JSON válido, sem markdown, sem explicação.
2. Cada subtask deve ter: id (string), agent (role sugerido), task (descrição clara), need (lista de IDs de steps anteriores dos quais depende, ou null).
3. Ordem topológica: steps que não dependem de outros vêm primeiro.
4. Mínimo 2, máximo 8 subtasks.
5. Se objetivo não for complexo, retorne {{\"simple\": true, \"reason\": \"...\"}}.

EXEMPLO DE SAÍDA:
{{{{
  "steps": [
    {{{{"id": "1", "agent": "BrowserAgent", "task": "Pesquisar web: ...", "need": null}}}},
    {{{{"id": "2", "agent": "FileAgent", "task": "Salvar achados em arquivo", "need": ["1"]}}}},
    {{{{"id": "3", "agent": "CoderAgent", "task": "Processar e formatar saída final", "need": ["2"]}}}}
  ]
}}}}
"""


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


def _build_tool_args(agent: str, task: str, step: dict) -> dict:
    """Constrói argumentos para a tool (skill) baseada no agente/tarefa.

    As skills do mcp-dev-tools esperam parâmetros específicos:
    - write_file: path, content
    - read_file: path, encoding
    - list_files: pattern, recursive
    - glob: pattern
    - delete_file: path
    - execute_python: code, timeout_sec
    - execute_shell: command, cwd, timeout_sec
    """
    import re
    
    tool_name = _infer_tool_name(agent, task)
    
    # Para skills que esperam "argumentos" (formato antigo)
    if tool_name.startswith("skill-"):
        return {"argumentos": task, "step_id": step.get("id")}
    
    # Para tools do mcp-dev-tools com parâmetros estruturados
    if tool_name == "write_file":
        # Tenta extrair path e content da task
        # Formato esperado: "Criar arquivo hello.txt com conteúdo Hello World"
        path_match = re.search(r'(?:arquivo|arquivo|file)\s+([^\s]+\.\w+)', task, re.IGNORECASE)
        # Tenta extrair conteúdo entre aspas ou após "conteúdo:" (com ou sem acento)
        content_match = re.search(r'(?:conte[úu]do|content|content)[:\s]+(["\'])([^\1]+)\1', task, re.IGNORECASE)
        if not content_match:
            content_match = re.search(r'(?:conte[úu]do|content|content)[:\s]+([^,\.]+)', task, re.IGNORECASE)
        
        path = path_match.group(1) if path_match else "output.txt"
        content = content_match.group(2).strip() if content_match and content_match.lastindex >= 2 else (content_match.group(1).strip() if content_match else task)
        
        return {"path": path, "content": content, "step_id": step.get("id")}
    
    elif tool_name == "read_file":
        path_match = re.search(r'(?:arquivo|file)\s+([^\s]+\.\w+)', task, re.IGNORECASE)
        path = path_match.group(1) if path_match else "output.txt"
        return {"path": path, "encoding": "utf-8", "step_id": step.get("id")}
    
    elif tool_name == "list_files":
        return {"pattern": "**/*", "recursive": True, "step_id": step.get("id")}
    
    elif tool_name == "glob":
        pattern_match = re.search(r'(?:padrão|pattern|glob)\s+([^\s,]+)', task, re.IGNORECASE)
        pattern = pattern_match.group(1) if pattern_match else "**/*"
        return {"pattern": pattern, "step_id": step.get("id")}
    
    elif tool_name == "delete_file":
        path_match = re.search(r'(?:arquivo|file)\s+([^\s]+\.\w+)', task, re.IGNORECASE)
        path = path_match.group(1) if path_match else "output.txt"
        return {"path": path, "step_id": step.get("id")}
    
    elif tool_name == "execute_python":
        # Extrai código Python da task se possível
        code_match = re.search(r'(?:código|code|python)[:]\s*(.+)', task, re.IGNORECASE | re.DOTALL)
        code = code_match.group(1).strip() if code_match else f"# Task: {task}\nprint('Task executed')"
        return {"code": code, "timeout_sec": 30, "step_id": step.get("id")}
    
    elif tool_name == "execute_shell":
        cmd_match = re.search(r'(?:comando|command|shell)[:]\s*(.+)', task, re.IGNORECASE)
        command = cmd_match.group(1).strip() if cmd_match else "echo 'Task executed'"
        return {"command": command, "cwd": ".", "timeout_sec": 60, "step_id": step.get("id")}
    
    # Fallback para skills antigas
    return {"argumentos": task, "step_id": step.get("id")}


def _infer_tool_name(agent: str, task: str) -> str:
    """Infere nome da tool (skill) baseado no agente e tarefa.

    As tools reais nos MCPs seguem o padrão: skill-{nome-da-skill}
    Para mcp-dev-tools, as tools são: read_file, write_file, list_files, glob, delete_file, execute_python, execute_shell
    """
    task_lower = task.lower()

    if agent in ("BrowserAgent", "browser"):
        if any(kw in task_lower for kw in ["pesquis", "busca", "search", "navega", "acessa", "navegaç"]):
            return "skill-busca-web"
        elif any(kw in task_lower for kw in ["clima", "tempo", "weather"]):
            return "skill-clima-api"
        elif any(kw in task_lower for kw in ["endereço", "endereco", "geolocal", "localiza"]):
            return "skill-endereco-geo"
        elif any(kw in task_lower for kw in ["navega", "click", "clic", "form", "preench"]):
            return "skill-navegacao-perita"
        return "skill-busca-web"

    elif agent in ("FileAgent", "file"):
        # mcp-dev-tools tem tools de arquivo reais
        if any(kw in task_lower for kw in ["salva", "save", "escreve", "write", "cria", "create", "escrever"]):
            return "write_file"
        elif any(kw in task_lower for kw in ["lê", "read", "carrega", "ler", "ler arquivo"]):
            return "read_file"
        elif any(kw in task_lower for kw in ["lista", "list", "ls", "diretório", "directory"]):
            return "list_files"
        elif any(kw in task_lower for kw in ["glob", "padrão", "pattern", "*.py", "*.js"]):
            return "glob"
        elif any(kw in task_lower for kw in ["apaga", "delete", "remove", "rm"]):
            return "delete_file"
        return "skill-busca-web"  # fallback

    elif agent in ("CoderAgent", "code", "coding"):
        if any(kw in task_lower for kw in ["audit", "auditoria", "revis", "review", "bug", "erro"]):
            return "skill-auditoria-de-codigo"
        elif any(kw in task_lower for kw in ["cli", "command", "terminal", "bash", "shell", "comando"]):
            return "execute_shell"
        elif any(kw in task_lower for kw in ["test", "teste", "pytest", "unit"]):
            return "skill-tdd-workflow"
        elif any(kw in task_lower for kw in ["refator", "refactor", "clean code", "limp"]):
            return "skill-refactoring-patterns"
        elif any(kw in task_lower for kw in ["docker", "container", "deploy"]):
            return "skill-docker-patterns"
        elif any(kw in task_lower for kw in ["api", "rest", "endpoint"]):
            return "skill-api-design"
        elif any(kw in task_lower for kw in ["segurança", "security", "auth", "authn"]):
            return "skill-security-review"
        elif any(kw in task_lower for kw in ["python", "script", "código", "code", "executa", "run"]):
            return "execute_python"
        return "skill-auditoria-de-codigo"

    elif agent in ("CasualAgent", "talk", "casual"):
        return "skill-busca-web"

    return "skill-busca-web"


def _call_mcp_tool(mcp_name: str, tool_name: str, arguments: dict) -> dict:
    """Chama uma tool em um servidor MCP via JSON-RPC stdio."""
    import subprocess
    import json
    import os

    # Mapeia nome do MCP para caminho do servidor principal (não skills individuais)
    mcp_paths = {
        "mcp-internet": "mcp/internet/server.py",
        "mcp-desenvolvimento": "mcp/desenvolvimento/server.py",
        "mcp-comportamentais": "mcp/comportamentais/server.py",
        "mcp-memoria": "mcp/memoria/server.py",
        "mcp-multimidia": "mcp/multimidia/server.py",
        "mcp-android": "mcp/android/server.py",
        "mcp-compreensao-pedidos": "mcp/nucleo/habilidades/compreensao-pedidos/server.py",
        "mcp-observabilidade": "mcp/nucleo/habilidades/observabilidade/server.py",
        "mcp-planner": "mcp/nucleo/habilidades/planner/server.py",
        "mcp-dev-tools": "mcp/desenvolvimento/habilidades/dev-tools/server.py",
        "eco-knowledge": "scripts/mcp-knowledge-server.py",
        "eco-obsidian": "scripts/mcp-obsidian-server.py",
    }

    server_path = mcp_paths.get(mcp_name)
    if not server_path:
        return {"error": f"MCP desconhecido: {mcp_name}", "available": list(mcp_paths.keys())}

    full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), server_path)
    if not os.path.exists(full_path):
        return {"error": f"Servidor MCP não encontrado: {full_path}"}

    # Request tools/call
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    try:
        result = subprocess.run(
            [sys.executable, full_path],
            input=json.dumps(req) + "\n",
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(full_path)
        )
        if result.returncode != 0:
            return {"error": f"MCP {mcp_name} falhou: {result.stderr[:500]}"}

        # Parse response (line-delimited JSON)
        for line in result.stdout.strip().split('\n'):
            try:
                resp = json.loads(line)
                if resp.get('id') == 1 and 'result' in resp:
                    content = resp['result'].get('content', [])
                    if content and content[0].get('type') == 'text':
                        return json.loads(content[0]['text'])
            except json.JSONDecodeError:
                continue
            except Exception:
                continue
        return {"error": "Resposta MCP inválida", "raw": result.stdout}
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout chamando MCP {mcp_name}"}
    except Exception as e:
        return {"error": f"Erro chamando MCP {mcp_name}: {str(e)}"}


def execute_plan_logic(plan: dict, goal: str) -> dict:
    """Executa plano completo com replan automático em falhas."""
    from scripts.tool_orchestrator import orchestrator

    results = {}
    completed = 0

    for step in plan.get("steps", []):
        step_id = step.get("id")
        task = step.get("task")
        mcp = step.get("mcp_suggested", "mcp-desenvolvimento")
        agent = step.get("agent", "CoderAgent")  # usa o agent do plano

        # Determina qual tool chamar no MCP baseado no agente/tarefa
        tool_name = _infer_tool_name(agent, task)

        # Prepara argumentos para a tool
        args = _build_tool_args(agent, task, step)

        # Função que o orchestrator vai executar
        def mcp_call_fn(**kwargs):
            return _call_mcp_tool(mcp, tool_name, kwargs)

        # Executa via orchestrator (retry, circuit breaker, timeout, métricas)
        try:
            output = orchestrator.execute(
                tool_name=f"{mcp}.{tool_name}",
                fn=mcp_call_fn,
                args=args,
                timeout=120.0,
                max_retries=2,
                backoff_base=2.0,
                metadata={
                    "step_id": step_id,
                    "task": task,
                    "agent": agent,
                    "mcp": mcp,
                    "goal": goal
                }
            )
            results[step_id] = {
                "step_id": step_id,
                "task": task,
                "mcp": mcp,
                "tool": tool_name,
                "agent": agent,
                "status": "success",
                "output": output
            }
            completed += 1
        except Exception as e:
            results[step_id] = {
                "step_id": step_id,
                "task": task,
                "mcp": mcp,
                "tool": tool_name,
                "agent": agent,
                "status": "failed",
                "error": str(e)
            }
            # Para execução em caso de falha (replan será feito pelo caller)
            break

    return {
        "goal": goal,
        "completed": completed,
        "total": len(plan.get("steps", [])),
        "results": results
    }


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
        return asyncio.run(handle_tool_async(tool, args, rid))

    return None


async def handle_tool_async(tool, args, rid):
    try:
        if tool == "create_plan":
            goal = args.get("goal", "")
            context = args.get("context", "")
            constraints = args.get("constraints", "")
            success_criteria = args.get("success_criteria", "")

            if not goal:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "goal é obrigatório"}}

            return create_plan_logic(goal, context, constraints, success_criteria)

        elif tool == "execute_plan":
            plan = args.get("plan", {})
            goal = args.get("goal", "")
            if not plan or not goal:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "plan e goal são obrigatórios"}}
            return execute_plan_logic(plan, goal)

        elif tool == "replan_on_failure":
            plan = args.get("plan", {})
            failed_step_id = args.get("failed_step_id", "")
            error = args.get("error", "")
            partial_results = args.get("partial_results", {})
            if not plan or not failed_step_id or not error:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "plan, failed_step_id e error são obrigatórios"}}
            return replan_on_failure_logic(plan, failed_step_id, error, partial_results)
        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)}]}
        }



def replan_on_failure_logic(plan, failed_step_id, error, partial_results):
    steps = plan.get("steps", [])
    failed_idx = None
    for i, step in enumerate(steps):
        if step.get("id") == failed_step_id:
            failed_idx = i
            break
    
    if failed_idx is None:
        return {"error": "Step {} not found in plan".format(failed_step_id)}
    
    failed_step = steps[failed_idx]
    retry_step = {
        "id": failed_step["id"] + "_retry",
        "agent": failed_step.get("agent", "CoderAgent"),
        "task": "RETRY with alternative approach: " + failed_step["task"] + " (previous error: " + error + ")",
        "need": failed_step.get("need"),
        "mcp_suggested": failed_step.get("mcp_suggested"),
        "agent_suggested": failed_step.get("agent_suggested"),
        "status": "pending",
        "is_retry": True
    }
    
    new_steps = steps[:failed_idx+1] + [retry_step] + steps[failed_idx+1:]
    
    return {
        "goal": plan.get("goal"),
        "steps": new_steps,
        "metadata": {
            "total_steps": len(new_steps),
            "created_by": "mcp-planner-replan"
        }
    }



async def _read_frame(stream):
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


async def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()


async def main_loop():
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        req = await _read_frame(stdin)
        if req is None:
            break
        resp = await handle(req)
        if resp is not None:
            await _write_frame(stdout, resp)


if __name__ == "__main__":
    import os
    asyncio.run(main_loop())