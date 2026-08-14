"""05/06/07. Interaction Model, Intent Predictor e Response Preference Model.

Modela o histórico de interações, infere a intenção mais provável da mensagem
atual e mantém o modelo de resposta preferida. Intenção inferida ≠ fato.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import Confidence, Prediction

INTENT_HEURISTICS = [
    ("solicitar_implementacao", r"\b(implemente|implementa|faça|faz|crie|cria|construa|constroi|adiciona|adicionar|codifique|codificar)\b"),
    ("solicitar_correcao", r"\b(corrige|corrija|conserta|consertar|arruma|arrumar|resolve|resolver|debug|depura)\b"),
    ("solicitar_explicacao", r"\b(explique|explica|o que é|o que e|como funciona|significa|entenda|por que|porque)\b"),
    ("solicitar_revisao", r"\b(audite|audita|revise|revisa|revisão|revisao|review|olhe|veja)\b"),
    ("solicitar_pesquisa", r"\b(pesquise|pesquisa|busque|busca|procura|procurar|pesquisar)\b"),
    ("solicitar_resumo", r"\b(resuma|resumo|sintetize|sintetiza|resumidamente|curto)\b"),
    ("solicitar_configuracao", r"\b(configure|configura|instale|instala|setup|configure)\b"),
    ("solicitar_aprendizado", r"\b(aprenda|aprender|registre|registra|memória|memoria|lembre|anote)\b"),
    ("solicitar_opiniao", r"\b(o que você acha|o que voce acha|vale a pena|acha que|opiniao|opinião)\b"),
    ("confirmacao", r"\b(certo\?|é isso\?|e isso\?|ta certo\?|está correto\?|funciona\?|ok\?)\b"),
    ("feedback_positivo", r"\b(perfeito|ótimo|otimo|excelente|muito bom|boa|show|top|exato|isso mesmo)\b"),
    ("feedback_correcao", r"\b(errou|inventou|alucinou|não é assim|nao e assim|tá errado|ta errado|reformul)\b"),
    ("decisao", r"\b(quero|decidi|escolho|prefiro|optei|vou de)\b"),
    ("saudacao", r"\b(oi|ola|olá|e aí|e ai|bom dia|boa tarde|boa noite|fala)\b"),
]


class InteractionModel:
    """Registra e consulta o histórico de interações."""

    def __init__(self, store):
        self._store = store

    def record(self, message: str, intent: str, observed: dict) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "text": message[:500],
            "intent": intent,
            "length": observed.get("length", 0),
            "word_count": observed.get("word_count", 0),
        }
        self._store.user().setdefault("interactions", []).append(entry)
        self._store.user()["interactions"] = self._store.user()["interactions"][-500:]
        self._store.user()["last_interaction"] = entry["ts"]
        self._store.log_interaction({"kind": "interaction", **entry})


class IntentPredictor:
    """Infere a intenção provável por heurística determinística."""

    @staticmethod
    def predict(message: str) -> dict:
        lowered = message.lower()
        scores = {}
        for intent, pattern in INTENT_HEURISTICS:
            if re.search(pattern, lowered):
                scores[intent] = scores.get(intent, 0) + 1
        if not scores:
            return {"intent": "generico", "confidence": 0.1, "candidates": []}
        total = sum(scores.values())
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best, best_score = ranked[0]
        conf = min(0.9, 0.5 + 0.15 * (best_score / max(1, total)))
        return {
            "intent": best,
            "confidence": round(conf, 2),
            "candidates": [{"intent": i, "score": round(s / total, 2)}
                           for i, s in ranked[:3]],
        }


class ResponsePreferenceModel:
    """Modelo de resposta mais eficaz para o usuário (forma, não verdade)."""

    @staticmethod
    def recommend(store) -> dict:
        prefs = store.user().get("preferences", {})
        rp = store.user().setdefault("response_preferences", {})
        deep = prefs.get("preferencia_aprofundamento", 0.5)
        examples = prefs.get("preferencia_exemplos", 0.5)
        structured = prefs.get("preferencia_formatos_estruturados", 0.5)
        direct = prefs.get("respostas_diretas", 0.5)
        technical = prefs.get("explicacoes_tecnicas", 0.5)

        depth = "profundo" if deep >= 0.65 else ("medio" if deep >= 0.45 else "curto")
        structure = "estruturado" if structured >= 0.6 else "prosa"
        rp.update({
            "profundidade": depth,
            "estrutura": structure,
            "com_exemplos": examples >= 0.55,
            "tom": "direto" if direct >= 0.55 else "didatico",
            "densidade_tecnica": "alta" if technical >= 0.55 else "media",
            "antecipar_problemas": prefs.get("preferencia_antecipar_problemas", 0.5) >= 0.55,
        })
        return dict(rp)
