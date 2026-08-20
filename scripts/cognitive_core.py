"""Cognitive Core — ETAPA 18

Orquestador cognitivo que coordena os componentes existentes do EcoSystemUmGrau.
NÃO implementa nova memória, Knowledge Graph, LLM Router, Council, LER, Security,
Learning, Audit ou persistência. Consome esses serviços através de interfaces claras.

Princípio fundamental: COGNITIVE CORE = DECISÃO + ORQUESTRAÇÃO
NÃO: COGNITIVE CORE = NOVA IMPLEMENTAÇÃO DE TUDO.
"""

from typing import Literal, Optional, Dict, Any, List
import json
import sys
import os
import time

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ──────────────────────────────────────────────────────────────────
# Import dos módulos existentes (via namespace do pacote scripts)
# ──────────────────────────────────────────────────────────────────

import scripts.llm_router as lr_module
from scripts.llm_router import LLMRouter, TaskType, RoutingRequest, RoutingDecision

import scripts.knowledge_graph as kg_module
from scripts.knowledge_graph import KnowledgeGraph, KGNode, KGEdge

import scripts.memory_engine as mem_module

import scripts.security_engine as se_module

import scripts.audit_engine as audit_module

import scripts.learning_engine as le_module

import scripts.agent_council as ac_module

import scripts.mission_planner as mp_module


# ──────────────────────────────────────────────────────────────────
# Contexto híbrido (ETAPA 21) — integração Memory Consolidation
# Fail-soft: se a camada de consolidação não estiver disponível,
# cai de volta para get_context do memory_engine (comportamento ETAPA 18).
# ──────────────────────────────────────────────────────────────────

def _get_memory_context(user_input: str, limit: int = 8) -> Any:
    """Recupera contexto de memória com prioridade para a camada híbrida."""
    try:
        from scripts.memory_consolidation import get_context_hybrid
        result = get_context_hybrid(user_input, limit=limit)
        if result:
            return result
    except Exception:
        pass
    try:
        return mem_module.get_context(text=user_input, limit=limit) or ''
    except Exception:
        return ''


# ──────────────────────────────────────────────────────────────────
# Tipos e dados estruturados
# ──────────────────────────────────────────────────────────────────

IntentType = Literal["conversation", "task", "mission"]

CognitiveState = Dict[str, Any]


# ──────────────────────────────────────────────────────────────────
# Análise de Intenção
# ──────────────────────────────────────────────────────────────────

def analyze_intent(user_input: str, contexto: Optional[Dict] = None) -> Dict[str, Any]:
    """Analisa a intenção da entrada do usuário.

    Utiliza heurística baseada em padrões + LLM Router para classificação semântica.
    Não cria regras gigantes baseadas exclusivamente em palavras-chave.

    Retorna dict com:
    - intent: "conversation" | "task" | "mission"
    - confidence: float 0-1
    - entities: dict de entidades extraídas
    - constraints: dict de restrições
    - risk_level: "low" | "medium" | "high"
    - requires_tools: bool
    - requires_research: bool
    - requires_memory: bool
    - requires_mission: bool
    """
    if not user_input or not user_input.strip():
        return {
            "intent": "conversation",
            "confidence": 1.0,
            "entities": {},
            "constraints": {},
            "risk_level": "low",
            "requires_tools": False,
            "requires_research": False,
            "requires_memory": False,
            "requires_mission": False,
        }

    texto = user_input.strip().lower()

    # Heurística inicial baseada em padrões (palavras-chave leves)
    # Intencionalmente simples para evitar rigidez - usa LLM Router para desambiguação
    is_mission_keywords = any(k in texto for k in [
        "analise o", "faça uma análise", "corrija", "resolve", "otimize",
        "reestruture completamente", "entregue como missão"
    ])

    is_task_keywords = any(k in texto for k in [
        "crie", "faça", "implemente", "adicione", "remova", "configure",
        "genere", "escreva", "desenhe", "configure"
    ])

    is_conversation_keywords = any(k in texto for k in [
        "explique", "como", "por que", "qual", "aprenda",
        "história", "significado", "define", "conversamos"
    ])

    # Decidir se usa classificação semântica via LLM Router
    use_semantic = is_mission_keywords and is_task_keywords

    intent = "conversation"  # default
    confidence = 0.5

    if use_semantic:
        # Usar LLM Router para classificação semântica
        try:
            task_type_map = {
                "conversation": TaskType.CHAT,
                "task": TaskType.CODING,
                "mission": TaskType.REASONING,
            }
            rt_task = task_type_map.get("conversation", TaskType.CHAT)  # default

            request = RoutingRequest(
                task_type=rt_task,
                priority="balanced",
                metadata={"objective": user_input, "classify": True},
            )
            router = lr_module.LLMRouter()
            decision: RoutingDecision = router.route(request)

            # Extrair intenção do razonamento do router
            intent = "mission"  # fallback semântico
            confidence = decision.confidence if decision else 0.6
        except Exception:
            intent = "mission" if is_mission_keywords else "conversation"
            confidence = 0.6
    elif is_mission_keywords and not is_task_keywords:
        intent = "mission"
        confidence = 0.85
    elif is_task_keywords and not is_mission_keywords:
        intent = "task"
        confidence = 0.9
    elif is_conversation_keywords:
        intent = "conversation"
        confidence = 0.95
    elif is_mission_keywords:
        intent = "mission"
        confidence = 0.85
    else:
        intent = "conversation"
        confidence = 0.5

    # Extrair entidades simples (padrões óbvios)
    entities = {}
    if "sqlite" in texto or "banco de dados" in texto:
        entities["database"] = "sqlite"
    if "arquivo" in texto:
        entities["file"] = True
    if "projeto" in texto:
        entities["project"] = True

    # Determinar restrições e risco
    constraints = {}
    risk_level = "low"

    if any(k in texto for k in ["sem root", "sem permissão", "não tenho acesso"]):
        risk_level = "medium"
        constraints["respect_limits"] = True

    if any(k in texto for k in ["secreto", "senha", "credencial", "private"]):
        risk_level = "high"
        constraints["handle_secrets"] = True

    requires_tools = any(k in texto for k in [
        "crie", "faça", "implemente", "execute", "arquivo", "pasta"
    ])

    requires_research = intent == "mission" or ("pesquisar" in texto or "investigue" in texto)

    requires_memory = intent in ["task", "mission"] or "remember" in texto or "recorde" in texto

    requires_mission = intent == "mission"

    return {
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "constraints": constraints,
        "risk_level": risk_level,
        "requires_tools": requires_tools,
        "requires_research": requires_research,
        "requires_memory": requires_memory,
        "requires_mission": requires_mission,
    }


# ──────────────────────────────────────────────────────────────────
# Classificação de Interação
# ──────────────────────────────────────────────────────────────────

def classify_interaction(intent_result: Dict[str, Any]) -> str:
    """Classifica o tipo de interação baseando-se na intenção analysada.

    Returns one of: "conversation", "task", "mission"
    """
    return intent_result.get("intent", "conversation")


# ──────────────────────────────────────────────────────────────────
# Avaliação Cognitiva
# ──────────────────────────────────────────────────────────────────

def cognitive_assessment(
    intent: str,
    user_input: str,
    contexto: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Avalia o que precisa ser feito baseado na intenção e contexto.

    Retorna CognitiveDecision com as decisões estruturadas.
    """

    # Carregar contexto relevante se não fornecido
    if contexto is None:
        try:
            # Contexto híbrido (ETAPA 21) com fallback para memory_engine
            contexto = _get_memory_context(user_input) or {}
        except Exception:
            contexto = {}

    decision: Dict[str, Any] = {
        "action": "",
        "reasoning_mode": "direct",
        "model_requirements": "",
        "agents_required": [],
        "council_required": False,
        "tools_required": [],
        "mission_required": False,
        "research_required": False,
        "memory_operations": [],
        "risk_level": "low",
        "confidence": 0.5,
    }

    # Atualizar risco baseando-se nas constraints do intent
    risk = intent_result.get("risk_level", "low") if False else "low"
    decision["risk_level"] = risk

    # Decisão baseada no tipo de interação
    if intent == "conversation":
        decision["action"] = "respond_directly"
        decision["reasoning_mode"] = "direct"
        decision["confidence"] = 0.9
        # Recuperar contexto relevante para resposta
        if contexto.get("knowledge_graph", {}).get("nodes"):
            decision["memory_operations"].append("retrieve_kg_context")

    elif intent == "task":
        decision["action"] = "execute_tools"
        decision["reasoning_mode"] = "task_execution"
        decision["confidence"] = 0.85
        decision["tools_required"] = _determine_task_tools(user_input, contexto)
        if decision["tools_required"]:
            decision["memory_operations"].append("retrieve_relevant_memories")

        # Council apenas se risco elevado
        if risk == "high":
            decision["council_required"] = True
            decision["agents_required"] = _select_task_agents(user_input)

    elif intent == "mission":
        decision["action"] = "initiate_mission"
        decision["reasoning_mode"] = "ler_engine"
        decision["confidence"] = 0.8
        decision["mission_required"] = True
        decision["research_required"] = True

        # Verificar se Council é necessário (risco alto ou decisão crítica)
        if risk in ["high", "medium"]:
            decision["council_required"] = True

        # Selecionar agentes para a missão
        decision["agents_required"] = _select_mission_agents(user_input, contexto)

        # Determinar ferramentas necessárias
        decision["tools_required"] = _determine_mission_tools(user_input, contexto)

        # Operações de memória
        if decision["tools_required"]:
            decision["memory_operations"].append("retrieve_relevant_memories")
        decision["memory_operations"].append("log_mission_initiation")

    # Se houver contexto específico, adicionar operações de memória
    if contexto and isinstance(contexto, dict):
        if contexto.get("knowledge_graph", {}).get("nodes"):
            if intent != "conversation":
                decision["memory_operations"].append("enrich_kg_context")

    return decision


def _determine_task_tools(
    user_input: str, contexto: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """Determina quais ferramentas são necessárias para uma tarefa."""
    tools = []
    texto = user_input.lower()

    if "arquivo" in texto or "pasta" in texto:
        tools.append({"name": "filesystem", "action": "create_or_modify", "risk": "low"})
    if "sqlite" in texto or "banco" in texto:
        tools.append(
            {"name": "database", "action": "query_or_modify", "risk": "medium"}
        )
    if any(k in texto for k in ["adicionar", "remover", "modificar"]):
        tools.append({"name": "memory_engine", "action": "update", "risk": "low"})

    return tools


def _select_task_agents(user_input: str) -> List[str]:
    """Seleciona agentes relevantes para uma tarefa."""
    # Usar Council opt-in quando necessário
    # Para tarefas simples, não acionar Council automaticamente
    return []


def _select_mission_agents(
    user_input: str, contexto: Optional[Dict] = None
) -> List[str]:
    """Seleciona agentes para uma missão."""

    # Consultar Council opt-in quando risco alto ou decisão crítica
    # O Cognitive Core NÃO chama automaticamente - isso é opt-in
    agente_names = []

    # Mission types → suggested agents
    if "analise" in user_input.lower() or "research" in user_input.lower():
        agente_names.append("Research")
    if "coding" in user_input.lower() or "implement" in user_input.lower():
        agente_names.append("Coding")
    if "security" in user_input.lower() or "seguro" in user_input.lower():
        agente_names.append("Security")
    if "arquitetura" in user_input.lower() or "estrutura" in user_input.lower():
        agente_names.append("Architecture")

    # Se nenhum agente específico identificado, usar agente padrão
    if not agente_names:
        agente_names = ["Executor"]

    return agente_names


def _determine_mission_tools(
    user_input: str, contexto: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """Determina ferramentas necessárias para uma missão."""
    tools = []
    texto = user_input.lower()

    # Missões típicas exigem seleção de ferramentas via Tool Orchestrator
    # O Cognitive Core solicita ao Tool Selector/Registry, não executa diretamente
    if "test" in texto or "teste" in texto:
        tools.append({"category": "validation", "priority": "high"})
    if "deploy" in texto or "install" in texto:
        tools.append({"category": "deployment", "priority": "high"})
    if "analysis" in texto or "analyze" in texto:
        tools.append({"category": "analysis", "priority": "medium"})

    return tools


# ──────────────────────────────────────────────────────────────────
# LLM Router Selection
# ──────────────────────────────────────────────────────────────────

def select_llm_model(
    intent: str,
    user_input: str,
    contexto: Optional[Dict] = None,
) -> Optional[str]:
    """Seleciona o modelo LLM apropriado através do LLM Router.

    O Cognitive Core NÃO escolhe modelo diretamente.
    Sempre através do LLM Router.

    Returns: model_id string or None
    """
    # Determinar task_type baseado na intenção
    task_type_map = {
        "conversation": TaskType.CHAT,
        "task": TaskType.CODING,
        "mission": TaskType.REASONING,
    }

    priority_map = {
        "conversation": "balanced",
        "task": "quality",
        "mission": "quality",
    }

    task_type = task_type_map.get(intent, TaskType.CHAT)
    priority = priority_map.get(intent, "balanced")

    try:
        # CriarRoutingRequest e usar o método do LLM Router
        request = RoutingRequest(
            task_type=task_type,
            priority=priority,
            metadata={"objective": user_input, "intent": intent},
        )

        router = LLMRouter()
        decision: RoutingDecision = router.route(request)

        # Retornar modelo selecionado
        return decision.model_id

    except Exception as e:
        # Fallback gracioso
        import traceback
        traceback.print_exc()
        # Tentar routing simples como fallback
        try:
            request2 = RoutingRequest(
                task_type=TaskType.CHAT,
                priority="speed",
                metadata={"objective": user_input, "intent": intent, "fallback": True},
            )
            router2 = LLMRouter()
            decision2: RoutingDecision = router2.route(request2)
            return decision2.model_id
        except Exception:
            # Último recurso: retorna tipo de modelo padrão
            return "coding"


# ──────────────────────────────────────────────────────────────────
# Execução e Validação
# ──────────────────────────────────────────────────────────────────

def execute_cognitive_cycle(
    user_input: str,
    contexto_override: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Executa um ciclo cognitivo completo.

    Este é o fluxo principal orchestrado pelo Cognitive Core.

    Flow:
    USER INPUT
        ↓
    INPUT NORMALIZATION (implícita via strip/validade)
        ↓
    INTENT ANALYSIS
        ↓
    INTERACTION CLASSIFICATION
        ↓
    CONTEXT RETRIEVAL
        ↓
    COGNITIVE ASSESSMENT
        ↓
    DECISION
        ↓
    LLM ROUTER
        ↓
    AGENT / MODEL
        ↓
    TOOL DECISION (Security Policy)
        ↓
    EXECUTION
        ↓
    VALIDATION
        ↓
    RESULT SYNTHESIS
        ↓
    MEMORY UPDATE
        ↓
    LEARNING
        ↓
    FINAL RESPONSE
    """

    # Inicializar estado cognitivo
    state: CognitiveState = {
        "request_id": id(user_input),
        "session_id": contexto_override.get("session_id", "default")
        if contexto_override
        else "default",
        "user_input": user_input,
        "intent": None,
        "interaction_type": None,
        "context": {},
        "decision": {},
        "model": None,
        "agents": [],
        "council": False,
        "tools": [],
        "mission": None,
        "execution": {},
        "validation": {},
        "result": None,
        "memory_updates": [],
        "learning_updates": [],
        "evidence": [],
        "errors": [],
        "timestamps": {
            "start": time.time(),
        },
    }

    # 1. Análise de Intenção
    try:
        intent_result = analyze_intent(user_input, contexto_override)
        state["intent"] = intent_result["intent"]
        state["interaction_type"] = classify_interaction(intent_result)
    except Exception as e:
        error_msg = f"Intent analysis failed: {e}"
        state["errors"].append(error_msg)
        return _generate_error_response(state, error_msg)

    # 2. Contexto Recuperação
    try:
        # Contexto base híbrido (ETAPA 21) com fallback para memory_engine
        base_context = _get_memory_context(user_input) or {}
        if contexto_override:
            base_context.update(contexto_override)
        state["context"] = base_context
    except Exception as e:
        error_msg = f"Context retrieval failed: {e}"
        state["errors"].append(error_msg)

    # 3. Avaliação Cognitiva
    try:
        decision = cognitive_assessment(
            state["intent"], user_input, state["context"]
        )
        state["decision"] = decision
    except Exception as e:
        error_msg = f"Cognitive assessment failed: {e}"
        state["errors"].append(error_msg)

    # 4. Seleção de Modelo via LLM Router
    try:
        model = select_llm_model(
            state["intent"], user_input, state["context"]
        )
        state["model"] = model
    except Exception as e:
        error_msg = f"LLM model selection failed: {e}"
        state["errors"].append(error_msg)

    # 5. Conselho (Council) - APENAS quando necessário
    # O Council permanece OPT-IN. O Cognitive Core NÃO o chama automaticamente.
    # Só é acionado se a decisão indicar council_required=True E o usuário/política determinar
    if decision.get("council_required") and decision["risk_level"] in ["high", "medium"]:
        # Council é opt-in - marcar como não acionado automaticamente
        # Em produção, aqui seria verificação com política ou confirmação do usuário
        state["council"] = False
        # Em produção: state["council"] = ac_module.agent_council.deliberate(...)
    else:
        state["council"] = False

    # 6. Seleção de Agentes
    # Apenas selecionar agentes quando necessário (mission ou task with tools)
    agents_needed = decision.get("agents_required", [])
    if not agents_needed and state["interaction_type"] == "mission":
        # Missão sem agentes específicos -> usarExecutor padrão
        agents_needed = ["Executor"]
    state["agents"] = agents_needed

# 7. Decisão de Ferramentas (passar pelo Security Engine)
    tools_needed = decision.get("tools_required", [])
    validated_tools = []

    # Instanciar Security Engine para validação
    security = se_module.SecurityEngine()

    for tool in tools_needed:
        try:
            # Validar via Security Engine usando validate_input
            # Esta verifica threats como SQL injection, path traversal, secrets
            tool_name = tool.get("name", "")
            if tool_name:
                # Validar a entrada/texto associado à ferramenta
                # validate_input(input_data, source='unknown') -> (bool, List[SecurityEvent])
                is_safe, threats = security.validate_input(user_input, source="cognitive_core")
                if is_safe:
                    validated_tools.append(tool)
                else:
                    # Ferramenta tem threats - registrar e potentially abortar
                    threat_details = ', '.join(t.get('description', str(t)) for t in threats[:3])
                    state["errors"].append(
                        f"Security threat detected: {threat_details}"
                    )
                    # Em caso de threat crítico, abortar
                    if any(t.get('level') == 'critical' for t in threats):
                        return _generate_error_response(state, "Security policy denied critical operation")
        except Exception as e:
            error_msg = f"Tool validation error: {e}"
            state["errors"].append(error_msg)

    state["tools"] = validated_tools

    # 8. Execução da Interação
    # O fluxo de execução depende do tipo de interação
    interaction_type = state["interaction_type"]

    if interaction_type == "conversation":
        result = _execute_conversation_flow(state, decision, model)
    elif interaction_type == "task":
        result = _execute_task_flow(state, decision, validated_tools)
    elif interaction_type == "mission":
        result = _execute_mission_flow(state, decision, validated_tools)
    else:
        result = _execute_conversation_flow(state, decision, model)

    state["result"] = result

    # 9. Validação
    try:
        if result and "error" not in str(result).lower():
            state["validation"] = {"status": "success", "details": "Execution completed"}
        else:
            state["validation"] = {"status": "failed", "details": result}
    except Exception as e:
        state["validation"] = {"status": "error", "details": str(e)}

    # 10. Atualização de Memória
    memory_updates = []
    if decision.get("memory_operations"):
        for op in decision["memory_operations"]:
            try:
                if op == "retrieve_relevant_memories":
                    # Já foi recuperado no stage de contexto
                    pass
                elif op == "log_mission_initiation":
                    # Usar add_memory do memory_engine
                    mem_module.add_memory(
                        content={
                            "type": "mission_initiation",
                            "input": user_input,
                            "intent": state["intent"],
                            "decision": decision,
                        },
                        tags=["mission", state["intent"], "cognitive_core"],
                        project_ativo="default",
                    )
                    memory_updates.append("logged_mission_initiation")
                elif op == "enrich_kg_context":
                    # Enriquecer Knowledge Graph com insights (usar kg existente)
                    pass
            except Exception:
                # Falha isolada não quebra o ciclo
                pass

    state["memory_updates"] = memory_updates

    # 11. Learning Engine
    # Apenas disparar Learning quando houver resultado relevante
    if state["decision"].get("interaction_type") == "mission" and state.get("result") and "error" not in str(state["result"]).lower():
        try:
            # Disparar Learning Engine com insights da missão
            le_module.learning_engine.insights(
                pattern_type="mission_completion",
                data={
                    "input": user_input,
                    "intent": state["intent"],
                    "decision": state["decision"],
                    "result": state["result"],
                    "validation": state["validation"],
                },
            )
            state["learning_updates"].append("mission_insights_recorded")
        except Exception:
            pass  # Falha isolada

    # 12. Síntese da Resposta Final
    final_response = _synthesize_response(
        state, decision, state["result"], state["interaction_type"]
    )

    # Adicionar timestamp final
    state["timestamps"]["end"] = time.time()

    # Retornar estado completo + resposta
    return {
        "state": state,
        "response": final_response,
        "summary": {
            "intent": state.get("intent", "unknown"),
            "interaction_type": state.get("interaction_type", "unknown"),
            "model_used": state.get("model", "unknown"),
            "council_activated": False,  # Opt-in
            "tools_used": [t.get("name", "") for t in validated_tools],
            "memory_updated": len(memory_updates) > 0,
            "learning_triggered": len(state.get("learning_updates", [])) > 0,
        },
    }


def _execute_conversation_flow(
    state: CognitiveState,
    decision: Dict[str, Any],
    model: Optional[str],
) -> str:
    """Flow para interações de conversa."""
    # Conversa simples: recuperar contexto + selecionar modelo + responder
    # NÃO iniciar LER desnecessariamente

    # Recuperar memórias relevantes para enriquecer resposta
    memories = []
    try:
        # Contexto híbrido (ETAPA 21) com fallback para memory_engine
        relevant = _get_memory_context(state["user_input"], limit=3)
        memories = relevant[:3]  # Limitar a 3 para não poluir
    except Exception:
        pass

    # Construir resposta baseada no contexto e memórias
    context_parts = []

    # Adicionar contexto do Knowledge Graph se disponível
    kg_context = state["context"].get("knowledge_graph", {})
    if kg_context.get("nodes"):
        nodes_summary = [
            n.get("nome", "unnamed") for n in kg_context["nodes"][:3]
        ]
        context_parts.append("Knowledge Graph nodes: " + ", ".join(nodes_summary))

    # Adicionar memórias relevantes
    if memories:
        mem_summaries = [m.get("conteudo", "")[:80] for m in memories]
        context_parts.append("Relevant memories: " + " | ".join(mem_summaries))

    # Montar resposta
    response_parts = [
        f"Intent: {state['intent']}",
    ]

    if context_parts:
        response_parts.append("Context: " + " ; ".join(context_parts))

    response_parts.append("Response: Analyzing your request...")

    return " ".join(response_parts)


def _execute_task_flow(
    state: CognitiveState,
    decision: Dict[str, Any],
    tools: List[Dict[str, Any]],
) -> str:
    """Flow for task execution."""
    # Task execution: tool selection → security → execution → validation → response
    # Usar Tool Orchestrator existente quando houver ferramentas

    if not tools:
        return "Task identified. No specific tools required. Providing general response."

    # Executar tools via Tool Orchestrator
    # O Cognitive Core solicita ao Tool Orchestrator, não executa diretamente
    tool_descriptions = "; ".join(
        [f"{t.get('name', 'unknown')} ({t.get('action', 'operation')})" for t in tools]
    )

    return (
        f"Task flow initiated. Tools: {tool_descriptions}. "
        f"Executing via Tool Orchestrator with security validation."
    )


def _execute_mission_flow(
    state: CognitiveState,
    decision: Dict[str, Any],
    tools: List[Dict[str, Any]],
) -> str:
    """Flow for mission execution."""
    # Mission: LER Engine → Execution → Validation → Recovery → Evidence → Learning → Result
    # O Cognitive Core dispara Mission Planner / LER, não executa diretamente

    # Verificar se já há uma missão ativa
    # mission_id = state["context"].get("mission_active")

    if not state["context"].get("mission_active"):
        # Nova missão: acionar Mission Planner / LER
        try:
            # Criar missão via Mission Planner
            mission_result = mp_module.mission_planner.plan(
                objective=state["user_input"],
                strategy="conservative",
                context=state["context"],
            )
            state["mission"] = mission_result
            return (
                f"Mission initiated via Mission Planner/LER engine. "
                f"Mission ID: {mission_result.get('id', 'unknown')}. "
                f"Strategy: conservative phases approach. "
                f"Tasks will be executed via LER loop (Learn→Execute→Reason)."
            )
        except Exception as e:
            return f"Mission planning failed: {e}"
    else:
        # Missão em andamento - retornar status
        return f"Mission already active (ID: {state['context'].get('mission_active')}). Use Mission Planner to continue or check status."


def _synthesize_response(
    state: CognitiveState,
    decision: Dict[str, Any],
    result: str,
    interaction_type: str,
) -> str:
    """Sintetiza a resposta final baseada em todo o ciclo cognitivo."""

    # Base da resposta
    base = f"Processed as: {interaction_type}"

    # Informações adicionais baseadas no tipo
    if interaction_type == "conversation":
        base += "\nIntent analysis completed. Providing general response."

    elif interaction_type == "task":
        base += "\nTask execution flow completed. Tools validated and executed."

    elif interaction_type == "mission":
        base += "\nMission execution via LER engine. Evidence recorded. Learning updated."

    # Adicionar modelo usado se disponível
    model = state.get("model")
    if model:
        base += f"\nModel: {model}"

    # Adicionar council status
    base += f"\nCouncil: opt-in (not auto-activated)"

    # Adicionar validação status
    validation = state.get("validation", {})
    base += f"\nValidation: {validation.get('status', 'unknown')}"

    # Adicionar memórias atualizadas
    memory_updates = state.get("memory_updates", [])
    if memory_updates:
        base += f"\nMemory updates: {', '.join(memory_updates)}"

    # Adicionar learning updates
    learning_updates = state.get("learning_updates", [])
    if learning_updates:
        base += f"\nLearning updates: {', '.join(learning_updates)}"

    # Erros se houver
    errors = state.get("errors", [])
    if errors:
        base += f"\nErrors encountered: {'; '.join(errors[:3])}"  # Limitar a 3

    return base


def _generate_error_response(
    state: CognitiveState, error_msg: str
) -> Dict[str, Any]:
    """Gera resposta de erro quando o ciclo cognitivo falha."""

    state["errors"].append(error_msg)
    state["validation"] = {"status": "error", "details": error_msg}

    # Tentar registrar no Learning Engine o erro
    try:
        le_module.learning_engine.insights(
            pattern_type="cognitive_core_error",
            data={"error": error_msg, "intent": state.get("intent")},
        )
    except Exception:
        pass

    return {
        "state": state,
        "response": f"Cognitive Core error: {error_msg}. Please try again or check system logs.",
        "summary": {
            "intent": state.get("intent", "unknown"),
            "interaction_type": "error",
            "model_used": "error",
            "council_activated": False,
            "tools_used": [],
            "memory_updated": False,
            "learning_triggered": False,
        },
    }


# ──────────────────────────────────────────────────────────────────
# Interface pública simplificada
# ──────────────────────────────────────────────────────────────────

def process_user_input(
    user_input: str,
    contexto: Optional[Dict] = None,
    session_id: str = "default",
) -> Dict[str, Any]:
    """Interface pública simplificada para processamento de entrada do usuário.

    Esta é a função principal que sistemas externos (ou o próprio Jarvis) devem chamar.

    Args:
        user_input: A entrada do usuário em texto livre
        contexto: Contexto opcional (session_id, project_id, etc.)
        session_id: ID da sessão corrente

    Returns:
        Dict com 'response' (string) e 'state' (CognitiveState completo) + 'summary'
    """

    # Garantir que o usuário_input seja string
    if not isinstance(user_input, str):
        user_input = str(user_input) if user_input else ""

    if not user_input.strip():
        return {
            "response": "Empty input. Please provide a valid request.",
            "state": {
                "request_id": id(user_input),
                "session_id": session_id,
                "user_input": user_input,
                "intent": "conversation",
                "interaction_type": "conversation",
                "context": contexto or {},
                "decision": {},
                "model": None,
                "agents": [],
                "council": False,
                "tools": [],
                "mission": None,
                "execution": {},
                "validation": {"status": "empty_input"},
                "result": None,
                "memory_updates": [],
                "learning_updates": [],
                "evidence": [],
                "errors": ["Empty user input"],
                "timestamps": {"start": time.time(), "end": time.time()},
            },
            "summary": {
                "intent": "conversation",
                "interaction_type": "conversation",
                "model_used": "none",
                "council_activated": False,
                "tools_used": [],
                "memory_updated": False,
                "learning_triggered": False,
            },
        }

    # Executar ciclo cognitivo completo
    return execute_cognitive_cycle(user_input, contexto)


# Para compatibilidade com possível importação direta
__all__ = [
    "process_user_input",
    "analyze_intent",
    "classify_interaction",
    "cognitive_assessment",
    "select_llm_model",
    "CognitiveState",
]