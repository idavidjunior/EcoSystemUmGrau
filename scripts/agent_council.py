"""Agent Council - Deliberação colaborativa com LLM real e paralelismo.

Versão 2.0: substitui respostas hardcoded por chamadas LLM reais.
Agentes independentes rod em paralelo (ThreadPool), respeitando quota NVIDIA (5 concorrentes).

Fluxo:
  Rodada 1: Agentes independentes (paralelo) → perspectivas iniciais
  Rodada 2: Agentes dependentes (paralelo) → refinam com base na rodada 1
  Rodada 3 (opcional): Revisão final se sem consenso

Agentes:
  01-Estrategista, 02-Cetico, 03-Realista, 04-Etica,
  05-Futuro, 06-Recursos, 07-Criativo, 08-Revisor, 11-LER-Executor
"""

import os
import sys
import json
import uuid
import time
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
COUNCIL_DIR = os.path.join(RUNTIME_DIR, 'agent_council')
sys.path.insert(0, SCRIPTS)

try:
    from llm_caller import call_llm, call_llm_json
except ImportError:
    def call_llm(prompt, system="", **kw):
        return ""
    def call_llm_json(prompt, system="", **kw):
        return {"_parse_error": "llm_caller not available"}


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
    AgentRole.ESTRATEGISTA: "Define direcao, objetivos e estrategia de alto nivel das solucoes",
    AgentRole.CETICO: "Desafia hipoteses, identifica riscos e evita conclusoes precipitadas",
    AgentRole.REALISTA: "Avalia viabilidade pratica, prazos e custos reais de implementacao",
    AgentRole.ETICA: "Avalia impactos eticos, legais, privacidade e conformidade",
    AgentRole.FUTURO: "Antecipa tendencias, evolucao tecnologica e escalabilidade futura",
    AgentRole.RECURSOS: "Mapeia recursos internos, bibliotecas, ferramentas e conhecimento reutilizavel",
    AgentRole.CRIATIVO: "Propoe solucoes inovadoras, alternativas nao obvias e abordagens criativas",
    AgentRole.REVISOR: "Revisa codigo, arquitetura, documentacao e consistencia tecnica",
    AgentRole.LER_EXECUTOR: "Delega tarefas complexas ao LER, garante execucao autonoma",
}

# Grupos de dependencia para paralelismo
# Rodada 1: independentes (podem rodar em paralelo)
INDEPENDENT_ROLES = [
    AgentRole.ESTRATEGISTA, AgentRole.CETICO, AgentRole.FUTURO,
    AgentRole.CRIATIVO, AgentRole.ETICA, AgentRole.RECURSOS,
]
# Rodada 2: dependentes da estrategia (podem rodar em paralelo entre si)
DEPENDENT_ROLES = [AgentRole.REALISTA, AgentRole.REVISOR]
# Rodada 3: executor (só se houver plano de execução)
EXECUTOR_ROLES = [AgentRole.LER_EXECUTOR]

MAX_PARALLEL_WORKERS = 5  # Limite NVIDIA quota (5 concorrentes)


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
    action_items: List[str] = field(default_factory=list)
    vote: str = "abstain"
    confidence: float = 0.5
    llm_model: str = ""
    response_time_ms: int = 0


@dataclass
class Deliberation:
    id: str
    topic: str
    context: str
    members: List[CouncilMember] = field(default_factory=list)
    status: DeliberationStatus = DeliberationStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    updated_at: str = ""
    consensus_reached: bool = False
    final_recommendation: str = ""
    dissenting_opinions: List[str] = field(default_factory=list)
    rounds: int = 0
    max_rounds: int = 3
    structured_output: Dict[str, Any] = field(default_factory=dict)


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
                            action_items=m.get('action_items', []),
                            vote=m.get('vote', 'abstain'),
                            confidence=m.get('confidence', 0.5),
                            llm_model=m.get('llm_model', ''),
                            response_time_ms=m.get('response_time_ms', 0),
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
                        structured_output=item.get('structured_output', {}),
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

    def _build_system_prompt(self, role: AgentRole) -> str:
        desc = AGENT_DESCRIPTIONS[role]
        return (
            f"Voce e o agente {role.value.upper()} de um conselho de engenharia.\n"
            f"Sua especialidade: {desc}\n\n"
            f"REGRAS:\n"
            f"- Responda SEMPRE em portugues do Brasil.\n"
            f"- Seja especifico e tecnico, nada generico.\n"
            f"- Cada preocupacao deve ter impacto real, nao teorico.\n"
            f"- Cada sugestao deve ser acionavel e concreta.\n"
            f"- Vote com base em evidencias, nao em suposicoes.\n"
            f"- Responda APENAS com JSON valido (sem markdown, sem explicacoes fora do JSON).\n"
        )

    def _build_round1_prompt(self, role: AgentRole, topic: str, context: str) -> str:
        return (
            f"TOPICO: {topic}\n"
            f"CONTEXTO: {context}\n\n"
            f"Analise este topico da perspectiva de {role.value.upper()}.\n"
            f"Gere um JSON com:\n"
            f'{{"perspective": "sua analise tecnica especifica (2-3 frases)",'
            f' "concerns": ["preocupacao com impacto real 1", "preocupacao 2"],'
            f' "suggestions": ["sugestao acionavel 1", "sugestao 2"],'
            f' "action_items": ["acao concreta a tomar 1", "acao 2"],'
            f' "vote": "aprovar|rejeitar|abster-se",'
            f' "confidence": 0.0 a 1.0}}'
        )

    def _build_round2_prompt(
        self, role: AgentRole, topic: str, context: str, round1_summary: str
    ) -> str:
        return (
            f"TOPICO: {topic}\n"
            f"CONTEXTO: {context}\n\n"
            f"RESUMO DA RODADA 1 (perspectivas dos outros agentes):\n{round1_summary}\n\n"
            f"Voce e o agente {role.value.upper()}.\n"
            f"Sua tarefa: {AGENT_DESCRIPTIONS[role]}\n\n"
            f"Refine sua analise considerando as perspectivas dos outros agentes acima.\n"
            f"Responda APENAS com JSON valido:\n"
            f'{{"perspective": "sua analise refinada (2-3 frases tecnicas)",'
            f' "concerns": ["preocupacao 1", "preocupacao 2"],'
            f' "suggestions": ["sugestao acionavel 1", "sugestao 2"],'
            f' "action_items": ["acao concreta 1", "acao 2"],'
            f' "vote": "aprovar|rejeitar|abster-se",'
            f' "confidence": 0.0 a 1.0}}'
        )

    def _call_agent(
        self, role: AgentRole, prompt: str, system: str = ""
    ) -> Tuple[CouncilMember, int]:
        """Chama LLM para um agente. Retorna (member, tempo_ms)."""
        start = time.time()
        sys_prompt = system or self._build_system_prompt(role)

        data = call_llm_json(
            prompt=prompt,
            system=sys_prompt,
            max_tokens=1024,
            temperature=0.3,
            timeout=30,
        )

        elapsed_ms = int((time.time() - start) * 1000)

        if "_parse_error" in data:
            # Fallback: tenta extrair informacao do texto cru
            raw = data.get("_raw", "")
            return CouncilMember(
                role=role,
                perspective=raw[:500] if raw else f"[LLM] Resposta nao estruturada para {role.value}",
                concerns=["Resposta do LLM nao foi parseada como JSON"],
                suggestions=[],
                vote="abster-se",
                confidence=0.3,
                response_time_ms=elapsed_ms,
            ), elapsed_ms

        return CouncilMember(
            role=role,
            perspective=data.get("perspective", ""),
            concerns=data.get("concerns", []),
            suggestions=data.get("suggestions", []),
            action_items=data.get("action_items", []),
            vote=data.get("vote", "abster-se"),
            confidence=min(1.0, max(0.0, float(data.get("confidence", 0.5)))),
            response_time_ms=elapsed_ms,
        ), elapsed_ms

    def _call_agents_parallel(
        self, agents: List[Tuple[AgentRole, str]], max_workers: int = MAX_PARALLEL_WORKERS
    ) -> Dict[AgentRole, CouncilMember]:
        """Chama multiplos agentes em paralelo. Respeita limite de workers."""
        results: Dict[AgentRole, CouncilMember] = {}
        system_prompts = {role: self._build_system_prompt(role) for role, _ in agents}

        def _worker(role: AgentRole, prompt: str) -> Tuple[AgentRole, CouncilMember]:
            member, _ = self._call_agent(role, prompt, system_prompts[role])
            return role, member

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_worker, role, prompt): role
                for role, prompt in agents
            }
            for future in concurrent.futures.as_completed(futures):
                role = futures[future]
                try:
                    r, member = future.result()
                    results[r] = member
                except Exception as e:
                    results[role] = CouncilMember(
                        role=role,
                        perspective=f"[ERRO] {type(e).__name__}: {e}",
                        vote="abster-se",
                        confidence=0.1,
                    )

        return results

    def _summarize_round(self, deliberation: Deliberation) -> str:
        lines = []
        for m in deliberation.members:
            if m.perspective:
                lines.append(
                    f"- {m.role.value}: {m.perspective[:200]} "
                    f"(voto: {m.vote}, confianca: {m.confidence:.1f})"
                )
                if m.concerns:
                    lines.append(f"  Preocupacoes: {'; '.join(m.concerns[:3])}")
                if m.suggestions:
                    lines.append(f"  Sugestoes: {'; '.join(m.suggestions[:3])}")
        return "\n".join(lines)

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
        all_actions = []
        for m in deliberation.members:
            all_suggestions.extend(m.suggestions)
            all_concerns.extend(m.concerns)
            all_actions.extend(m.action_items)

        votes = {"aprovar": 0, "rejeitar": 0, "abster-se": 0}
        for m in deliberation.members:
            votes[m.vote] += 1

        rec = f"DELIBERACAO #{deliberation.id} - {deliberation.topic}\n"
        rec += f"Status: {'CONSENSO' if deliberation.consensus_reached else 'SEM CONSENSO'}\n"
        rec += f"Votos: {votes}\n"
        rec += f"Rodadas: {deliberation.rounds}\n\n"

        rec += "Perspectivas:\n"
        for m in deliberation.members:
            if m.perspective:
                rec += f"  [{m.role.value}] {m.perspective[:300]}\n"

        rec += "\nSugestoes consolidadas:\n"
        for s in list(dict.fromkeys(all_suggestions))[:10]:
            rec += f"  - {s}\n"

        rec += "\nPreocupacoes:\n"
        for c in list(dict.fromkeys(all_concerns))[:10]:
            rec += f"  ! {c}\n"

        if all_actions:
            rec += "\nAcoes concretas:\n"
            for a in list(dict.fromkeys(all_actions))[:10]:
                rec += f"  > {a}\n"

        return rec

    def _build_structured_output(self, deliberation: Deliberation) -> Dict[str, Any]:
        """Gera output estruturado para o council_orchestrator consumir."""
        votes = {"aprovar": 0, "rejeitar": 0, "abster-se": 0}
        for m in deliberation.members:
            votes[m.vote] += 1

        approved = votes["aprovar"] > votes["rejeitar"]

        all_suggestions = []
        all_concerns = []
        all_actions = []
        for m in deliberation.members:
            all_suggestions.extend(m.suggestions)
            all_concerns.extend(m.concerns)
            all_actions.extend(m.action_items)

        # Mapeia quais agentes aprovaram para decidir proximos passos
        approved_by = [m.role.value for m in deliberation.members if m.vote == "aprovar"]
        rejected_by = [m.role.value for m in deliberation.members if m.vote == "rejeitar"]

        return {
            "deliberation_id": deliberation.id,
            "topic": deliberation.topic,
            "approved": approved,
            "consensus": deliberation.consensus_reached,
            "votes": votes,
            "approved_by": approved_by,
            "rejected_by": rejected_by,
            "suggestions": list(dict.fromkeys(all_suggestions)),
            "concerns": list(dict.fromkeys(all_concerns)),
            "action_items": list(dict.fromkeys(all_actions)),
            "member_perspectives": {
                m.role.value: {
                    "perspective": m.perspective,
                    "confidence": m.confidence,
                    "response_time_ms": m.response_time_ms,
                }
                for m in deliberation.members
            },
        }

    def deliberate(
        self,
        topic: str,
        context: str,
        required_roles: List[AgentRole] = None,
        max_rounds: int = 2,
        use_llm: bool = True,
    ) -> Deliberation:
        """Delibera sobre um topico usando LLM real com paralelismo.

        Args:
            topic: O que esta sendo decidido
            context: Informacoes relevantes para a decisao
            required_roles: Quais agentes participam (default: independentes + dependentes)
            max_rounds: Maximo de rodadas de deliberacao
            use_llm: Se False, usa respostas simuladas (fallback)

        Returns:
            Deliberation com resultado
        """
        deliberation_id = str(uuid.uuid4())[:8]

        if required_roles is None:
            required_roles = INDEPENDENT_ROLES + DEPENDENT_ROLES

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
            round1_summary = self._summarize_round(deliberation) if round_num > 1 else ""

            if use_llm:
                self._deliberate_round_llm(deliberation, round_num, round1_summary)
            else:
                self._deliberate_round_simulated(deliberation, round_num, round1_summary)

            self._save()

            if self._check_consensus(deliberation):
                deliberation.status = DeliberationStatus.CONSENSUS
                deliberation.consensus_reached = True
                break

        if not deliberation.consensus_reached:
            deliberation.status = DeliberationStatus.NO_CONSENSUS

        deliberation.final_recommendation = self._build_recommendation(deliberation)
        deliberation.structured_output = self._build_structured_output(deliberation)
        deliberation.dissenting_opinions = self._collect_dissent(deliberation)
        deliberation.updated_at = datetime.now().isoformat(timespec='seconds')
        self._save()
        return deliberation

    def _deliberate_round_llm(
        self, deliberation: Deliberation, round_num: int, previous_summary: str
    ):
        """Executa uma rodada de deliberacao com LLM real + paralelismo."""
        # Separa agentes por grupo de dependencia
        present_roles = {m.role for m in deliberation.members}
        round_independent = [r for r in INDEPENDENT_ROLES if r in present_roles]
        round_dependent = [r for r in DEPENDENT_ROLES if r in present_roles]

        # Rodada 1: agentes independentes em paralelo
        if round_num == 1 and round_independent:
            agents_to_call = [
                (role, self._build_round1_prompt(role, deliberation.topic, deliberation.context))
                for role in round_independent
            ]
            print(f"[Council] Rodada 1: chamando {len(agents_to_call)} agentes em paralelo...")
            results = self._call_agents_parallel(agents_to_call)
            for role, member in results.items():
                self._update_member(deliberation, member)

        # Rodada 2: agentes dependentes em paralelo (com contexto da rodada 1)
        if round_dependent:
            agents_to_call = [
                (role, self._build_round2_prompt(role, deliberation.topic, deliberation.context, previous_summary))
                for role in round_dependent
            ]
            print(f"[Council] Rodada {round_num}: chamando {len(agents_to_call)} agentes dependentes...")
            results = self._call_agents_parallel(agents_to_call)
            for role, member in results.items():
                self._update_member(deliberation, member)

        # Rodadas adicionais: todos refinam
        if round_num > 2:
            all_present = [r for r in INDEPENDENT_ROLES + DEPENDENT_ROLES if r in present_roles]
            agents_to_call = [
                (role, self._build_round2_prompt(role, deliberation.topic, deliberation.context, previous_summary))
                for role in all_present
            ]
            print(f"[Council] Rodada {round_num}: refinamento coletivo ({len(agents_to_call)} agentes)...")
            results = self._call_agents_parallel(agents_to_call)
            for role, member in results.items():
                self._update_member(deliberation, member)

    def _deliberate_round_simulated(
        self, deliberation: Deliberation, round_num: int, previous_summary: str
    ):
        """Fallback: respostas simuladas (quando LLM indisponivel)."""
        for member in deliberation.members:
            member.perspective = f"[SIMULADO] {member.role.value}: analise de {deliberation.topic}"
            member.concerns = ["Resposta simulada - LLM indisponivel"]
            member.suggestions = ["Verificar conectividade com LLM"]
            member.vote = "aprovar"
            member.confidence = 0.5

    def _update_member(self, deliberation: Deliberation, new_member: CouncilMember):
        """Atualiza dados de um membro na deliberacao."""
        for i, m in enumerate(deliberation.members):
            if m.role == new_member.role:
                deliberation.members[i] = new_member
                return

    def _collect_dissent(self, deliberation: Deliberation) -> List[str]:
        dissent = []
        for m in deliberation.members:
            if m.vote == "rejeitar" or (m.vote == "abster-se" and m.concerns):
                dissent.append(f"{m.role.value}: {'; '.join(m.concerns[:2])}")
        return dissent

    def get_deliberation(self, deliberation_id: str) -> Optional[Deliberation]:
        return self.deliberations.get(deliberation_id)

    def list_deliberations(self, limit: int = 20) -> List[Deliberation]:
        return list(self.deliberations.values())[-limit:]

    def get_agent_prompt(self, role: AgentRole, topic: str, context: str) -> str:
        return self._build_round1_prompt(role, topic, context)

    def stats(self) -> Dict[str, Any]:
        total = len(self.deliberations)
        consensus = sum(1 for d in self.deliberations.values() if d.consensus_reached)
        return {
            'total_deliberations': total,
            'consensus_reached': consensus,
            'consensus_rate': round(consensus / total * 100, 1) if total > 0 else 0,
        }

    def escolher_saliente(self, members: List[CouncilMember]) -> Tuple[Optional[CouncilMember], str]:
        """Saliência multi-agente (padrão heardlabs/heard).

        Entre vários agentes com perspectivas diferentes, escolhe O mais saliente
        para narrar/responder e devolve um resumo dos demais. Prioridade:
          1. voto contrário (bloqueio/oposição) — precisa ser ouvido primeiro
          2. abstenção com preocupações (risco não resolvido)
          3. qualquer preocupação (dúvida com impacto)
          4. com sugestões/ações (proposta concreta)
          5. demais (perspectiva informativa)

        Retorna (membro_saliente, resumo_dos_demais).
        """
        if not members:
            return None, ""

        def peso(m: CouncilMember) -> int:
            if m.vote == "rejeitar":
                return 5
            if m.vote == "abster-se" and m.concerns:
                return 4
            if m.concerns:
                return 3
            if m.suggestions or m.action_items:
                return 2
            return 1

        ordenados = sorted(members, key=peso, reverse=True)
        saliente = ordenados[0]
        demais = ordenados[1:]

        rotulo = {
            5: "bloqueio/oposição",
            4: "risco não resolvido",
            3: "preocupação com impacto",
            2: "proposta concreta",
            1: "informativo",
        }.get(peso(saliente), "informativo")

        if not demais:
            return saliente, rotulo
        linhas = [f"[{m.role.value}] {m.perspective[:120]} (voto: {m.vote}, confiança: {m.confidence:.1f})" for m in demais if m.perspective]
        return saliente, rotulo + " | outros: " + " || ".join(linhas[:3])

    def narrar_saliencia(self, deliberation: Deliberation) -> str:
        """Texto pronto para narração/voz da deliberação: o saliente em detalhe,
        os demais em resumo de uma linha. Usado pelo narrador para não falar
        todos os agentes igualmente (um fala, os outros resumem)."""
        saliente, resumo = self.escolher_saliente(deliberation.members)
        if saliente is None:
            return ""
        texto = f"{saliente.role.value.upper()}: {saliente.perspective}"
        if saliente.concerns:
            texto += f". Preocupações: {'; '.join(saliente.concerns[:2])}."
        if saliente.suggestions:
            texto += f" Sugestão: {saliente.suggestions[0]}."
        if resumo:
            texto += f" {resumo}"
        return texto[:600]


council = AgentCouncil()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Agent Council - Deliberacao colaborativa com LLM real')
    sub = parser.add_subparsers(dest='cmd')

    p_delib = sub.add_parser('deliberate')
    p_delib.add_argument('topic')
    p_delib.add_argument('context')
    p_delib.add_argument('--roles', nargs='*', default=[])
    p_delib.add_argument('--rounds', type=int, default=2)
    p_delib.add_argument('--no-llm', action='store_true', help='Usar respostas simuladas')

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
        result = council.deliberate(
            args.topic, args.context,
            required_roles=roles, max_rounds=args.rounds,
            use_llm=not args.no_llm,
        )
        print(f"Deliberation ID: {result.id}")
        print(f"Status: {result.status.value}")
        print(f"Consensus: {result.consensus_reached}")
        print(f"Rounds: {result.rounds}")
        print(f"\n{result.final_recommendation}")
        if result.dissenting_opinions:
            print("\nOpinioes divergentes:")
            for d in result.dissenting_opinions:
                print(f"  - {d}")
        # Output estruturado para orquestrador
        print(f"\n--- STRUCTURED OUTPUT ---")
        print(json.dumps(result.structured_output, indent=2, ensure_ascii=False))

    elif args.cmd == 'get':
        d = council.get_deliberation(args.deliberation_id)
        if d:
            print(json.dumps({
                'id': d.id,
                'topic': d.topic,
                'status': d.status.value,
                'consensus': d.consensus_reached,
                'recommendation': d.final_recommendation,
                'structured_output': d.structured_output,
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
