"""PAIS — orquestrador e CLI.

Pipeline de resposta (protocolo do PAIS):
ENTENDER -> INTENCAO -> CONTEXTO -> USER MODEL -> AFIRMACOES -> CONFIANCA ->
PESQUISA? -> EVIDENCIA -> CONTRADICOES -> CONCLUSAO -> ANTI-BAJULACAO ->
ANTI-ALUCINACAO -> PERSONALIZAR FORMA -> REGISTRAR FEEDBACK.

Uso:
  python mcp/nucleo/habilidades/pais/cli.py observe "<mensagem do usuario>"
  python mcp/nucleo/habilidades/pais/cli.py profile
  python mcp/nucleo/habilidades/pais/cli.py predict
  python mcp/nucleo/habilidades/pais/cli.py feedback "<mensagem de retorno do usuario>"
  python mcp/nucleo/habilidades/pais/cli.py report
  python mcp/nucleo/habilidades/pais/cli.py review "<texto da resposta>"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pais import observer, profilers, interaction, memory, learning, epistemic
from pais import prediction, guards, adaptation, audit
from pais.storage import Store
from pais.models import Confidence, EvidenceStatus


class PAIS:
    def __init__(self, store: Store = None):
        self.store = store or Store()
        self.observer = observer
        self.interaction_model = interaction.InteractionModel(self.store)
        self.intent = interaction.IntentPredictor()
        self.response_prefs = interaction.ResponsePreferenceModel()
        self.episodic = memory.EpisodicMemory(self.store)
        self.sem = memory.SemanticUserModel(self.store)
        self.patterns = learning.PatternLearningEngine(self.store)
        self.feedback_engine = learning.FeedbackLearningEngine()
        self.evidence = epistemic.EvidenceEngine()
        self.contradictions = epistemic.ContradictionDetector()
        self.uncertainty = epistemic.UncertaintyEngine()
        self.integrity = epistemic.EpistemicIntegrityEngine(self.store)
        self.anti_syc = guards.AntiSycophancyGuard()
        self.halluc = guards.HallucinationGuard()
        self.research = guards.ResearchDecisionEngine()
        self.predictor = prediction.PredictionEngine(self.store)
        self.adaptation = adaptation.AdaptationController(self.store)
        self.audit = audit.AuditGovernance(self.store)

    def observe(self, message: str) -> dict:
        """Passo central: observa, perfiliza, consolida e prevê."""
        oi = self.observer.observe(message)
        intent_res = self.intent.predict(message)

        # Perfis
        ling = self.store.user().setdefault("linguistic_profile", {})
        profilers.LinguisticProfiler().update(ling, message)
        reas = self.store.user().setdefault("reasoning_profile", {})
        profilers.ReasoningProfiler().update(reas, message)

        # Preferências (probabilísticas)
        prefs = self.store.user().setdefault("preferences", {})
        profilers.PreferenceModel.update(prefs, ling, message)

        # Fatos/padrões (com confiança)
        if oi.is_decision:
            self.sem.observe("padrao.decisao", "toma decisoes explicitas", "patterns",
                             "interaction", Confidence.MEDIUM_CONFIDENCE)
        if oi.is_imperative:
            self.sem.observe("padrao.imperativo", "prefere pedidos de acao", "patterns",
                             "interaction", Confidence.LOW_CONFIDENCE)
        if oi.is_knowledge_query:
            self.sem.observe("padrao.pede_esclarecimento", "pergunta para entender", "patterns",
                             "interaction", Confidence.LOW_CONFIDENCE)
        if oi.has_uncertainty:
            self.sem.observe("padrao.expressa_incerteza", "expressa duvida com frequencia",
                             "patterns", "interaction", Confidence.LOW_CONFIDENCE)

        # Interação + tópicos
        topics = self.observer.extract_topics(message, self.store.user().get("frequent_topics", []))
        self.interaction_model.record(message, intent_res["intent"], oi.__dict__)
        self.patterns.consolidate_topics(topics)

        # Registro de afirmação quando há verbo factual + substantivo
        self._register_claim_if_factual(message)

        # Previsão do próximo passo
        pred = self.predictor.predict_next(intent_res["intent"])

        self.store.save_user()
        self.store.save_epistemic()
        return {
            "observado": oi.__dict__,
            "intencao": intent_res,
            "linguistico": ling,
            "raciocinio": reas,
            "preferencias": prefs,
            "topicos": topics,
            "previsao_proximo_passo": pred,
            "adaptacao": self.adaptation.guidance(),
        }

    def _register_claim_if_factual(self, message: str) -> None:
        if not self._looks_factual(message):
            return
        claim = self.evidence.register(
            self.store, message, source="user", source_quality="unknown",
            support=EvidenceStatus.UNKNOWN, confidence=0.1)
        self.store.epistemic().setdefault("uncertainties", []).append(claim.to_dict())

    @staticmethod
    def _looks_factual(message: str) -> bool:
        import re
        return bool(re.search(r"(suporta|funciona|é compatível|e compativel|é assim|"
                              r"é verdade|e verdade|custa|versão|versao|data|lança|lanca)",
                              message.lower()))

    def feedback(self, message: str) -> dict:
        kind = self.feedback_engine.classify(message)
        self.feedback_engine.apply(self.store, kind)
        learning.FeedbackKindUtil.note_occurrence(self.store, kind)
        self.store.save_epistemic()
        return {"feedback": kind.value}

    def review(self, response: str, user_message: str = "", actually_done: list = None) -> dict:
        """Passos 11-12 do protocolo: auditoria anti-bajulação e anti-alucinação."""
        syc = self.anti_syc.check(user_message, response)
        hal = self.halluc.check(response, actually_done)
        integrity = self.integrity.review(response)
        for g in (syc, hal):
            self.audit.audit_log(g)
        return {
            "anti_bajulacao": syc,
            "anti_alucinacao": hal,
            "integridade": integrity,
            "aprovada": bool(syc["passed"] and hal["passed"] and
                             integrity["decision"] != "NEEDS_EVIDENCE"),
        }

    def report(self) -> dict:
        return self.audit.report()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pais", description="PAIS - sistema de aprendizado adaptativo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_obs = sub.add_parser("observe", help="observa uma interacao do usuario")
    p_obs.add_argument("mensagem")

    p_fb = sub.add_parser("feedback", help="classifica feedback")
    p_fb.add_argument("mensagem")

    p_rev = sub.add_parser("review", help="audita resposta contra bajulacao/alucinacao")
    p_rev.add_argument("resposta")
    p_rev.add_argument("--usuario", default="")

    sub.add_parser("profile", help="mostra o modelo do usuario")
    sub.add_parser("predict", help="preve proximo passo")
    sub.add_parser("report", help="relatorio de metricas")

    args = parser.parse_args(argv)
    pais = PAIS()
    if args.cmd == "observe":
        import json
        print(json.dumps(pais.observe(args.mensagem), ensure_ascii=False, indent=2))
    elif args.cmd == "feedback":
        import json
        print(json.dumps(pais.feedback(args.mensagem), ensure_ascii=False, indent=2))
    elif args.cmd == "review":
        import json
        print(json.dumps(pais.review(args.resposta, args.usuario), ensure_ascii=False, indent=2))
    elif args.cmd == "profile":
        import json
        u = pais.store.user()
        print(json.dumps({
            "linguistico": u.get("linguistic_profile"),
            "raciocinio": u.get("reasoning_profile"),
            "preferencias": u.get("preferences"),
            "padroes": u.get("patterns"),
            "fatos": u.get("facts"),
            "topicos_frequentes": u.get("frequent_topics"),
            "adaptacao": pais.adaptation.profile(),
        }, ensure_ascii=False, indent=2))
    elif args.cmd == "predict":
        import json
        last = (pais.store.user().get("interactions") or [{}])[-1].get("intent", "")
        print(json.dumps(pais.predictor.predict_next(last), ensure_ascii=False, indent=2))
    elif args.cmd == "report":
        import json
        print(json.dumps(pais.report(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
