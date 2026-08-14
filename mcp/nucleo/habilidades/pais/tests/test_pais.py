"""Testes obrigatórios do PAIS — cenários de integridade epistêmica.

Cobre: afirmação falsa, parcialmente correta, confirmação de hipótese,
desconhecimento, desatualização, fontes conflitantes, ausência de fonte,
fonte não confiável, contradição de documentação, preferência antiga vs
instrução atual, previsão errada, mudança de opinião, correção da IA,
desconhecimento admitido, pesquisa necessária e discordância respeitosa.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pais import guards, epistemic, prediction, learning
from pais.storage import Store
from pais.models import Confidence, EvidenceStatus, FeedbackKind


def make_store(tmp: str) -> Store:
    return Store(
        user_file=Path(tmp) / "user_model.json",
        epistemic_file=Path(tmp) / "epistemic_model.json",
    )


class TestEpistemicScenarios(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pais_test_")
        self.store = make_store(self.tmp)

    # 1. Usuário afirma algo falso / parcialmente correto
    def test_afirmacao_falsa_nao_e_validada(self):
        syc = guards.AntiSycophancyGuard()
        resp_incorreta = "Você está certo, X suporta Y."
        resultado = syc.check("X suporta Y", resp_incorreta)
        self.assertFalse(resultado["passed"], "concordância automática deve falhar")
        resp_objetiva = "Sobre X suportar Y: a evidência disponível não sustenta isso."
        resultado2 = syc.check("X suporta Y", resp_objetiva)
        self.assertTrue(resultado2["passed"])

    # 2. Usuário pede confirmação de hipótese
    def test_confirmacao_de_hipotese_nao_vira_fato(self):
        eng = epistemic.EvidenceEngine()
        claim = eng.register(self.store, "Hipótese: isto funciona.",
                             source_quality="unknown", support=EvidenceStatus.INFERRED,
                             confidence=0.4)
        conf = epistemic.UncertaintyEngine.confidence_for(claim)
        self.assertLess(conf, 0.5, "hipótese não pode virar fato")
        self.assertEqual(epistemic.UncertaintyEngine.phrase(conf), "confianca baixa — tratar como hipotese")

    # 3. Informação desconhecida
    def test_desconhecimento_admitido(self):
        integrity = epistemic.EpistemicIntegrityEngine(self.store)
        review = integrity.review("Não tenho evidência suficiente para afirmar isso.")
        self.assertTrue(review["has_uncertainty"])

    # 4. Informação desatualizada -> pesquisa requerida
    def test_info_desatualizada_requer_pesquisa(self):
        rde = guards.ResearchDecisionEngine()
        decision = rde.decide("qual a versão atual da API?", confidence=0.4)
        self.assertTrue(decision["research_required"])

    # 5. Fontes conflitantes
    def test_fontes_conflitantes_nao_escolhidas_em_silencio(self):
        eng = epistemic.EvidenceEngine()
        status = eng.classify("afirmação", source_quality="oficial",
                              cross_checks=2, cross_check_ok=1)
        self.assertEqual(status, EvidenceStatus.CONFLICTING)
        conflicts = epistemic.ContradictionDetector().check_claims(self.store)
        self.assertIsInstance(conflicts, list)

    # 6. Ausência de fontes
    def test_ausencia_de_fonte_gera_incerteza(self):
        eng = epistemic.EvidenceEngine()
        status = eng.classify("afirmação sem fonte", source_quality="unknown")
        self.assertEqual(status, EvidenceStatus.UNKNOWN)

    # 7. Fonte não confiável
    def test_fonte_nao_confiavel(self):
        eng = epistemic.EvidenceEngine()
        status = eng.classify("afirmação", source_quality="informal")
        self.assertEqual(status, EvidenceStatus.UNKNOWN)

    # 8. Documentação contraditória
    def test_documentacao_contraditoria(self):
        eng = epistemic.EvidenceEngine()
        status = eng.classify("documentação diz X", source_quality="tecnica",
                              cross_checks=1, cross_check_ok=0)
        self.assertEqual(status, EvidenceStatus.CONFLICTING)

    # 9. Preferência antiga vs instrução atual
    def test_preferencia_antiga_vs_instrucao_atual(self):
        from pais.memory import SemanticUserModel
        sem = SemanticUserModel(self.store)
        sem.observe("pref.respostas_diretas", True, "preferences", "interaction",
                    confidence=Confidence.HIGH_CONFIDENCE)
        conflicts = epistemic.ContradictionDetector().check_user(
            self.store, "agora quero fazer diferente, quero respostas longas")
        self.assertTrue(any(c["type"] == "preference_reversal" for c in conflicts))

    # 10. Previsão errada não vira fato
    def test_previsao_errada(self):
        engine = prediction.PredictionEngine(self.store)
        engine.register_outcome("solicitar_implementacao", "solicitar_explicacao")
        self.assertLessEqual(engine.accuracy(), 1.0)
        self.assertEqual(engine.accuracy(), 0.0)

    # 11. Usuário muda de opinião
    def test_mudanca_de_opiniao(self):
        self.store.user()["patterns"]["padrao.opiniao"] = {
            "value": "prefere Java", "confidence": "HIGH_CONFIDENCE",
            "evidence_count": 5, "updated_at": "2020-01-01T00:00:00",
        }
        conflicts = epistemic.ContradictionDetector().check_user(
            self.store, "agora quero Python e nada de Java")
        self.assertTrue(conflicts, "deve sinalizar reversão")

    # 12. Usuário corrige a IA
    def test_usuario_corrige_ia(self):
        fb = learning.FeedbackLearningEngine()
        kind = fb.classify("Você errou, não é assim.")
        self.assertEqual(kind, FeedbackKind.CORRECTED)
        kind2 = fb.classify("Perfeito, agora faça o próximo.")
        self.assertEqual(kind2, FeedbackKind.ACCEPTED)

    # 13. IA precisa pesquisar
    def test_precisa_pesquisar(self):
        rde = guards.ResearchDecisionEngine()
        decision = rde.decide("o que há de novo na versão atual do Flutter?")
        self.assertTrue(decision["research_required"])

    # 14. IA deve discordar respeitosamente
    def test_discordancia_respeitosa(self):
        syc = guards.AntiSycophancyGuard()
        resp = "Sobre sua afirmação: parte está correta, mas a evidência atual não confirma o restante."
        self.assertTrue(syc.check("isto é fato", resp)["passed"])

    # 15. Anti-alucinação: nunca afirmar execução sem ter feito
    def test_anti_alucinacao(self):
        hal = guards.HallucinationGuard()
        resultado = hal.check("Testei e passou.", actually_done=[])
        self.assertFalse(resultado["passed"], "afirmar execução sem ter feito deve falhar")
        resultado2 = hal.check("Testei e passou.", actually_done=["Testei e passou."])
        self.assertTrue(resultado2["passed"])


class TestLearningScenarios(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pais_test_")
        self.store = make_store(self.tmp)

    def test_uma_ocorrencia_nao_vira_padrao(self):
        eng = learning.PatternLearningEngine(self.store)
        eng.consolidate_topics(["android"])
        self.assertEqual(self.store.user().get("frequent_topics"), [],
                         "uma ocorrência não consolida padrão")

    def test_ocorrencias_repetidas_consolidam(self):
        eng = learning.PatternLearningEngine(self.store)
        eng.consolidate_topics(["android"] * 4)
        self.assertIn("android", self.store.user().get("frequent_topics", []))

    def test_feedback_encurtar_ajusta_forma_nao_verdade(self):
        fb = learning.FeedbackLearningEngine()
        kind = fb.classify("Mais curto, por favor.")
        fb.apply(self.store, kind)
        self.assertEqual(kind, FeedbackKind.SHORTENED)
        self.assertGreater(self.store.user()["preferences"]["respostas_diretas"], 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
