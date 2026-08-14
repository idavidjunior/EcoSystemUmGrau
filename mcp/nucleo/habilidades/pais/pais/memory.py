"""08/09. Episodic Memory e Semantic User Model.

Memória episódica (eventos) separada do modelo semântico do usuário
(fatos, preferências, padrões). Nada é misturado com conhecimento factual.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import (Claim, Confidence, Memory, MemoryStatus, Prediction, Trait, _now)

DECAY_DAYS = 90          # memórias perdem peso após isso
EXPIRATION_DAYS = 365    # expiração dura


class EpisodicMemory:
    """Registra eventos com governança (decay/expiração)."""

    def __init__(self, store):
        self._store = store

    def add(self, kind: str, content: str, context: dict = None) -> Memory:
        mem = Memory(type=kind, content=content, source="interaction",
                     confidence=Confidence.LOW_CONFIDENCE,
                     status=MemoryStatus.UNCONFIRMED,
                     context=context or {})
        return mem

    def _apply_decay(self) -> None:
        """Marca STALE/EXPIRED memórias antigas (nunca apaga silenciosamente)."""
        now = datetime.now(timezone.utc)
        memories = self._store.user().get("episodic", {})
        changed = False
        for key, m in memories.items():
            if m.get("status") in ("REJECTED", "EXPIRED"):
                continue
            try:
                created = datetime.fromisoformat(m["created_at"])
            except (KeyError, ValueError):
                continue
            age = now - created
            if m.get("expires_at"):
                try:
                    if now > datetime.fromisoformat(m["expires_at"]):
                        m["status"] = "EXPIRED"
                        changed = True
                        continue
                except ValueError:
                    pass
            if age > timedelta(days=EXPIRATION_DAYS):
                m["status"] = "EXPIRED"
                changed = True
            elif age > timedelta(days=DECAY_DAYS):
                m["status"] = "STALE"
                changed = True
        if changed:
            self._store.save_user()

    def expire_old(self) -> int:
        self._apply_decay()
        memories = self._store.user().get("episodic", {})
        return sum(1 for m in memories.values() if m.get("status") == "EXPIRED")


class SemanticUserModel:
    """Traits consolidados (fatos/preferências/padrões sobre o usuário)."""

    def __init__(self, store):
        self._store = store

    def get_trait(self, key: str) -> dict:
        for bucket in ("facts", "preferences", "patterns", "habits"):
            t = self._store.user().get(bucket, {}).get(key)
            if t:
                return t
        return self._store.user().get("inferences", {}).get(key, {})

    def set_trait(self, bucket: str, trait: Trait) -> None:
        store = self._store.user()
        store.setdefault(bucket, {})[trait.key] = trait.to_dict()

    def observe(self, key: str, value, bucket: str, source: str,
                confidence: Confidence = Confidence.LOW_CONFIDENCE) -> None:
        """Observa um sinal e consolida com contagem/frequência."""
        store = self._store.user()
        store.setdefault(bucket, {})
        existing = store[bucket].get(key)
        now = _now()
        if existing:
            existing["frequency"] = existing.get("frequency", 1) + 1
            existing["evidence_count"] = existing.get("evidence_count", 0) + 1
            existing["value"] = value
            existing["updated_at"] = now
            existing["confidence"] = _promote(existing.get("confidence"), confidence).value
            existing["status"] = _status_for(existing.get("confidence"))
            existing["last_confirmed"] = now if confidence in (
                Confidence.EXPLICIT, Confidence.CONFIRMED) else existing.get("last_confirmed", "")
            store[bucket][key] = existing
        else:
            trait = Trait(key=key, value=value, confidence=confidence,
                          status=MemoryStatus.UNCONFIRMED, source=source,
                          evidence_count=1)
            store[bucket][key] = trait.to_dict()

    def register_claim(self, claim: Claim) -> None:
        ep = self._store.epistemic()
        ep.setdefault("claims", {})[claim.id] = claim.to_dict()

    def register_prediction(self, prediction: Prediction) -> None:
        ep = self._store.epistemic()
        ep.setdefault("predictions", {})[prediction.made_at] = prediction.__dict__

    def record_outcome(self, predicted_intent: str, actual_intent: str) -> None:
        ep = self._store.epistemic()
        ep.setdefault("prediction_outcomes", []).append({
            "predicted": predicted_intent, "actual": actual_intent,
            "hit": predicted_intent == actual_intent, "at": _now(),
        })


def _promote(current_raw, new):
    if new == Confidence.EXPLICIT:
        return Confidence.EXPLICIT
    if new == Confidence.CONFIRMED:
        return Confidence.CONFIRMED
    current = Confidence(current_raw) if current_raw in Confidence._value2member_map_ else Confidence.UNKNOWN
    rank = {"LOW_CONFIDENCE": 1, "MEDIUM_CONFIDENCE": 2, "HIGH_CONFIDENCE": 3}
    if rank.get(new.value, 0) > rank.get(current.value, 0):
        return new
    return current


def _status_for(confidence_raw) -> str:
    if confidence_raw == "EXPLICIT":
        return "CONFIRMED"
    if confidence_raw in ("HIGH_CONFIDENCE", "CONFIRMED"):
        return "CONFIRMED"
    if confidence_raw == "MEDIUM_CONFIDENCE":
        return "UNCONFIRMED"
    return "UNCONFIRMED"
