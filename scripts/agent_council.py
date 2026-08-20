"""Agent Council - Mecanismo de deliberação colaborativa entre agentes.

Permite que múltiplos agentes especializados discutam uma tarefa complexa,
cheguem a consenso, e produzam uma recomendação unificada.

Agentes disponíveis no ecossistema:
- 01-Estrategista: Define direção, objetivos, estratégia de alto nível
- 02-Cetico: Desafia hipóteses, identifica riscos, evita conclusões precipitadas
- 03-Realista: Avalia viabilidade prática, prazos, custos reais
- 04-Etica: Avalia impactos éticos, legais, privacidade, conformidade
- 05-Futuro: Antecipa tendências, evolução tecnológica, escalabilidade
- 06-Recursos: Mapeia recursos internos, bibliotecas, ferramentas reutilizáveis
- 07-Criativo: Propõe soluções inovadoras, alternativas não óbvias
- 08-Revisor: Revisa código, arquitetura, documentação, consistência técnica
- 11-LER-Executor: Delega tarefas complexas ao LER, garante execução autônoma
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
COUNCIL_DIR = os.path.join(RUNTIME_DIR, 'agent_council')
sys.path.insert(0, SCRIPTS)

try:
    from runtime_state import load_state, save_state
except ImportError:
    def load_state():
        return {}
    def save_state(state):
        pass


class AgentRole(Enum):
    ESTRATEGISTA = "01-estrategista"
    CETICO = "02-cetico"
    REALISTA = "03-realista"
    ETICA = "04-etica"
    FUTURO = "05-futuro"
    RECURSOS = "06-recursos"
    CRIATIVO = "07-criativo"
    REVISOR = "08-revisor"
    LER_EXECUTOR = "11-ler-executor"


AGENT_DESCRIPTIONS = {
    AgentRole.ESTRATEGISTA: "Define direção, objetivos e estratégia de alto nível das soluções",
    AgentRole.CETICO: "Desafia hipóteses, identifica riscos e evita conclusões precipitadas",
    AgentRole.REALISTA: "Avalia viabilidade prática, prazos e custos reais de implementação",
    AgentRole.ETICA: "Avalia impactos éticos, legais, de privacidade e conformidade",
    AgentRole.FUTURO: "Antecipa tendências, evolução tecnológica e escalabilidade futura",
    AgentRole.RECURSOS: "Mapeia recursos internos, bibliotecas, ferramentas e conhecimento reutilizável",
    AgentRole.CRIATIVO: "Propõe soluções inovadoras, alternativas não óbvias e abordagens criativas",
    AgentRole.REVISOR: "Revisa código, arquitetura, documentação e consistência técnica",
    AgentRole.LER_EXECUTOR: "Delega tarefas complexas ao LER e garante execução autônoma",
}


class DeliberationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONSENSUS = "consensus"
    NO_CONSENSUS = "no_consensus"
    TIMEOUT = "timeout"


@dataclass
class CouncilMember:
    role: AgentRole
    perspective: str = ""
    concerns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    vote: str = "abstain"  # approve, reject, abstain
    confidence: float = 0.5


@dataclass
class Deliberation:
    id: str
    topic: str
    context: str
    members: List[CouncilMember] = field(default_factory=list)
    status: DeliberationStatus = DeliberationStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    consensus_reached: bool = False
    final_recommendation: str = ""
    dissenting_opinions: List[str] = field(default_factory=list)
    rounds: int = 0
    max_rounds: int = 3


class AgentCouncil:
    def __init__(self):
        self.deliberations: Dict[str, Deliberation] = {}
        self.max_history = 100
        self._load()

    def _get_storage_path(self):
        return os.path.join(COUNCIL_DIR, 'deliberations.json')

    def _ensure_dirs(self):
        os.makedirs(COUNCIL_DIR, exist_ok=True)

    def _load(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    members = [
                        CouncilMember(
                            role=AgentRole(m['role']),
                            perspective=m.get('perspective', ''),
                            concerns=m.get('concerns', []),
                            suggestions=m.get('suggestions', []),
                            vote=m.get('vote', 'abstain'),
                            confidence=m.get('confidence', 0.5),
                        )
                        for m in item.get('members', [])
                    ]
                    self.deliberations[item['id']] = Deliberation(
                        id=item['id'],
                        topic=item['topic'],
                        context=item['context'],
                        members=members,
                        status=DeliberationStatus(item.get('status', 'pending')),
                        created_at=item.get('created_at', ''),
                        updated_at=item.get('updated_at', ''),
                        consensus_reached=item.get('consensus_reached', False),
                        final_recommendation=item.get('final_recommendation', ''),
                        dissenting_opinions=item.get('dissenting_opinions', []),
                        rounds=item.get('rounds', 0),
                        max_rounds=item.get('max_rounds', 3),
                    )
            except Exception as e:
                print(f"[Council] Erro ao carregar: {e}")

    def _save(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        try:
            tmp = path + '.tmp'
            data = []
            for d in list(self.deliberations.values())[-self.max_history:]:
                item = asdict(d)
                item['members'] = [asdict(m) for m in d.members]
                item['status'] = d.status.value
                item['members'] = [
                    {**asdict(m), 'role': m.role.value}
                    for m in d.members
                ]
                data.append(item)
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            print(f"[Council] Erro ao salvar: {e}")

    def _get_agent_prompt(self, role: AgentRole, topic: str, context: str, previous_input: str = "") -> str:
        desc = AGENT_DESCRIPTIONS[role]
        base = f"""Você é o agente {role.value.upper()}: {desc}.

Tópico em discussão: {topic}
Contexto: {context}

{f"Entrada anterior da discussão: {previous_input}" if previous_input else ""}

Forneça sua perspectiva única, preocupações, sugestões e um voto (aprovar/rejeitar/abster-se) com nível de confiança (0-1).
Responda em formato JSON:
{{
  "perspective": "sua visão única sobre o tema",
  "concerns": ["preocupação 1", "preocupação 2"],
  "suggestions": ["sugestão 1", "sugestão 2"],
  "vote": "aprovar|rejeitar|abster-se",
  "confidence": 0.8
}}"""
        return base

    def _simulate_agent_response(self, role: AgentRole, topic: str, context: str, previous: str = "") -> CouncilMember:
        responses = {
            AgentRole.ESTRATEGISTA: {
                "perspective": f"Estrategicamente, {topic} deve alinhar com objetivos de longo prazo do ecossistema",
                "concerns": ["Desvio da missão principal", "Complexidade desnecessária"],
                "suggestions": ["Definir métricas de sucesso claras", "Planejar fases de entrega"],
                "vote": "aprovar",
                "confidence": 0.8,
            },
            AgentRole.CETICO: {
                "perspective": f"Precisamos questionar se {topic} realmente resolve o problema ou cria mais complexidade",
                "concerns": ["Falta de validação de hipóteses", "Risco de over-engineering", "Premissas não validadas"],
                "suggestions": ["Prova de conceito primeiro", "Definir critérios de falha"],
                "vote": "abster-se",
                "confidence": 0.6,
            },
            AgentRole.REALISTA: {
                "perspective": f"Viabilidade prática de {topic}: esforço estimado, dependências, recursos necessários",
                "concerns": ["Prazo irrealista", "Recursos insuficientes", "Dívida técnica"],
                "suggestions": ["MVP em 2 semanas", "Reutilizar componentes existentes"],
                "vote": "aprovar",
                "confidence": 0.7,
            },
            AgentRole.ETICA: {
                "perspective": f"Impactos éticos de {topic}: privacidade, segurança, acessibilidade, conformidade",
                "concerns": ["Dados sensíveis expostos", "Viés em decisões automatizadas"],
                "suggestions": ["Auditoria de privacidade", "Testes de acessibilidade"],
                "vote": "aprovar",
                "confidence": 0.9,
            },
            AgentRole.FUTURO: {
                "perspective": f"Evolução de {topic}: escalabilidade, manutenibilidade, tendências tecnológicas",
                "concerns": ["Lock-in tecnológico", "Obsolescência rápida"],
                "suggestions": ["Arquitetura modular", "Interfaces estáveis"],
                "vote": "aprovar",
                "confidence": 0.75,
            },
            AgentRole.RECURSOS: {
                "perspective": f"Recursos disponíveis para {topic}: código existente, skills, ferramentas, documentação",
                "concerns": ["Duplicação de esforço", "Lacunas de conhecimento"],
                "suggestions": ["Reutilizar module X", "Consultar skill Y"],
                "vote": "aprovar",
                "confidence": 0.85,
            },
            AgentRole.CRIATIVO: {
                "perspective": f"Abordagens alternativas para {topic}: soluções não óbvias, inovação lateral",
                "concerns": ["Solução convencional limita potencial"],
                "suggestions": ["Abordagem híbrida", "Experimentar técnica Z"],
                "vote": "aprovar",
                "confidence": 0.7,
            },
            AgentRole.REVISOR: {
                "perspective": f"Revisão técnica de {topic}: arquitetura, código, documentação, consistência",
                "concerns": ["Acoplamento excessivo", "Falta de testes", "Documentação ausente"],
                "suggestions": ["Adicionar testes de contrato", "Documentar decisões"],
                "vote": "aprovar",
                "confidence": 0.8,
            },
            AgentRole.LER_EXECUTOR: {
                "perspective": f"Execução autônoma de {topic} via LER: decomposição, loops, checkpoints",
                "concerns": ["Tarefa muito complexa para uma iteração", "Dependências circulares"],
                "suggestions": ["Dividir em subtarefas LER", "Definir checkpoints claros"],
                "vote": "aprovar",
                "confidence": 0.75,
            },
        }
        resp = responses.get(role, responses[AgentRole.ESTRATEGISTA])
        return CouncilMember(role=role, **resp)

    def deliberate(
        self,
        topic: str,
        context: str,
        required_roles: List[AgentRole] = None,
        max_rounds: int = 3,
        auto_simulate: bool = True,
    ) -> Deliberation:
        deliberation_id = str(uuid.uuid4())[:8]

        if required_roles is None:
            required_roles = [
                AgentRole.ESTRATEGISTA,
                AgentRole.CETICO,
                AgentRole.REALISTA,
                AgentRole.ETICA,
                AgentRole.RECURSOS,
                AgentRole.REVISOR,
            ]

        members = [CouncilMember(role=r) for r in required_roles]

        deliberation = Deliberation(
            id=deliberation_id,
            topic=topic,
            context=context,
            members=members,
            status=DeliberationStatus.IN_PROGRESS,
            max_rounds=max_rounds,
        )

        self.deliberations[deliberation_id] = deliberation

        for round_num in range(1, max_rounds + 1):
            deliberation.rounds = round_num
            previous_summary = self._summarize_round(deliberation, round_num - 1) if round_num > 1 else ""

            for member in deliberation.members:
                if auto_simulate:
                    response = self._simulate_agent_response(member.role, topic, context, previous_summary)
                    member.perspective = response.perspective
                    member.concerns = response.concerns
                    member.suggestions = response.suggestions
                    member.vote = response.vote
                    member.confidence = response.confidence

            self._save()

            if self._check_consensus(deliberation):
                deliberation.status = DeliberationStatus.CONSENSUS
                deliberation.consensus_reached = True
                deliberation.final_recommendation = self._build_recommendation(deliberation)
                break

        if not deliberation.consensus_reached:
            deliberation.status = DeliberationStatus.NO_CONSENSUS
            deliberation.final_recommendation = self._build_recommendation(deliberation)
            deliberation.dissenting_opinions = self._collect_dissent(deliberation)

        deliberation.updated_at = datetime.now().isoformat(timespec='seconds')
        self._save()
        return deliberation

    def _summarize_round(self, deliberation: Deliberation, round_num: int) -> str:
        if round_num == 0:
            return ""
        summaries = []
        for m in deliberation.members:
            if m.perspective:
                summaries.append(f"{m.role.value}: {m.perspective[:100]} (vote: {m.vote})")
        return "; ".join(summaries)

    def _check_consensus(self, deliberation: Deliberation) -> bool:
        votes = [m.vote for m in deliberation.members if m.vote != "abstain"]
        if not votes:
            return False
        approve = votes.count("aprovar")
        reject = votes.count("rejeitar")
        total = len(votes)
        return approve / total >= 0.66 and reject == 0

    def _build_recommendation(self, deliberation: Deliberation) -> str:
        all_suggestions = []
        all_concerns = []
        for m in deliberation.members:
            all_suggestions.extend(m.suggestions)
            all_concerns.extend(m.concerns)

        votes = {"aprovar": 0, "rejeitar": 0, "abster-se": 0}
        for m in deliberation.members:
            votes[m.vote] += 1

        rec = f"DELIBERAÇÃO #{deliberation.id} - {deliberation.topic}\n"
        rec += f"Status: {'CONSENSO' if deliberation.consensus_reached else 'SEM CONSENSO'}\n"
        rec += f"Votos: {votes}\n\n"
        rec += "Principais sugestões:\n"
        for s in list(dict.fromkeys(all_suggestions))[:10]:
            rec += f"  • {s}\n"
        rec += "\nPrincipais preocupações:\n"
        for c in list(dict.fromkeys(all_concerns))[:10]:
            rec += f"  ⚠ {c}\n"
        return rec

    def _collect_dissent(self, deliberation: Deliberation) -> List[str]:
        dissent = []
        for m in deliberation.members:
            if m.vote == "rejeitar" or (m.vote == "abster-se" and m.concerns):
                dissent.append(f"{m.role.value}: {', '.join(m.concerns[:2])}")
        return dissent

    def get_deliberation(self, deliberation_id: str) -> Optional[Deliberation]:
        return self.deliberations.get(deliberation_id)

    def list_deliberations(self, limit: int = 20) -> List[Deliberation]:
        return list(self.deliberations.values())[-limit:]

    def get_agent_prompt(self, role: AgentRole, topic: str, context: str) -> str:
        return self._get_agent_prompt(role, topic, context)

    def stats(self) -> Dict[str, Any]:
        total = len(self.deliberations)
        consensus = sum(1 for d in self.deliberations.values() if d.consensus_reached)
        return {
            'total_deliberations': total,
            'consensus_reached': consensus,
            'consensus_rate': round(consensus / total * 100, 1) if total > 0 else 0,
        }


council = AgentCouncil()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Agent Council - Deliberação colaborativa')
    sub = parser.add_subparsers(dest='cmd')

    p_delib = sub.add_parser('deliberate')
    p_delib.add_argument('topic')
    p_delib.add_argument('context')
    p_delib.add_argument('--roles', nargs='*', default=[])
    p_delib.add_argument('--rounds', type=int, default=3)

    p_get = sub.add_parser('get')
    p_get.add_argument('deliberation_id')

    p_list = sub.add_parser('list')
    p_list.add_argument('--limit', type=int, default=20)

    p_prompt = sub.add_parser('prompt')
    p_prompt.add_argument('role', choices=[r.value for r in AgentRole])
    p_prompt.add_argument('topic')
    p_prompt.add_argument('context')

    p_stats = sub.add_parser('stats')

    args = parser.parse_args()

    if args.cmd == 'deliberate':
        roles = [AgentRole(r) for r in args.roles] if args.roles else None
        result = council.deliberate(args.topic, args.context, required_roles=roles, max_rounds=args.rounds)
        print(f"Deliberation ID: {result.id}")
        print(f"Status: {result.status.value}")
        print(f"Consensus: {result.consensus_reached}")
        print(f"Rounds: {result.rounds}")
        print(f"\n{result.final_recommendation}")
        if result.dissenting_opinions:
            print("\nOpiniões divergentes:")
            for d in result.dissenting_opinions:
                print(f"  - {d}")

    elif args.cmd == 'get':
        d = council.get_deliberation(args.deliberation_id)
        if d:
            print(json.dumps({
                'id': d.id,
                'topic': d.topic,
                'status': d.status.value,
                'consensus': d.consensus_reached,
                'recommendation': d.final_recommendation,
            }, indent=2, ensure_ascii=False))
        else:
            print("Not found")

    elif args.cmd == 'list':
        for d in council.list_deliberations(args.limit):
            print(f"{d.id} | {d.topic[:50]} | {d.status.value} | consensus={d.consensus_reached}")

    elif args.cmd == 'prompt':
        prompt = council.get_agent_prompt(AgentRole(args.role), args.topic, args.context)
        print(prompt)

    elif args.cmd == 'stats':
        print(json.dumps(council.stats(), indent=2, ensure_ascii=False))

    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())