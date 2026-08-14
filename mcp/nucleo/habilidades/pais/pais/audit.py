"""21. Audit & Governance Layer — métricas e relatório de integridade.

Métricas separadas: personalização, predição, precisão factual, cobertura de
evidência, calibração, alucinação, bajulação, correção, precisão de pesquisa.
Satisfação do usuário NUNCA é a única métrica.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .prediction import PredictionEngine


class AuditGovernance:
    def __init__(self, store):
        self.store = store
        self.pred_engine = PredictionEngine(store)

    def metrics(self) -> dict:
        ep = self.store.epistemic()
        user = self.store.user()
        prefs = user.get("preferences", {})

        # Predição / calibração
        prediction_accuracy = self.pred_engine.accuracy()
        outcomes = ep.get("prediction_outcomes", [])

        # Evidência
        claims = ep.get("claims", {})
        evidence_coverage = 0.0
        if claims:
            verified = sum(1 for c in claims.values()
                           if c.get("support_level") in ("VERIFIED", "SUPPORTED"))
            evidence_coverage = round(verified / len(claims), 2)

        # Feedback
        feedback_counts = ep.get("metrics", {}).get("feedback_counts", {})
        accepted = feedback_counts.get("ACCEPTED", 0)
        corrected = feedback_counts.get("CORRECTED", 0) + feedback_counts.get("REJECTED", 0) \
            + feedback_counts.get("OVERRIDDEN", 0)
        total_fb = sum(feedback_counts.values())
        correction_rate = round(corrected / max(1, total_fb), 2)

        # Personalização (cobertura de preferências aprendidas, não de verdade)
        learned = sum(1 for v in prefs.values()
                      if isinstance(v, (int, float)) and v not in (0.5, 0.0, 1.0))
        personalization_score = round(learned / max(1, len(prefs)), 2)

        # Memória
        episodic = user.get("episodic", {})
        stale = sum(1 for m in episodic.values() if m.get("status") == "STALE")
        memory_staleness = round(stale / max(1, len(episodic)), 2)

        return {
            "personalization_score": personalization_score,
            "prediction_accuracy": prediction_accuracy,
            "prediction_count": len(outcomes),
            "factual_accuracy_estimada": evidence_coverage,
            "evidence_coverage": evidence_coverage,
            "calibration_score": round(prediction_accuracy, 2),
            "hallucination_rate": self._hallucination_rate(),
            "sycophancy_rate": self._sycophancy_rate(),
            "correction_rate": correction_rate,
            "feedback_total": total_fb,
            "memory_staleness": memory_staleness,
            "memory_count": len(episodic),
            "claim_count": len(claims),
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    def _hallucination_rate(self) -> float:
        log = self._read_log()
        flagged = sum(1 for e in log if e.get("guard") == "hallucination" and not e.get("passed"))
        return round(flagged / max(1, len(log)), 2)

    def _sycophancy_rate(self) -> float:
        log = self._read_log()
        flagged = sum(1 for e in log if e.get("guard") == "anti_sycophancy" and not e.get("passed"))
        return round(flagged / max(1, len(log)), 2)

    def _read_log(self) -> list:
        import json
        from pathlib import Path
        log_file = Path(self.store.user_file).parent / "audit.log"
        entries = []
        if not log_file.exists():
            return entries
        try:
            for line in log_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entries.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            pass
        return entries

    def report(self) -> dict:
        m = self.metrics()
        health = "SAUDAVEL" if m["prediction_count"] >= 3 and m["evidence_coverage"] >= 0.5 else "EM_AMADURECIMENTO"
        return {
            "modulo": "pais",
            "health": health,
            "metrics": m,
            "note": ("Satisfacao do usuario nao e a unica metrica. Uma resposta pode ser "
                     "desagradavel e correta; agradavel e falsa. Otimiza-se qualidade global."),
        }

    def audit_log(self, entry: dict) -> None:
        import json
        from pathlib import Path
        log_file = Path(self.store.user_file).parent / "audit.log"
        entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass
