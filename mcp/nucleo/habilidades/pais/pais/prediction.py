"""19. Prediction Engine — prevê intenções futuras com probabilidade.

PREVISÃO ≠ INTENÇÃO CONFIRMADA. Toda previsão carrega probabilidade, base
e nunca é apresentada como certeza.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

TRANSITIONS = defaultdict(Counter)


def _key(pair):
    return f"{pair[0]} -> {pair[1]}"


class PredictionEngine:
    def __init__(self, store):
        self._store = store

    def _build_transitions(self) -> defaultdict:
        interactions = self._store.user().get("interactions", [])
        trans = defaultdict(Counter)
        for i in range(len(interactions) - 1):
            a = interactions[i].get("intent", "")
            b = interactions[i + 1].get("intent", "")
            if a and b:
                trans[a][b] += 1
        return trans

    def predict_next(self, last_intent: str) -> dict:
        """Previsão do próximo passo provável com probabilidade."""
        trans = self._build_transitions()
        outcomes = trans.get(last_intent, {})
        if not outcomes:
            return {"next_intent": "", "probability": 0.0,
                    "basis": ["sem histórico suficiente"], "prediction": None}
        total = sum(outcomes.values())
        top, count = outcomes.most_common(1)[0]
        prob = count / total
        prediction = {
            "next_intent": top,
            "probability": round(prob, 2),
            "basis": [f"{last_intent}->{top}: {count}/{total}"],
            "made_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "outcome": "pending",
        }
        self._store.epistemic().setdefault("predictions", {})
        key = _key((last_intent, top))
        self._store.epistemic()["predictions"][key] = prediction
        self._store.save_epistemic()
        return {**prediction, "prediction": prediction}

    def register_outcome(self, last_intent: str, actual_intent: str) -> None:
        """Registra se a previsão acertou (hit/miss) para calibrar."""
        ep = self._store.epistemic()
        key = _key((last_intent, actual_intent))
        pred = ep.get("predictions", {}).get(key)
        if pred:
            pred["outcome"] = "hit"
        ep.setdefault("prediction_outcomes", []).append({
            "predicted": last_intent, "actual": actual_intent,
            "hit": last_intent == actual_intent,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        self._store.save_epistemic()

    def accuracy(self) -> float:
        ep = self._store.epistemic()
        outcomes = ep.get("prediction_outcomes", [])
        if not outcomes:
            return 0.0
        hits = sum(1 for o in outcomes if o.get("hit"))
        return round(hits / len(outcomes), 2)
