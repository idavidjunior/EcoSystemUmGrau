"""01. Interaction Observer — observa sinais estruturais de cada interação.

Extrai características determinísticas (stdlib, sem LLM) de uma mensagem do
usuário e registra o evento. Nenhum sinal individual é tratado como preferência.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

CITATION_RE = re.compile(r"(https?://\S+|`[^`]+`|\b\w+\s+et al\.?\b)", re.I)
QUESTION_RE = re.compile(r"[?？]")
CURRENCY_RE = re.compile(r"[R$€$£]\s?\d")
NUMERIC_RE = re.compile(r"\b\d[\d.,]*\b")
CODEBLOCK_RE = re.compile(r"```[\s\S]*?```")
ACTION_WORDS = ["faça", "faz", "crie", "cria", "implemente", "implementa",
                "corrija", "corrige", "configure", "instala", "instale",
                "rode", "roda", "execute", "executa", "teste", "testa",
                "explique", "explica", "me ajude", "ajuda", "resuma",
                "traduza", "traduz", "audite", "audita", "analise", "analisa"]
DECISION_WORDS = ["quero", "decidi", "escolho", "prefiro", "optei", "vou de",
                  "não quero", "nao quero", "evite", "pare"]
KNOWLEDGE_WORDS = ["o que é", "o que significa", "como funciona", "por que",
                   "porque", "qual a diferença", "certo?", "está certo",
                   "funciona?", "entendi", "correto"]
UNCERTAINTY_WORDS = ["acho que", "talvez", "não sei", "nao sei", "não tenho certeza",
                     "nao tenho certeza", "provavelmente", "não entendi", "nao entendi"]
ABBREVIATIONS = {
    "vc", "pq", "tb", "q", "blz", "ok", "flw", "tmj", "vlw", "kd", "porr",
    "nd", "dps", "tbm", "mto", "mt", "gnt", "obg", "hj", "amanhã", "pro",
}


class ObservedInteraction:
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.text = ""
        self.length = 0
        self.word_count = 0
        self.has_question = False
        self.has_currency = False
        self.has_code = False
        self.has_numbers = False
        self.has_citations = False
        self.is_imperative = False
        self.is_decision = False
        self.is_knowledge_query = False
        self.has_uncertainty = False
        self.abbreviation_count = 0
        self.formality = 0.5          # 0 informal .. 1 formal
        self.technicality = 0.0       # 0..1
        self.action_words = []
        self.topics = []


def observe(message: str) -> ObservedInteraction:
    """Extrai sinais estruturais da mensagem do usuário."""
    oi = ObservedInteraction()
    if not message:
        return oi
    text = message.strip()
    oi.text = text
    oi.length = len(text)
    words = re.findall(r"\b[\wÀ-ÿ'-]+\b", text.lower())
    oi.word_count = len(words)
    oi.has_question = bool(QUESTION_RE.search(text))
    oi.has_currency = bool(CURRENCY_RE.search(text))
    oi.has_code = bool(CODEBLOCK_RE.search(text)) or "```" in text
    oi.has_numbers = bool(NUMERIC_RE.search(text))
    oi.has_citations = bool(CITATION_RE.search(text))

    lowered = text.lower()
    oi.action_words = [w for w in ACTION_WORDS if w in lowered]
    oi.is_imperative = any(w in lowered for w in
                           ["faça", "faz", "crie", "cria", "implemente", "corrija",
                            "corrige", "configure", "instale", "rode", "execute",
                            "teste", "audite", "analise", "traduza", "resuma"])
    oi.is_decision = any(w in lowered for w in DECISION_WORDS)
    oi.is_knowledge_query = any(w in lowered for w in KNOWLEDGE_WORDS)
    oi.has_uncertainty = any(w in lowered for w in UNCERTAINTY_WORDS)

    toks = set(words)
    oi.abbreviation_count = len(toks & ABBREVIATIONS)

    formal_markers = sum(1 for w in ["por favor", "poderia", "gostaria", "obrigado",
                                     "desculpe", "senhor"] if w in lowered)
    informal_markers = oi.abbreviation_count + sum(1 for w in ["kkk", "lol", "cara",
                                                               "mano", "pow", "tipo"] if w in lowered)
    oi.formality = round(0.5 + 0.15 * formal_markers - 0.12 * informal_markers, 2)
    oi.formality = max(0.0, min(1.0, oi.formality))

    technical = sum(1 for w in ["android", "flutter", "python", "api", "mcp", "adb",
                                "gradle", "sqlite", "websocket", "server", "config",
                                "runtime", "kernel", "script", "função", "funcao",
                                "classe", "método", "metodo", "função"] if w in lowered)
    oi.technicality = round(min(1.0, technical / 3), 2)

    if not oi.has_code and oi.has_numbers and not oi.has_currency:
        pass  # contexto de métricas é capturado nos tópicos
    return oi


def extract_topics(message: str, known_projects: dict) -> list:
    """Tenta associar a mensagem a projetos/assuntos conhecidos."""
    lowered = message.lower()
    hits = []
    for key in known_projects:
        if key and key.lower() in lowered:
            hits.append(key)
    if not hits:
        for kw in ["jarvis", "ecosystem", "ecossistema", "voxumgrau", "widget",
                   "runtime", "ler", "sdd", "spec", "android", "adroid", "mp3player",
                   "supermercado", "clima", "clima api"]:
            if kw in lowered:
                hits.append(kw)
    return hits
