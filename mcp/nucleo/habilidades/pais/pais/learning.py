"""10/11. Pattern Learning Engine e Feedback Learning Engine.

Aprende padrões por repetição (nunca por ocorrência única) e classifica
feedback explícito/implicito.
"""
from __future__ import annotations

import re
from collections import Counter

from .models import Confidence, FeedbackKind, MemoryStatus, Trait

MIN_EVIDENCE = 3   # mínimo de evidências para consolidar padrão


class PatternLearningEngine:
    """Consolida padrões quando há frequência suficiente."""

    def __init__(self, store):
        self._store = store
        self.sem = SemanticUserModelShim(store)

    def consolidate_topics(self, topics: list, count: int = 30) -> None:
        """Frequência de assuntos. Padrão só vira trait com MIN_EVIDENCE."""
        topics_counter = Counter(topics)
        store = self._store.user()
        store.setdefault("topic_frequency", {})
        for topic, inc in topics_counter.items():
            cur = store["topic_frequency"].get(topic, 0)
            store["topic_frequency"][topic] = cur + inc
        if store["topic_frequency"]:
            counter = Counter(store["topic_frequency"])
            store["frequent_topics"] = [t for t, c in counter.most_common(count) if c >= MIN_EVIDENCE]
        self._store.save_user()

    def consolidate_patterns(self) -> None:
        """Transforma inferências com evidência suficiente em padrões."""
        store = self._store.user()
        infs = store.get("inferences", {})
        pats = store.setdefault("patterns", {})
        for key, inf in list(infs.items()):
            if inf.get("evidence_count", 0) >= MIN_EVIDENCE:
                pats.setdefault(key, inf)
        self._store.save_user()


class SemanticUserModelShim:
    """Ponte mínima para _promote dentro do pattern engine."""

    def __init__(self, store):
        self._store = store

    def set_trait(self, bucket, trait):
        self._store.user().setdefault(bucket, {})[trait.key] = trait.to_dict()


class FeedbackLearningEngine:
    """Classifica o sinal de feedback após uma resposta."""

    POSITIVE = ["perfeito", "ótimo", "otimo", "excelente", "muito bom", "exato",
                "isso mesmo", "correto", "certo", "show", "top", "boa", "legal",
                "funcionou", "resolveu", "agora sim", "obrigado", "valeu"]
    NEGATIVE = ["errou", "inventou", "alucinou", "não é", "nao e", "tá errado",
                "ta errado", "errado", "não entendi", "nao entendi", "não era",
                "nao era", "ruim", "horrível", "horrivel", "de novo não",
                "de novo nao", "não foi", "nao foi", "não serviu", "nao serviu"]
    SHORTEN_REQUEST = ["mais curto", "resume", "resumo", "menos texto", "direto",
                       "objetivo", "sem enrolação", "sem enrolacao", "encurta",
                       "encurte", "vai logo", "menos"]
    EXPAND_REQUEST = ["mais detalhe", "detalha", "aprofund", "explica melhor",
                      "mais contexto", "completo", "mais explicação", "mais explicacao",
                      "continua", "continue", "extende", "estende"]

    def classify(self, message: str) -> FeedbackKind:
        lowered = message.lower()
        if any(w in lowered for w in self.SHORTEN_REQUEST):
            return FeedbackKind.SHORTENED
        if any(w in lowered for w in self.EXPAND_REQUEST):
            return FeedbackKind.EXPANDED
        if any(w in lowered for w in self.NEGATIVE):
            if re.search(r"(reformul|diferente|em vez|em vez de|tenta de novo|faz de novo|outra)", lowered):
                return FeedbackKind.REFORMULATED
            if any(w in lowered for w in ["deixa", "esquece", "esqueça", "ignora", "larga",
                                          "não faz", "nao faz", "muda de", "mude de", "abandona"]):
                return FeedbackKind.OVERRIDDEN
            return FeedbackKind.CORRECTED
        if any(w in lowered for w in self.POSITIVE):
            return FeedbackKind.ACCEPTED
        if "?" in message or re.search(r"\b(confirma|confirme|entendi|certo)", lowered):
            return FeedbackKind.QUESTIONED
        return FeedbackKind.NEUTRAL

    def apply(self, store, kind: FeedbackKind, prefs_key: str = "") -> None:
        """Atualiza preferências pelo feedback (implícito, com cuidado)."""
        user = store.user()
        prefs = user.setdefault("preferences", {})
        if kind == FeedbackKind.SHORTENED:
            prefs["respostas_diretas"] = round(min(1.0, prefs.get("respostas_diretas", 0.5) + 0.08), 2)
            prefs["preferencia_aprofundamento"] = round(max(0.0, prefs.get("preferencia_aprofundamento", 0.5) - 0.06), 2)
        elif kind == FeedbackKind.EXPANDED:
            prefs["preferencia_aprofundamento"] = round(min(1.0, prefs.get("preferencia_aprofundamento", 0.5) + 0.08), 2)
        elif kind == FeedbackKind.ACCEPTED:
            if prefs_key:
                prefs[prefs_key] = round(min(1.0, prefs.get(prefs_key, 0.5) + 0.04), 2)
        elif kind in (FeedbackKind.CORRECTED, FeedbackKind.REJECTED, FeedbackKind.OVERRIDDEN):
            # sinal de que a forma/estrutura precisa revisão — não toca verdade
            user.setdefault("feedback_flags", []).append(kind.value)
        store.save_user()
        store.log_interaction({"kind": "feedback", "label": kind.value})


class FeedbackKindUtil:
    @staticmethod
    def note_occurrence(store, kind: FeedbackKind) -> None:
        """Conta ocorrências por tipo de feedback para auditoria."""
        ep = store.epistemic()
        counts = ep.setdefault("metrics", {}).setdefault("feedback_counts", {})
        counts[kind.value] = counts.get(kind.value, 0) + 1
