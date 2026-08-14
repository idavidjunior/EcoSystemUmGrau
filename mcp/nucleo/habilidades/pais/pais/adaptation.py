"""20. Adaptation Controller — personaliza a FORMA, nunca a verdade.

Aplicável: vocabulário, profundidade, estrutura, ritmo, exemplos, nível
técnico, formato. Jamais: fatos, evidências, resultados, segurança, critérios
de validação.
"""
from __future__ import annotations

from .interaction import ResponsePreferenceModel


class AdaptationController:
    def __init__(self, store):
        self.store = store

    def profile(self) -> dict:
        rp = ResponsePreferenceModel.recommend(self.store)
        prefs = self.store.user().get("preferences", {})
        tech = self.store.user().get("linguistic_profile", {}).get("technical_level", "unknown")
        return {
            "profundidade": rp.get("profundidade", "medio"),
            "estrutura": rp.get("estrutura", "prosa"),
            "com_exemplos": rp.get("com_exemplos", False),
            "tom": rp.get("tom", "direto"),
            "densidade_tecnica": rp.get("densidade_tecnica", "media"),
            "antecipar_problemas": rp.get("antecipar_problemas", False),
            "nivel_tecnico_observado": tech,
            "tolerancia_explicacoes": prefs.get("tolerancia_explicacoes", 0.5),
        }

    def guidance(self, response_has_facts: bool = True) -> dict:
        """Orientação para o agente formatar a resposta."""
        p = self.profile()
        guidance = []
        guidance.append(f"Profundidade: {p['profundidade']}.")
        guidance.append(f"Estrutura: {p['estrutura']}.")
        if p["com_exemplos"]:
            guidance.append("Inclua exemplo pratico quando pertinente.")
        if p["antecipar_problemas"]:
            guidance.append("Antecipe riscos/problemas conhecidos.")
        if p["tom"] == "direto":
            guidance.append("Tom direto, sem rodeios.")
        return {
            "profile": p,
            "guidance": guidance,
            "invariant": ("Fatos, evidencias, resultados de testes e criterios de validacao "
                          "NAO sao alterados pela personalizacao."),
        }
