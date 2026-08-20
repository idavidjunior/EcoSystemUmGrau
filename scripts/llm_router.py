"""LLM Router - Roteamento inteligente de tarefas para modelos LLM.

Decide qual modelo usar baseado em:
- Tipo de tarefa (coding, reasoning, creative, analysis, etc.)
- Orçamento de custo
- Requisitos de latência
- Capacidades necessárias (contexto longo, function calling, etc.)
- Performance histórica dos modelos (via Model Monitor)
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

try:
    from model_monitor import _load_state as load_monitor_state, _calcular_score, _obter_modelos_disponiveis
except ImportError:
    def load_monitor_state():
        return {}
    def _calcular_score(md, config):
        return 50.0
    def _obter_modelos_disponiveis():
        return ['opencode/big-pickle', 'opencode/nemotron-3-ultra-free']


class TaskType(Enum):
    CODING = "coding"
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CHAT = "chat"
    PLANNING = "planning"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"


class Capability(Enum):
    LONG_CONTEXT = "long_context"
    FUNCTION_CALLING = "function_calling"
    STRUCTURED_OUTPUT = "structured_output"
    CODE_EXECUTION = "code_execution"
    MULTILINGUAL = "multilingual"
    REASONING = "reasoning"
    SPEED = "speed"
    CHEAP = "cheap"
    CREATIVE = "creative"


@dataclass
class ModelProfile:
    id: str
    name: str
    capabilities: List[Capability]
    cost_per_1m_input_usd: float = 0.0
    cost_per_1m_output_usd: float = 0.0
    max_context_tokens: int = 8192
    avg_latency_ms: int = 5000
    strength_tags: List[str] = field(default_factory=list)
    weakness_tags: List[str] = field(default_factory=list)


@dataclass
class RoutingRequest:
    task_type: TaskType
    required_capabilities: List[Capability] = field(default_factory=list)
    preferred_capabilities: List[Capability] = field(default_factory=list)
    max_cost_usd: Optional[float] = None
    max_latency_ms: Optional[int] = None
    min_context_tokens: Optional[int] = None
    priority: str = "balanced"  # "cost", "speed", "quality", "balanced"
    exclude_models: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    model_id: str
    confidence: float
    reasoning: str
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    estimated_cost_usd: float = 0.0
    estimated_latency_ms: int = 0


MODEL_PROFILES = {
    'opencode/big-pickle': ModelProfile(
        id='opencode/big-pickle',
        name='Big Pickle',
        capabilities=[
            Capability.LONG_CONTEXT, Capability.FUNCTION_CALLING,
            Capability.STRUCTURED_OUTPUT, Capability.CODE_EXECUTION,
            Capability.MULTILINGUAL, Capability.REASONING
        ],
        cost_per_1m_input_usd=0.0,
        cost_per_1m_output_usd=0.0,
        max_context_tokens=128000,
        avg_latency_ms=8000,
        strength_tags=['general', 'coding', 'reasoning', 'long_context'],
        weakness_tags=['speed'],
    ),
    'opencode/nemotron-3-ultra-free': ModelProfile(
        id='opencode/nemotron-3-ultra-free',
        name='Nemotron 3 Ultra',
        capabilities=[
            Capability.LONG_CONTEXT, Capability.FUNCTION_CALLING,
            Capability.STRUCTURED_OUTPUT, Capability.REASONING
        ],
        cost_per_1m_input_usd=0.0,
        cost_per_1m_output_usd=0.0,
        max_context_tokens=128000,
        avg_latency_ms=6000,
        strength_tags=['reasoning', 'coding', 'analysis'],
        weakness_tags=['creative'],
    ),
    'opencode/deepseek-v4-flash-free': ModelProfile(
        id='opencode/deepseek-v4-flash-free',
        name='DeepSeek V4 Flash',
        capabilities=[
            Capability.CODE_EXECUTION, Capability.FUNCTION_CALLING,
            Capability.STRUCTURED_OUTPUT, Capability.SPEED
        ],
        cost_per_1m_input_usd=0.0,
        cost_per_1m_output_usd=0.0,
        max_context_tokens=64000,
        avg_latency_ms=3000,
        strength_tags=['coding', 'speed', 'debugging'],
        weakness_tags=['long_context', 'creative'],
    ),
    'opencode/mimo-v2.5-free': ModelProfile(
        id='opencode/mimo-v2.5-free',
        name='MiMo v2.5',
        capabilities=[
            Capability.MULTILINGUAL, Capability.CODE_EXECUTION,
            Capability.FUNCTION_CALLING, Capability.SPEED
        ],
        cost_per_1m_input_usd=0.0,
        cost_per_1m_output_usd=0.0,
        max_context_tokens=32768,
        avg_latency_ms=4000,
        strength_tags=['multilingual', 'coding', 'speed'],
        weakness_tags=['reasoning', 'long_context'],
    ),
    'opencode/laguna-s-2.1-free': ModelProfile(
        id='opencode/laguna-s-2.1-free',
        name='Laguna S 2.1',
        capabilities=[
            Capability.CREATIVE, Capability.MULTILINGUAL,
            Capability.LONG_CONTEXT
        ],
        cost_per_1m_input_usd=0.0,
        cost_per_1m_output_usd=0.0,
        max_context_tokens=64000,
        avg_latency_ms=7000,
        strength_tags=['creative', 'writing', 'multilingual'],
        weakness_tags=['coding', 'reasoning', 'structured_output'],
    ),
    'opencode/ling-3.0-flash-free': ModelProfile(
        id='opencode/ling-3.0-flash-free',
        name='Ling 3.0 Flash',
        capabilities=[
            Capability.SPEED, Capability.CODE_EXECUTION,
            Capability.FUNCTION_CALLING, Capability.STRUCTURED_OUTPUT
        ],
        cost_per_1m_input_usd=0.0,
        cost_per_1m_output_usd=0.0,
        max_context_tokens=32768,
        avg_latency_ms=2500,
        strength_tags=['speed', 'coding', 'structured_output'],
        weakness_tags=['reasoning', 'long_context', 'creative'],
    ),
    'opencode/north-mini-code-free': ModelProfile(
        id='opencode/north-mini-code-free',
        name='North Mini Code',
        capabilities=[
            Capability.CODE_EXECUTION, Capability.SPEED,
            Capability.FUNCTION_CALLING
        ],
        cost_per_1m_input_usd=0.0,
        cost_per_1m_output_usd=0.0,
        max_context_tokens=16384,
        avg_latency_ms=2000,
        strength_tags=['coding', 'speed', 'small_tasks'],
        weakness_tags=['reasoning', 'long_context', 'analysis'],
    ),
}


TASK_TYPE_DEFAULTS = {
    TaskType.CODING: RoutingRequest(
        task_type=TaskType.CODING,
        required_capabilities=[Capability.CODE_EXECUTION, Capability.FUNCTION_CALLING],
        preferred_capabilities=[Capability.STRUCTURED_OUTPUT, Capability.LONG_CONTEXT],
        priority="quality",
    ),
    TaskType.REASONING: RoutingRequest(
        task_type=TaskType.REASONING,
        required_capabilities=[Capability.REASONING],
        preferred_capabilities=[Capability.LONG_CONTEXT, Capability.STRUCTURED_OUTPUT],
        priority="quality",
    ),
    TaskType.CREATIVE: RoutingRequest(
        task_type=TaskType.CREATIVE,
        required_capabilities=[Capability.CREATIVE],
        preferred_capabilities=[Capability.MULTILINGUAL, Capability.LONG_CONTEXT],
        priority="quality",
    ),
    TaskType.ANALYSIS: RoutingRequest(
        task_type=TaskType.ANALYSIS,
        required_capabilities=[Capability.REASONING, Capability.LONG_CONTEXT],
        preferred_capabilities=[Capability.STRUCTURED_OUTPUT],
        priority="quality",
    ),
    TaskType.SUMMARIZATION: RoutingRequest(
        task_type=TaskType.SUMMARIZATION,
        required_capabilities=[Capability.LONG_CONTEXT],
        preferred_capabilities=[Capability.STRUCTURED_OUTPUT],
        priority="balanced",
    ),
    TaskType.TRANSLATION: RoutingRequest(
        task_type=TaskType.TRANSLATION,
        required_capabilities=[Capability.MULTILINGUAL],
        preferred_capabilities=[Capability.STRUCTURED_OUTPUT],
        priority="balanced",
    ),
    TaskType.CHAT: RoutingRequest(
        task_type=TaskType.CHAT,
        required_capabilities=[],
        preferred_capabilities=[Capability.SPEED],
        priority="speed",
    ),
    TaskType.PLANNING: RoutingRequest(
        task_type=TaskType.PLANNING,
        required_capabilities=[Capability.REASONING, Capability.STRUCTURED_OUTPUT],
        preferred_capabilities=[Capability.LONG_CONTEXT],
        priority="quality",
    ),
    TaskType.DEBUGGING: RoutingRequest(
        task_type=TaskType.DEBUGGING,
        required_capabilities=[Capability.CODE_EXECUTION, Capability.REASONING],
        preferred_capabilities=[Capability.STRUCTURED_OUTPUT, Capability.FUNCTION_CALLING],
        priority="quality",
    ),
    TaskType.ARCHITECTURE: RoutingRequest(
        task_type=TaskType.ARCHITECTURE,
        required_capabilities=[Capability.REASONING, Capability.LONG_CONTEXT, Capability.STRUCTURED_OUTPUT],
        preferred_capabilities=[Capability.FUNCTION_CALLING],
        priority="quality",
    ),
}


class LLMRouter:
    def __init__(self):
        self.profiles = MODEL_PROFILES
        self.routing_history: List[Dict[str, Any]] = []
        self.max_history = 200

    def route(self, request: RoutingRequest) -> RoutingDecision:
        monitor_state = load_monitor_state()
        monitor_config = monitor_state.get('config', {})
        monitor_modelos = monitor_state.get('modelos', {})

        candidates = self._filter_candidates(request, monitor_modelos)
        if not candidates:
            fallback = self._get_fallback_model(request.exclude_models)
            return RoutingDecision(
                model_id=fallback,
                confidence=0.3,
                reasoning="Nenhum modelo atende aos requisitos. Usando fallback.",
                estimated_cost_usd=0.0,
                estimated_latency_ms=self.profiles.get(fallback, ModelProfile('', '', [])).avg_latency_ms,
            )

        scored = self._score_candidates(candidates, request, monitor_modelos, monitor_config)
        scored.sort(key=lambda x: -x[1])

        best_model, best_score = scored[0]
        alternatives = [(m, s) for m, s in scored[1:4]]

        profile = self.profiles[best_model]
        decision = RoutingDecision(
            model_id=best_model,
            confidence=min(1.0, best_score / 100.0),
            reasoning=self._build_reasoning(request, best_model, best_score, profile, monitor_modelos),
            alternatives=alternatives,
            estimated_cost_usd=0.0,
            estimated_latency_ms=profile.avg_latency_ms,
        )

        self._record_routing(request, decision)
        return decision

    def _filter_candidates(
        self,
        request: RoutingRequest,
        monitor_modelos: Dict[str, Any],
    ) -> List[str]:
        candidates = []
        for model_id, profile in self.profiles.items():
            if model_id in request.exclude_models:
                continue
            if not profile.capabilities:
                continue

            has_required = all(cap in profile.capabilities for cap in request.required_capabilities)
            if not has_required:
                continue

            if request.min_context_tokens and profile.max_context_tokens < request.min_context_tokens:
                continue

            if request.max_latency_ms and profile.avg_latency_ms > request.max_latency_ms:
                continue

            if model_id in monitor_modelos:
                md = monitor_modelos[model_id]
                if md.get('requests_total', 0) >= 5:
                    taxa_erro = (md.get('requests_erro', 0) / md.get('requests_total', 1)) * 100
                    if taxa_erro > 50:
                        continue

            candidates.append(model_id)
        return candidates

    def _get_fallback_model(self, exclude: List[str]) -> str:
        for model_id in _obter_modelos_disponiveis():
            if model_id not in exclude:
                return model_id
        return 'opencode/big-pickle'

    def _score_candidates(
        self,
        candidates: List[str],
        request: RoutingRequest,
        monitor_modelos: Dict[str, Any],
        monitor_config: Dict[str, Any],
    ) -> List[Tuple[str, float]]:
        scored = []
        for model_id in candidates:
            profile = self.profiles[model_id]
            score = 0.0

            preferred_match = sum(1 for cap in request.preferred_capabilities if cap in profile.capabilities)
            score += preferred_match * 15

            for tag in profile.strength_tags:
                if tag in [request.task_type.value, 'general']:
                    score += 10

            for tag in profile.weakness_tags:
                if tag in [request.task_type.value]:
                    score -= 10

            if model_id in monitor_modelos:
                md = monitor_modelos[model_id]
                health_score = _calcular_score(md, monitor_config)
                score += health_score * 0.4

                if md.get('requests_total', 0) > 0:
                    latency_factor = max(0, 1 - (md.get('latencia_media_ms', 5000) / 20000))
                    score += latency_factor * 10
            else:
                score += 30

            if request.priority == "cost":
                score += (1 - (profile.cost_per_1m_input_usd + profile.cost_per_1m_output_usd) / 10) * 20
            elif request.priority == "speed":
                score += max(0, 1 - (profile.avg_latency_ms / 15000)) * 20
            elif request.priority == "quality":
                score += 10

            scored.append((model_id, max(0, score)))
        return scored

    def _build_reasoning(
        self,
        request: RoutingRequest,
        model_id: str,
        score: float,
        profile: ModelProfile,
        monitor_modelos: Dict[str, Any],
    ) -> str:
        reasons = []
        reasons.append(f"Tipo de tarefa: {request.task_type.value}")
        reasons.append(f"Prioridade: {request.priority}")
        reasons.append(f"Modelo: {profile.name} (score: {score:.1f})")
        reasons.append(f"Capabilities: {[c.value for c in profile.capabilities]}")

        if model_id in monitor_modelos:
            md = monitor_modelos[model_id]
            if md.get('requests_total', 0) > 0:
                reasons.append(f"Histórico: {md['requests_total']} reqs, {md['taxa_sucesso_pct']:.0f}% sucesso, {md['latencia_media_ms']:.0f}ms latência")
        else:
            reasons.append("Sem histórico de performance (modelo novo)")

        return " | ".join(reasons)

    def _record_routing(self, request: RoutingRequest, decision: RoutingDecision):
        record = {
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'task_type': request.task_type.value,
            'priority': request.priority,
            'selected_model': decision.model_id,
            'confidence': decision.confidence,
            'alternatives': decision.alternatives,
            'reasoning': decision.reasoning,
        }
        self.routing_history.append(record)
        if len(self.routing_history) > self.max_history:
            self.routing_history = self.routing_history[-self.max_history:]

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.routing_history[-limit:]

    def get_model_recommendations(self, task_type: TaskType) -> List[Dict[str, Any]]:
        request = TASK_TYPE_DEFAULTS.get(task_type, RoutingRequest(task_type=task_type))
        decision = self.route(request)
        result = [{
            'model': decision.model_id,
            'confidence': decision.confidence,
            'reasoning': decision.reasoning,
        }]
        for alt_model, alt_score in decision.alternatives:
            result.append({
                'model': alt_model,
                'confidence': alt_score / 100.0,
                'reasoning': f"Alternativa (score: {alt_score:.1f})",
            })
        return result


router = LLMRouter()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='LLM Router - Roteamento inteligente de modelos')
    sub = parser.add_subparsers(dest='cmd')

    p_route = sub.add_parser('route')
    p_route.add_argument('task_type', choices=[t.value for t in TaskType])
    p_route.add_argument('--priority', choices=['cost', 'speed', 'quality', 'balanced'], default='balanced')
    p_route.add_argument('--max-latency', type=int, default=None)
    p_route.add_argument('--min-context', type=int, default=None)
    p_route.add_argument('--exclude', nargs='*', default=[])
    p_route.add_argument('--require-cap', nargs='*', default=[])
    p_route.add_argument('--prefer-cap', nargs='*', default=[])

    sub.add_parser('recommendations')
    p_rec = sub.add_parser('recommend')
    p_rec.add_argument('task_type', choices=[t.value for t in TaskType])

    sub.add_parser('history')
    sub.add_parser('profiles')
    p_prof = sub.add_parser('profile')
    p_prof.add_argument('model_id')

    args = parser.parse_args()

    if args.cmd == 'route':
        req_caps = [Capability(c) for c in args.require_cap]
        pref_caps = [Capability(c) for c in args.prefer_cap]
        request = RoutingRequest(
            task_type=TaskType(args.task_type),
            required_capabilities=req_caps,
            preferred_capabilities=pref_caps,
            priority=args.priority,
            max_latency_ms=args.max_latency,
            min_context_tokens=args.min_context,
            exclude_models=args.exclude,
        )
        decision = router.route(request)
        print(f"Selected: {decision.model_id}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Reasoning: {decision.reasoning}")
        print(f"Estimated latency: {decision.estimated_latency_ms}ms")
        if decision.alternatives:
            print("Alternatives:")
            for m, s in decision.alternatives:
                print(f"  {m} (score: {s:.1f})")

    elif args.cmd == 'recommend' or args.cmd == 'recommendations':
        task = TaskType(args.task_type) if args.cmd == 'recommend' else TaskType.CODING
        recs = router.get_model_recommendations(task)
        for r in recs:
            print(f"{r['model']}: confidence={r['confidence']:.2f} - {r['reasoning']}")

    elif args.cmd == 'history':
        for h in router.get_history(20):
            print(f"{h['timestamp']} | {h['task_type']} | {h['selected_model']} | conf={h['confidence']:.2f}")

    elif args.cmd == 'profiles':
        for mid, profile in router.profiles.items():
            print(f"{mid}: caps={[c.value for c in profile.capabilities]}, latency={profile.avg_latency_ms}ms")

    elif args.cmd == 'profile':
        if args.model_id in router.profiles:
            p = router.profiles[args.model_id]
            print(json.dumps({
                'id': p.id,
                'name': p.name,
                'capabilities': [c.value for c in p.capabilities],
                'cost_input': p.cost_per_1m_input_usd,
                'cost_output': p.cost_per_1m_output_usd,
                'max_context': p.max_context_tokens,
                'avg_latency_ms': p.avg_latency_ms,
                'strengths': p.strength_tags,
                'weaknesses': p.weakness_tags,
            }, indent=2, ensure_ascii=False))
        else:
            print(f"Model {args.model_id} not found")

    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())