"""12/13/14/15. Epistemic Integrity, Evidence & Verification, Contradiction
Detector e Uncertainty & Confidence Engine.

Responde à pergunta: "o que podemos afirmar com fundamento?" — independente
do User Model. Nunca sobrescreve evidência com preferência do usuário.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import Claim, Confidence, EvidenceStatus

VERBATIM_CLAIM = re.compile(
    r"(afirmo|afirmo que|isso é verdade|isso e verdade|tenho certeza|com certeza|"
    r"garanto|é fato|e fato|comprovado|certamente|obviamente)", re.I)
TEMPORAL_CLAIM = re.compile(
    r"\b(hoje|agora|atualmente|nesta semana|este ano|este mês|este mes|"
    r"agora em 20\d\d|última versão|ultima versao|versão atual|versao atual)\b", re.I)
EXECUTION_CLAIM = re.compile(
    r"(rodei|executei|testei|compilou|rodou|passou|falhou|funcionou|instalei|"
    r"rodei o teste|deploy feito|commitado|commit feito)", re.I)
SOURCE_CLAIM = re.compile(
    r"(a documentação|a doc|o github|a fonte|a spec|o manual|segundo o|"
    r"de acordo com|conforme)", re.I)
NOUN_VERB = re.compile(r"[\wÀ-ÿáéíóúâêôãõç-]{3,} (é|e|foi|será|sera|está|esta|funciona|suporta) ", re.I)


class EvidenceEngine:
    """Classifica afirmações factuais relevantes."""

    SOURCE_QUALITY = {
        "oficial": 1.0, "primaria": 0.95, "cientifica": 0.9, "norma": 0.88,
        "tecnica": 0.8, "instituicao": 0.85, "jornalismo": 0.6,
        "secundaria": 0.5, "comunidade": 0.35, "informal": 0.2,
    }

    def classify(self, claim_text: str, source_quality: str = "unknown",
                 cross_checks: int = 0, cross_check_ok: int = 0) -> EvidenceStatus:
        quality = self.SOURCE_QUALITY.get(source_quality.lower(), 0.0)
        if cross_checks > 0 and cross_check_ok < cross_checks:
            return EvidenceStatus.CONFLICTING
        if quality >= 0.9 and cross_checks > 0 and cross_check_ok == cross_checks:
            return EvidenceStatus.VERIFIED
        if quality >= 0.75:
            return EvidenceStatus.SUPPORTED
        if quality >= 0.4:
            return EvidenceStatus.INFERRED
        return EvidenceStatus.UNKNOWN

    def register(self, store, claim_text: str, source: str = "user",
                 source_quality: str = "unknown", support: EvidenceStatus = None,
                 confidence: float = 0.0) -> Claim:
        if support is None:
            support = self.classify(claim_text, source_quality)
        if confidence <= 0:
            confidence = self.SOURCE_QUALITY.get(source_quality.lower(), 0.0)
        claim = Claim(text=claim_text[:500], source=source,
                      source_quality=source_quality, support_level=support,
                      confidence=round(confidence, 2))
        store.epistemic().setdefault("claims", {})[claim.id] = claim.to_dict()
        store.save_epistemic()
        return claim


class ContradictionDetector:
    """Detecta conflitos: memória x conversa, fontes, preferências."""

    def check_user(self, store, statement: str) -> list:
        """Conflito entre instrução atual do usuário e inferências antigas."""
        lowered = statement.lower()
        conflicts = []
        user = store.user()
        for bucket in ("patterns", "inferences", "preferences"):
            for key, val in user.get(bucket, {}).items():
                v = str(val.get("value", "")) if isinstance(val, dict) else str(val)
                if not v or len(v) < 3:
                    continue
                if _opposes(lowered, v):
                    conflicts.append({
                        "type": "preference_reversal",
                        "current": statement[:200],
                        "old": key,
                        "old_value": v,
                    })
        return conflicts

    def check_claims(self, store) -> list:
        """Conflito entre afirmações registradas."""
        claims = store.epistemic().get("claims", {})
        conflicts = []
        items = list(claims.items())
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                k1, c1 = items[i]
                k2, c2 = items[j]
                if c1.get("support_level") == "CONFLICTING" or c2.get("support_level") == "CONFLICTING":
                    conflicts.append({"claim_a": k1, "claim_b": k2, "reason": "evidencias conflitantes"})
        return conflicts


class UncertaintyEngine:
    """Explicita incerteza e distingue conhecimento de hipótese."""

    @staticmethod
    def confidence_for(claim: Claim) -> float:
        base = claim.confidence
        if claim.support_level == EvidenceStatus.VERIFIED:
            return round(min(0.99, base * 1.1), 2)
        if claim.support_level == EvidenceStatus.SUPPORTED:
            return round(base, 2)
        if claim.support_level == EvidenceStatus.INFERRED:
            return round(base * 0.5, 2)
        if claim.support_level == EvidenceStatus.CONFLICTING:
            return 0.3
        return 0.1

    @staticmethod
    def phrase(confidence: float) -> str:
        if confidence >= 0.9:
            return "alta confianca"
        if confidence >= 0.7:
            return "boa confianca"
        if confidence >= 0.5:
            return "confianca moderada"
        if confidence >= 0.2:
            return "confianca baixa — tratar como hipotese"
        return "sem evidencia suficiente"


class EpistemicIntegrityEngine:
    """Revisa uma resposta antes da entrega (independente do User Model)."""

    def __init__(self, store):
        self.store = store

    def review(self, response: str, claims_present: bool = True) -> dict:
        issues = []
        lowered = response.lower()
        if "não sei" in lowered or "nao sei" in lowered:
            issues.append("desconhecimento admitido (valido)")
        if ("evidência" in lowered or "evidencia" in lowered) and \
                any(w in lowered for w in ("sem", "suficiente", "não tenho", "nao tenho", "insuficiente")):
            issues.append("falta de evidencia admitida (valido)")
        if re.search(r"(funciona|suporta|é compatível|e compativel|é melhor|e melhor)",
                     lowered) and claims_present:
            issues.append("possivel afirmacao factual sem evidencia citada")
        return {
            "reviewed": True,
            "has_uncertainty": any("desconhecimento" in i or "sem evidencia" in i or "evidencia admitida" in i
                                   for i in issues),
            "issues": issues,
            "decision": "PASS" if not any("afirmacao factual" in i for i in issues) else "NEEDS_EVIDENCE",
        }


def _opposes(lowered: str, old: str) -> bool:
    old_l = old.lower()
    if "prefere " in old_l or "prefere_" in old_l:
        return "mudei" in lowered or "mude de" in lowered or "agora quero" in lowered or \
               "diferente" in lowered or "não quero mais" in lowered or "nao quero mais" in lowered
    return False
