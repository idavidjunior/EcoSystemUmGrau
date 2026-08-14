"""02/03/04. Perfis: Linguístico, Raciocínio e Preferências.

O objetivo é compreender o usuário, não transformar sua escrita. Toda
característica inferida é probabilisticamente rastreada (ver models.Trait).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import Confidence, MemoryStatus, Trait, _now

PROJECT_WORDS = ["jarvis", "ecosystem", "ecossistema", "voxumgrau", "widget",
                 "runtime", "ler", "sdd", "spec", "android", "mp3player",
                 "supermercado", "flutter", "clima"]
TECH_WORDS = ["android", "flutter", "python", "api", "mcp", "adb", "gradle",
              "sqlite", "websocket", "server", "config", "runtime", "kernel",
              "script", "função", "funcao", "classe", "método", "metodo",
              "test", "debug", "deploy", "build", "commit", "branch"]
ACTION_WORDS = ["faça", "faz", "crie", "cria", "implemente", "corrija", "corrige",
                "configure", "instale", "rode", "execute", "teste", "audite",
                "analise", "traduza", "resuma", "explique"]
EXPLANATION_WORDS = ["explique", "explica", "o que é", "o que significa",
                     "como funciona", "por que", "porque", "detalhe", "detalha",
                     "aprofund", "entendeu", "contexto"]
EXAMPLE_WORDS = ["exemplo", "exemplo?", "me dê um", "me da um", "exemplifique"]
SHORT_WORDS = ["resumo", "resuma", "curto", "rápido", "rapido", "direto", "objetivo"]
DEEP_WORDS = ["aprofund", "detalh", "completo", "completa", "arquitetura",
              "design", "tudo sobre", "pode explicar mais"]
DECISION_WORDS = ["quero", "decidi", "escolho", "prefiro", "optei", "vou de"]
CORRECTION_PATTERNS = [
    (r"\b(não|nao|n) .{0,20}(é|e) (isso|assim|desse jeito|dessa forma)\b", "corrige-conceito"),
    (r"\b(na verdade|na real|na verdade,)\b", "corrige-constata"),
    (r"\b(você|voce) (errou|inventou|alucinou|se esqueceu|não entendeu|nao entendeu)\b", "corrige-ia"),
    (r"\b(esquece|esqueça|larga|ignora|não era|nao era)\b", "corrige-direcao"),
]
ACCEPT_PATTERNS = [r"\b(perfeito|ótimo|otimo|excelente|muito bom|boa|show|top)\b",
                   r"\b(pode|pode sim|exato|isso mesmo|correto|certo)\b"]
QUESTION_PATTERNS = [
    (r"\b(o que|qual|como|onde|quando|quem|por que|porque)\b", "factual"),
    (r"\b(certo\?|é isso\?|e isso\?|ta certo\?|está correto\?)\b", "confirmacao"),
    (r"\b(é possível|dá para|da para|poderia|consegue)\b", "viabilidade"),
    (r"\b(vale a pena|compensa|devo|deveria)\b", "decisao"),
]


class LinguisticProfiler:
    """Observa como o usuário escreve, sem corrigir seu estilo."""

    def update(self, profile: dict, text: str) -> None:
        words = re.findall(r"\b[\wÀ-ÿ'-]+\b", text.lower())
        if not words:
            return
        avg_len = _avg(profile.get("avg_message_length", 0), len(text),
                       profile.get("sample_count", 0))
        avg_words = _avg(profile.get("avg_word_count", 0), len(words),
                         profile.get("sample_count", 0))
        abbr_count = len(set(words) & {
            "vc", "pq", "tb", "q", "blz", "ok", "flw", "tmj", "vlw", "kd",
            "nd", "dps", "tbm", "mto", "mt", "gnt", "obg", "hj", "pro", "porr"})
        tech_count = sum(1 for w in words if w in TECH_WORDS)
        formality = round(min(1.0, max(0.0, 0.5 + (len(text) / 200) * 0.1)), 2)
        informal_markers = sum(1 for w in words if w in
                               {"kkk", "lol", "cara", "mano", "pow", "tipo"})
        if informal_markers:
            formality = round(max(0.0, formality - 0.15 * informal_markers), 2)

        profile["avg_message_length"] = round(avg_len, 1)
        profile["avg_word_count"] = round(avg_words, 1)
        profile["sample_count"] = profile.get("sample_count", 0) + 1
        profile["abbreviation_count"] = profile.get("abbreviation_count", 0) + abbr_count
        profile["technical_word_count"] = profile.get("technical_word_count", 0) + tech_count
        profile["formality"] = round(_avg(profile.get("formality", 0.5), formality,
                                          profile.get("sample_count", 0)), 2)
        profile["uses_abbreviations"] = profile.get("abbreviation_count", 0) >= 2
        profile["technical_level"] = _technical_level(
            profile.get("technical_word_count", 0), profile.get("sample_count", 0))
        profile["last_sample"] = text[:200]


class ReasoningProfiler:
    """Identifica padrões de raciocínio — como interação, não como verdade."""

    def update(self, profile: dict, text: str) -> None:
        lowered = text.lower()
        profile.setdefault("decomposes", 0)
        profile.setdefault("seeks_confirmation", 0)
        profile.setdefault("asks_factual", 0)
        profile.setdefault("asks_viability", 0)
        profile.setdefault("asks_decision", 0)
        profile.setdefault("gives_correction", 0)
        profile.setdefault("gives_acceptance", 0)
        profile.setdefault("explores_hypotheses", 0)
        profile.setdefault("seeks_examples", 0)
        profile.setdefault("sample_count", 0)

        if _has_any(lowered, ["primeiro", "em seguida", "depois", "passo 1", "etapa",
                              "dividir", "divida", "separar", "quebrar em"]):
            profile["decomposes"] += 1
        if _has_any(lowered, ["certo?", "é isso?", "ta certo?", "está correto?",
                              "confirm", "confirma", "entendi", "entendeu"]):
            profile["seeks_confirmation"] += 1
        for pat, kind in QUESTION_PATTERNS:
            if re.search(pat, lowered):
                key = {"factual": "asks_factual", "confirmacao": "seeks_confirmation",
                       "viabilidade": "asks_viability", "decisao": "asks_decision"}[kind]
                profile[key] += 1
        if re.search(r"(na verdade|na real|você errou|voce errou|esquece|não é|nao e)",
                     lowered):
            profile["gives_correction"] += 1
        if _has_any(lowered, ACCEPT_PATTERNS):
            profile["gives_acceptance"] += 1
        if _has_any(lowered, ["e se", "será que", "talvez", "poderia ser", "hipótese",
                              "hipotese", "o que acha de"]):
            profile["explores_hypotheses"] += 1
        if _has_any(lowered, EXAMPLE_WORDS):
            profile["seeks_examples"] += 1
        profile["sample_count"] += 1

        n = profile["sample_count"]
        profile["style"] = {
            "decomposes_problems": profile["decomposes"] / max(1, n),
            "seeks_confirmation": profile["seeks_confirmation"] / max(1, n),
            "asks_factual": profile["asks_factual"] / max(1, n),
            "asks_viability": profile["asks_viability"] / max(1, n),
            "asks_decision": profile["asks_decision"] / max(1, n),
            "corrects_frequently": profile["gives_correction"] / max(1, n),
            "accepts_quickly": profile["gives_acceptance"] / max(1, n),
            "explores_hypotheses": profile["explores_hypotheses"] / max(1, n),
            "seeks_examples": profile["seeks_examples"] / max(1, n),
        }


class PreferenceModel:
    """Preferências separadas, probabilísticas e revisáveis (Trait)."""

    DEFAULTS = {
        "respostas_diretas": 0.5,
        "explicacoes_tecnicas": 0.5,
        "preferencia_arquitetura": 0.5,
        "preferencia_exemplos": 0.5,
        "preferencia_antecipar_problemas": 0.5,
        "preferencia_solucoes_praticas": 0.5,
        "preferencia_aprofundamento": 0.5,
        "preferencia_formatos_estruturados": 0.5,
        "tolerancia_explicacoes": 0.5,
        "profundidade_desejada": 0.5,
    }

    @staticmethod
    def update(preferences: dict, profile: dict, text: str) -> None:
        lowered = text.lower()
        p = preferences
        for key in PreferenceModel.DEFAULTS:
            p.setdefault(key, PreferenceModel.DEFAULTS[key])

        if _has_any(lowered, SHORT_WORDS) or (profile.get("avg_word_count") or 99) < 12:
            p["respostas_diretas"] = round(_bump(p["respostas_diretas"], +0.06), 2)
        if _has_any(lowered, DEEP_WORDS):
            p["preferencia_aprofundamento"] = round(_bump(p["preferencia_aprofundamento"], +0.06), 2)
        if _has_any(lowered, ["exemplo", "me dê", "me da"]):
            p["preferencia_exemplos"] = round(_bump(p["preferencia_exemplos"], +0.06), 2)
        if _has_any(lowered, ["arquitetura", "design", "padrão", "padrao", "estrutura"]):
            p["preferencia_arquitetura"] = round(_bump(p["preferencia_arquitetura"], +0.06), 2)
        if _has_any(lowered, ["antes de", "cuidado", "atenção", "atencao", "risco",
                              "pode quebrar", "impacto"]):
            p["preferencia_antecipar_problemas"] = round(_bump(p["preferencia_antecipar_problemas"], +0.06), 2)
        if _has_any(lowered, ["direto", "objetivo", "simples", "curto", "resume",
                              "resumo", "sem enrolação", "sem enrolacao"]):
            p["preferencia_solucoes_praticas"] = round(_bump(p["preferencia_solucoes_praticas"], +0.06), 2)
        if _has_any(lowered, ["lista", "tópicos", "topicos", "passo a passo", "checklist"]):
            p["preferencia_formatos_estruturados"] = round(_bump(p["preferencia_formatos_estruturados"], +0.06), 2)
        if p.get("seeks_examples") and p["seeks_examples"] > 0.5:
            p["preferencia_exemplos"] = round(max(p["preferencia_exemplos"], 0.7), 2)
        if _has_any(lowered, ["explica", "explique", "detalha", "detalhe"]):
            p["explicacoes_tecnicas"] = round(_bump(p["explicacoes_tecnicas"], +0.05), 2)

    @staticmethod
    def to_traits(preferences: dict) -> list:
        traits = []
        for key, value in preferences.items():
            if not isinstance(value, (int, float)):
                continue
            conf = Confidence.HIGH_CONFIDENCE if value >= 0.75 else (
                Confidence.MEDIUM_CONFIDENCE if value >= 0.6 else Confidence.LOW_CONFIDENCE)
            traits.append(Trait(key=f"pref.{key}", value=round(value, 2),
                                confidence=conf, status=MemoryStatus.UNCONFIRMED))
        return traits


def _avg(current, new_value, sample_count):
    if sample_count <= 0:
        return new_value
    return (current * sample_count + new_value) / (sample_count + 1)


def _bump(value, delta):
    return max(0.0, min(1.0, value + delta))


def _has_any(lowered, terms):
    return any(t in lowered for t in terms)


def _technical_level(tech_words, samples):
    if samples <= 0:
        return "unknown"
    ratio = tech_words / samples
    if ratio >= 2.0:
        return "alto"
    if ratio >= 0.8:
        return "medio"
    if ratio > 0:
        return "basico"
    return "unknown"
