"""16/17/18. Anti-Sycophancy Guard, Hallucination Guard e Research Decision Engine.

Protegem a integridade da resposta: não bajular, não inventar, pesquisar
quando o limiar de confiança não for atingido.
"""
from __future__ import annotations

import re

from .models import EvidenceStatus

AGREEMENT_WORDS = ["você está certo", "voce esta certo", "você tem razão", "voce tem razao",
                   "exatamente como você disse", "exatamente como voce disse", "concordo"]
HEDGE_FOR_FACTUAL = r"(é melhor|e melhor|é o certo|e o certo|com certeza|certamente|é verdade|e verdade)"
VERIFICATION_NEEDED = r"(suporta|funciona|compatível|compativel|correto|errado|é assim|e assim)"


class AntiSycophancyGuard:
    """Nunca validar hipótese apenas porque veio do usuário."""

    def check(self, user_message: str, response: str) -> dict:
        lowered_resp = response.lower()
        issues = []
        auto_agree = any(w in lowered_resp for w in AGREEMENT_WORDS)
        if auto_agree:
            issues.append("concordancia automatica detectada — verificar se ha evidencia")
        factual_overclaim = bool(re.search(HEDGE_FOR_FACTUAL, lowered_resp))
        if factual_overclaim:
            issues.append("afirmacao factual apresentada sem fonte — verificar")
        return {
            "guard": "anti_sycophancy",
            "passed": not issues,
            "issues": issues,
            "recommendation": ("Reconhecer objetivamente o que esta correto; corrigir claramente "
                               "o que nao esta; declarar duvida quando houver.")
        }


class HallucinationGuard:
    """Nunca afirmar que algo foi executado/pesquisado se não foi."""

    VERIFY_RE = re.compile(
        r"(testei|testado|passou|passou nos testes|executado|executei|rodei|compilei|instalei|"
        r"funcionou|foi commitado|deploy feito|pesquisei|verifiquei na doc|"
        r"consultei a documentação|consultei a documentacao|segundo o site)", re.I)

    def check(self, response: str, actually_done: list = None) -> dict:
        actually_done = actually_done or []
        done_lower = [d.lower() for d in actually_done]
        claims = self.VERIFY_RE.findall(response.lower())
        fake = [c for c in claims if not any(c in d for d in done_lower)]
        return {
            "guard": "hallucination",
            "passed": not fake,
            "suspect_claims": fake,
            "recommendation": "Nao afirmar execucao/pesquisa sem tela-la de fato."
        }


class ResearchDecisionEngine:
    """Decide se é necessário pesquisar antes de responder."""

    STABLE_KNOWLEDGE = ["python", "java", "sql", "git", "rest", "json", "http",
                        "android sdk", "flutter widget", "função", "funcao", "classe",
                        "método", "metodo", "variável", "variavel"]
    TOPIC_KEYWORDS = re.compile(
        r"(suporta|funciona|compatível|compativel|a versão|a versao|o release|"
        r"atualizad|nova versão|nova versao|breaking change|api mudou|deprecat|"
        r"o que há de novo|o que ha de novo|2025|2026)", re.I)

    def decide(self, question: str, confidence: float = 0.0,
               source_status: EvidenceStatus = EvidenceStatus.UNKNOWN,
               topic_recency: bool = False) -> dict:
        lowered = question.lower()
        needs = False
        reasons = []
        if source_status in (EvidenceStatus.UNKNOWN, EvidenceStatus.CONFLICTING):
            needs = True
            reasons.append("evidencia insuficiente ou conflitante")
        if confidence < 0.5:
            needs = True
            reasons.append("confianca abaixo do limiar")
        if self.TOPIC_KEYWORDS.search(lowered):
            needs = True
            reasons.append("topico sujeito a mudanca temporal")
        if topic_recency:
            needs = True
            reasons.append("atualidade requerida")
        if any(k in lowered for k in self.STABLE_KNOWLEDGE) and not needs:
            needs = False
            reasons.append("conhecimento estavel")
        return {
            "research_required": needs,
            "reasons": reasons,
            "recommendation": ("Pesquisar antes de responder." if needs
                               else "Pode responder com o conhecimento disponivel, explicitando limites.")
        }
