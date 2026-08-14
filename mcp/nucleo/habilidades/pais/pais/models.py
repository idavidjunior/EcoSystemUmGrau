"""Modelos de dados do PAIS — níveis de confiança, status e entidades.

Nenhuma característica inferida sobre o usuário é tratada como fato.
Toda entidade carrega origem, timestamp, frequência, confiança e evidências.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Confidence(enum.Enum):
    EXPLICIT = "EXPLICIT"                 # declarado diretamente pelo usuário
    CONFIRMED = "CONFIRMED"               # declarado/confirmado repetidamente
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"   # padrão observado repetidamente
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"  # tendência observada
    LOW_CONFIDENCE = "LOW_CONFIDENCE"     # hipótese inicial
    UNKNOWN = "UNKNOWN"                   # informação insuficiente
    CONFLICTING = "CONFLICTING"           # evidências contraditórias


# Peso para consolidação/decay.
CONFIDENCE_RANK = {
    Confidence.EXPLICIT: 1.0,
    Confidence.CONFIRMED: 0.9,
    Confidence.HIGH_CONFIDENCE: 0.8,
    Confidence.MEDIUM_CONFIDENCE: 0.6,
    Confidence.LOW_CONFIDENCE: 0.35,
    Confidence.UNKNOWN: 0.1,
    Confidence.CONFLICTING: 0.5,
}


class MemoryStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    CONFLICTING = "CONFLICTING"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class EvidenceStatus(enum.Enum):
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    INFERRED = "INFERRED"
    UNCERTAIN = "UNCERTAIN"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


class FeedbackKind(enum.Enum):
    ACCEPTED = "ACCEPTED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"
    REFORMULATED = "REFORMULATED"
    EXPANDED = "EXPANDED"
    SHORTENED = "SHORTENED"
    QUESTIONED = "QUESTIONED"
    OVERRIDDEN = "OVERRIDDEN"
    NEUTRAL = "NEUTRAL"


@dataclass
class Trait:
    """Característica inferida/declarada sobre o usuário."""
    key: str
    value: object
    confidence: Confidence = Confidence.UNKNOWN
    status: MemoryStatus = MemoryStatus.UNCONFIRMED
    source: str = "inference"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    frequency: int = 1
    evidence_count: int = 0
    last_confirmed: str = ""
    expiration_policy: str = "adaptive"   # adaptive | fixed | never

    def to_dict(self) -> dict:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        d["status"] = self.status.value
        return d


@dataclass
class Memory:
    """Memória episódica (eventos) com governança completa."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: str = "episodic"              # user_fact | user_preference | user_pattern | project | goal | event | correction
    content: str = ""
    source: str = "interaction"
    confidence: Confidence = Confidence.UNKNOWN
    status: MemoryStatus = MemoryStatus.UNCONFIRMED
    evidence_count: int = 0
    last_confirmed: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    expires_at: str = ""
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        d["status"] = self.status.value
        return d


@dataclass
class Claim:
    """Afirmação com rastreio de fonte e verificação."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    text: str = ""
    source: str = "user"                # user | conversation | research | model
    source_quality: str = "UNKNOWN"     # oficial | primaria | cientifica | secundaria | informal | unknown
    support_level: EvidenceStatus = EvidenceStatus.UNKNOWN
    confidence: float = 0.0             # 0..1
    verified_at: str = ""
    contradiction_of: list = field(default_factory=list)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["support_level"] = self.support_level.value
        return d


@dataclass
class Prediction:
    """Previsão — nunca apresentada como certeza."""
    next_intent: str = ""
    probability: float = 0.0
    basis: list = field(default_factory=list)
    made_at: str = field(default_factory=_now)
    outcome: str = ""                    # hit | miss | pending
