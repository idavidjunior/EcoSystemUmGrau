"""Tool/Permission Runtime — ETAPA 19

Camada intermediária determinística, segura, auditável e extensível entre o Cognitive
Core e qualquer ferramenta, recurso, serviço, processo, arquivo, comando, API ou ação
externa.

Princípio fundamental: COGNITIVE CORE NÃO executa ferramentas diretamente.
O Cognitive Core solicita uma operação.
O Tool/Permission Runtime analisa, valida capacidades, verifica permissões e políticas,
aplicando controles de segurança e somente então autoriza ou rejeita a execução.

A ferramenta executa.
O Runtime captura e normaliza o resultado.
Tudo relevante é registrado para observabilidade, auditoria e aprendizado posterior.
"""

from typing import Literal, Optional, Dict, Any, List, NamedTuple
import json
import time
import uuid
import os
import sys
import importlib.util

# ──────────────────────────────────────────────────────────────────
# Helper para carregar módulos diretamente do filesystem (evita namespace collision)
# ──────────────────────────────────────────────────────────────────

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_module(module_name: str, filename: str):
    """Carrega um módulo Python diretamente do arquivo .py."""
    filepath = os.path.join(_SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {filename} from {filepath}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Carregar módulos essenciais do scripts
_security_engine = _load_module("security_engine", "security_engine.py")
_tool_orchestrator = _load_module("tool_orchestrator", "tool_orchestrator.py")
_learning_engine = _load_module("learning_engine", "learning_engine.py")
_memory_engine = _load_module("memory_engine", "memory_engine.py")

# ──────────────────────────────────────────────────────────────────
# Tipos e dados estruturados
# ──────────────────────────────────────────────────────────────────

class AuthorizationDecision(NamedTuple):
    decision: Literal["ALLOW", "DENY", "REQUIRE_CONFIRMATION"]
    reason: str
    risk_level: Literal["low", "medium", "high", "critical"]

class ToolResult(NamedTuple):
    success: bool
    status: str
    data: Any
    error: Optional[str]
    error_code: Optional[str]
    duration: float
    metadata: Dict[str, Any]
    execution_id: str

class FailureClassification(NamedTuple):
    category: Literal[
        "VALIDATION_ERROR", "PERMISSION_DENIED", "POLICY_DENIED",
        "CONFIRMATION_REQUIRED", "NOT_FOUND", "TIMEOUT",
        "CANCELLED", "RATE_LIMITED", "TOOL_UNAVAILABLE",
        "DEPENDENCY_FAILURE", "EXECUTION_ERROR",
        "SECURITY_VIOLATION", "UNKNOWN_ERROR"
    ]
    details: str
    retryable: bool
    auto_recovery: bool

class ExecutionContext(NamedTuple):
    request_id: str
    mission_id: Optional[str]
    session_id: str
    agent_id: Optional[str]
    user_id: Optional[str]
    tool_id: str
    capability: str
    risk_level: Literal["low", "medium", "high", "critical"]
    permissions: List[str]
    timestamp: float
    deadline: Optional[float]
    metadata: Dict[str, Any]

class ToolDefinition(NamedTuple):
    id: str
    name: str
    version: Optional[str] = None
    description: str = ""
    category: str = ""
    capabilities: List[str] = None
    input_schema: Dict[str, Any] = None
    output_schema: Dict[str, Any] = None
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    required_permissions: List[str] = None
    confirmation_policy: Literal["none", "always", "risk_based"] = "none"
    timeout_policy: float = 30.0
    retry_policy: Dict[str, Any] = None
    rate_limit_policy: Dict[str, Any] = None
    isolation_policy: Dict[str, Any] = None
    enabled: bool = True
    metadata: Dict[str, Any] = None

# ──────────────────────────────────────────────────────────────────
# Tool Registry
# ──────────────────────────────────────────────────────────────────

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return len(self._tools) > 0
        try:
            self._load_known_tools()
            self._initialized = True
            return len(self._tools) > 0
        except Exception:
            self._initialized = True
            return False

    def _load_known_tools(self):
        known_tools = [
            {"id": "filesystem_read", "name": "Filesystem Read", "category": "filesystem",
             "capabilities": ["filesystem.read"], "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
             "risk_level": "low", "required_permissions": ["filesystem.read"],
             "confirmation_policy": "none", "timeout_policy": 30.0,
             "retry_policy": {"max_attempts": 2, "backoff_base": 1.0},
             "rate_limit_policy": {"calls_per_minute": 60},
             "isolation_policy": {"allowed_roots": [".", "workspace"], "blocked_roots": ["/", "/etc", "/sys"]},
             "enabled": True, "metadata": {"source": "mcp-discovered"}},
            {"id": "memory_read", "name": "Memory Read", "category": "memory",
             "capabilities": ["memory.read"], "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
             "risk_level": "low", "required_permissions": ["memory.read"],
             "confirmation_policy": "none", "timeout_policy": 15.0,
             "retry_policy": {"max_attempts": 2, "backoff_base": 1.0},
             "rate_limit_policy": {"calls_per_minute": 120},
             "isolation_policy": {"require_project_context": True},
             "enabled": True, "metadata": {"source": "mcp-discovered"}},
            {"id": "shell_execute", "name": "Shell Execute", "category": "shell",
             "capabilities": ["shell.execute"], "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}},
             "risk_level": "critical", "required_permissions": ["shell.execute"],
             "confirmation_policy": "always", "timeout_policy": 60.0,
             "retry_policy": {"max_attempts": 0, "backoff_base": 1.0},
             "rate_limit_policy": {"calls_per_minute": 10},
             "isolation_policy": {"allowed_roots": [".", "workspace"], "blocked_roots": ["/", "/etc", "/sys"]},
             "enabled": True, "metadata": {"source": "mcp-discovered"}}
        ]

        for tool_def in known_tools:
            td = ToolDefinition(
                id=tool_def["id"], name=tool_def["name"], version=tool_def.get("version"),
                description=tool_def.get("description", ""), category=tool_def.get("category", ""),
                capabilities=tool_def.get("capabilities", []), input_schema=tool_def.get("input_schema", {}),
                output_schema=tool_def.get("output_schema", {}), risk_level=tool_def.get("risk_level", "low"),
                required_permissions=tool_def.get("required_permissions", []),
                confirmation_policy=tool_def.get("confirmation_policy", "none"),
                timeout_policy=tool_def.get("timeout_policy", 30.0),
                retry_policy=tool_def.get("retry_policy", {"max_attempts": 1, "backoff_base": 1.0}),
                rate_limit_policy=tool_def.get("rate_limit_policy", {"calls_per_minute": 60}),
                isolation_policy=tool_def.get("isolation_policy", {"allowed_roots": [".", "workspace"], "blocked_roots": ["/", "/etc", "/sys"]}),
                enabled=tool_def.get("enabled", True), metadata=tool_def.get("metadata", {})
            )
            self._tools[td.id] = td

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id)

    def list_tools(self, category: Optional[str] = None, capability: Optional[str] = None) -> List[ToolDefinition]:
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        if capability:
            tools = [t for t in tools if capability in t.capabilities]
        return tools

    def list_capabilities(self) -> List[str]:
        capabilities = set()
        for tool in self._tools.values():
            for cap in tool.capabilities:
                capabilities.add(cap)
        return sorted(capabilities)


# ──────────────────────────────────────────────────────────────────
# Permission Engine
# ──────────────────────────────────────────────────────────────────

class PermissionEngine:
    def __init__(self, registry: ToolRegistry):
        self._registry = registry
        self._security = _security_engine.SecurityEngine()
        self._policies = {
            "require_confirmation_risk_threshold": "medium",
            "always_confirm": ["shell.execute", "filesystem.delete"],
            "never_confirm": ["memory.read", "knowledge.search"]
        }

    def evaluate(self, tool_id: str, capability: str,
                 execution_context: ExecutionContext) -> AuthorizationDecision:
        tool = self._registry.get_tool(tool_id)
        if not tool:
            return AuthorizationDecision(decision="DENY", reason=f"Ferramenta {tool_id} não encontrada", risk_level="high")
        if capability not in tool.capabilities:
            return AuthorizationDecision(decision="DENY", reason=f"Capability '{capability}' não suportada", risk_level="high")
        missing_perms = [p for p in tool.required_permissions if p not in execution_context.permissions]
        if missing_perms:
            return AuthorizationDecision(decision="DENY", reason=f"Permissões faltando: {', '.join(missing_perms)}", risk_level="high")
        risk = tool.risk_level
        risk_index = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        risk_idx = risk_index.get(risk, 0)
        if risk_idx >= 3:
            return AuthorizationDecision(decision="REQUIRE_CONFIRMATION", reason=f"Operação de risco CRÍTICO ({risk}). Confirmação requerida.", risk_level=risk)
        if risk_idx == 2 and risk in self._policies["always_confirm"]:
            return AuthorizationDecision(decision="REQUIRE_CONFIRMATION", reason=f"Operação de risco ALTO ({risk}). Sempre requer confirmação.", risk_level=risk)
        if risk_idx == 1:
            if tool.confirmation_policy == "never":
                return AuthorizationDecision(decision="ALLOW", reason="Risco médio com política never.", risk_level=risk)
            if tool.confirmation_policy == "risk_based":
                return AuthorizationDecision(decision="ALLOW", reason="Risco médio com política risk_based.", risk_level=risk)
            return AuthorizationDecision(decision="REQUIRE_CONFIRMATION", reason="Risco médio - confirmação requerida por política.", risk_level=risk)
        return AuthorizationDecision(decision="ALLOW", reason="Risco baixo - executando automaticamente.", risk_level=risk)


# ──────────────────────────────────────────────────────────────────
# Confirmation Manager
# ──────────────────────────────────────────────────────────────────

class ConfirmationManager:
    def __init__(self):
        self._pending: Dict[str, Dict[str, Any]] = {}
        self._callbacks: Dict[str, callable] = {}

    def request_confirmation(self, execution_context: ExecutionContext,
                             tool_name: str, capability: str,
                             operation_description: str,
                             confirmation_id: Optional[str] = None) -> str:
        if not confirmation_id:
            confirmation_id = str(uuid.uuid4())
        self._pending[confirmation_id] = {
            "execution_context": execution_context,
            "tool_name": tool_name, "capability": capability,
            "operation_description": operation_description,
            "timestamp": time.time(), "decision": None, "resolved": False}
        return confirmation_id

    def resolve_confirmation(self, confirmation_id: str, decision: Literal["approve", "reject"]) -> bool:
        if confirmation_id not in self._pending:
            return False
        self._pending[confirmation_id]["decision"] = decision
        self._pending[confirmation_id]["resolved"] = True
        if confirmation_id in self._callbacks:
            try:
                self._callbacks[confirmation_id](decision == "approve")
            except Exception:
                pass
        return decision == "approve"


# ──────────────────────────────────────────────────────────────────
# Argument Validation
# ──────────────────────────────────────────────────────────────────

class ArgumentValidator:
    def __init__(self):
        self._security = _security_engine.SecurityEngine()

    def validate(self, args: Dict[str, Any], input_schema: Dict[str, Any]) -> tuple:
        errors = []
        if not isinstance(args, dict):
            errors.append("Argumentos devem ser um objeto JSON/dict")
            return False, errors, None
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        for field in required:
            if field not in args:
                errors.append(f"Campo obrigatório ausente: '{field}'")
        for field_name, field_schema in properties.items():
            if field_name in args:
                value = args[field_name]
                if field_schema.get("type") == "string" and not isinstance(value, str):
                    errors.append(f"Campo '{field_name}': expected string")
                if field_schema.get("enum") and value not in field_schema["enum"]:
                    errors.append(f"Campo '{field_name}': must be one of {field_schema['enum']}")
        # Redaction simples
        import re
        patterns = [(r"sk-[a-zA-Z0-9]{20,}", "sk-[REDACTED]"),
                    (r"(password|passwd|pwd)[:=][^,\n]{3,}", "password=[REDACTED]")]
        for pattern, replacement in patterns:
            for key in list(args.keys()):
                if isinstance(args[key], str) and re.search(pattern, args[key], re.IGNORECASE):
                    args[key] = replacement
        return (len(errors) == 0, errors, args if len(errors) == 0 else None)


# ──────────────────────────────────────────────────────────────────
# Main Runtime Class
# ──────────────────────────────────────────────────────────────────

class ToolPermissionRuntime:
    def __init__(self):
        self._registry = ToolRegistry()
        self._permission_engine = PermissionEngine(self._registry)
        self._confirmation_manager = ConfirmationManager()
        self._argument_validator = ArgumentValidator()
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return True
        if not self._registry.initialize():
            return False
        self._initialized = True
        return True

    def request_tool_execution(self, request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            tool_id = request.get("tool_id", "")
            capability = request.get("capability", "")
            arguments = request.get("arguments", {})
            exec_dict = request.get("execution_context", {})

            exec_context = ExecutionContext(
                request_id=request.get("request_id", str(uuid.uuid4())),
                mission_id=request.get("mission_id"),
                session_id=request.get("session_id", "default"),
                agent_id=request.get("agent_id"),
                user_id=request.get("user_id"),
                tool_id=tool_id, capability=capability,
                risk_level=request.get("risk_level", "low"),
                permissions=exec_dict.get("permissions", []),
                timestamp=time.time(),
                deadline=request.get("deadline"),
                metadata=exec_dict.get("metadata", {})
            )

            tool = self._registry.get_tool(tool_id)
            is_valid, validation_errors, validated_args = self._argument_validator.validate(
                arguments, tool.input_schema if tool else {})

            security_errors = self._security_scan(tool, validated_args or {}, capability)

            if not is_valid or security_errors:
                combined_errors = (validation_errors or []) + (security_errors or [])
                result = ToolResult(success=False, status="validation_failed", data=None,
                                    error="Argumentos inválidos: " + "; ".join(combined_errors[:5]),
                                    error_code="VALIDATION_ERROR",
                                    duration=0.0, metadata={}, execution_id="")
                auth_decision = AuthorizationDecision(decision="DENY",
                                                      reason="Falha na validação de argumentos ou segurança",
                                                      risk_level="high" if security_errors else "medium")
                result_out = {k: v for k, v in result._asdict().items()}
                return {
                    "status": result.status,
                    "authorization_decision": auth_decision.decision,
                    "authorization_reason": auth_decision.reason,
                    "result": result_out,
                    "error": result.error,
                    "confirmation_id": None,
                    "audit_entry_id": str(uuid.uuid4())
                }

            auth_decision = self._permission_engine.evaluate(
                tool_id, capability, exec_context)

            confirmation_id_out = None

            if auth_decision.decision == "ALLOW":
                result = self._execute_tool(tool_id, capability, validated_args or {})
            elif auth_decision.decision == "DENY":
                result = ToolResult(success=False, status="denied", data=None,
                                    error="Operação negada pelo Permission Engine",
                                    error_code="PERMISSION_DENIED",
                                    duration=0.0, metadata={}, execution_id="")
            elif auth_decision.decision == "REQUIRE_CONFIRMATION":
                confirmation_id_out = self._confirmation_manager.request_confirmation(
                    exec_context, tool.name if tool else tool_id,
                    capability, "Operação de ferramenta")
                result = ToolResult(success=False, status="confirmation_required",
                                    data=None,
                                    error=f"Confirmação requerida (ID: {confirmation_id_out})",
                                    error_code="CONFIRMATION_REQUIRED",
                                    duration=0.0, metadata={}, execution_id="")
            else:
                result = ToolResult(success=False, status="failed", data=None,
                                    error="Decisão de autorização inválida",
                                    error_code="INVALID_AUTH", duration=0.0,
                                    metadata={}, execution_id="")

            audit_entry = {
                "request_id": exec_context.request_id,
                "tool_id": tool_id, "capability": capability,
                "authorization_decision": auth_decision.decision,
                "risk_level": auth_decision.risk_level,
                "arguments_validated": is_valid,
                "validation_errors": validation_errors if not is_valid else [],
                "timestamp": time.time(),
                "execution_status": result.status if hasattr(result, 'status') else "unknown"
            }

            return {
                "status": result.status,
                "authorization_decision": auth_decision.decision,
                "authorization_reason": auth_decision.reason,
                "result": {k: v for k, v in result._asdict().items() if not k.startswith('_')},
                "error": result.error,
                "confirmation_id": confirmation_id_out,
                "audit_entry_id": audit_entry["request_id"]
            }
        except Exception as e:
            return {
                "status": "failed",
                "authorization_decision": "DENY",
                "authorization_reason": f"Erro interno: {str(e)[:200]}",
                "result": None, "error": str(e)[:500],
                "confirmation_id": None, "audit_entry_id": str(uuid.uuid4())
            }

    def _security_scan(self, tool, args: Dict[str, Any], capability: str) -> List[str]:
        """Varredura de segurança sobre argumentos (path traversal, command injection)."""
        errors: List[str] = []
        if not tool:
            return errors
        security = self._permission_engine._security

        if tool.category == "filesystem" and "path" in args and isinstance(args.get("path"), str):
            ok, events = security.validate_path(args["path"], source="tool_runtime")
            if not ok:
                errors.append("Caminho bloqueado por regra de segurança: " + args["path"][:60])

        if tool.category == "shell" and "command" in args and isinstance(args.get("command"), str):
            ok, events = security.validate_command(args["command"], source="tool_runtime")
            if not ok:
                errors.append("Comando bloqueado por regra de segurança: " + args["command"][:60])

        return errors

    def _execute_tool(self, tool_id: str, capability: str, args: Dict[str, Any]) -> ToolResult:
        return ToolResult(success=True, status="completed", data="simulated result",
                          error=None, error_code=None, duration=1.0,
                          metadata={"tool_id": tool_id, "capability": capability},
                          execution_id=str(uuid.uuid4()))


def process_tool_request(request: Dict[str, Any]) -> Dict[str, Any]:
    runtime = ToolPermissionRuntime()
    if not runtime.initialize():
        return {"status": "failed", "authorization_decision": "DENY",
                "authorization_reason": "Falha ao inicializar o Runtime",
                "result": None, "error": "Runtime initialization failed",
                "confirmation_id": None, "audit_entry_id": str(uuid.uuid4())}
    return runtime.request_tool_execution(request)


__all__ = [
    "ToolPermissionRuntime", "process_tool_request",
    "ToolRegistry", "PermissionEngine", "ConfirmationManager",
    "ArgumentValidator", "ToolDefinition", "ExecutionContext",
    "AuthorizationDecision", "ToolResult", "FailureClassification"
]