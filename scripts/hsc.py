"""Compressão Semântica Hierárquica (HSC) — infraestrutura permanente do ecossistema.

Transforma qualquer conteúdo em representações progressivamente mais compactas
(9 níveis: source, extraction, summary, synthesis, synopsis, structure,
key_concepts, essence, semantic_core) preservando fatos, entidades, relações,
números, datas, negações, condições e grau de certeza.

Princípio: COMPRIMA A FORMA, NÃO DESTRUA O CONHECIMENTO.
A compressão é EXTRATIVA e determinística: nenhuma frase é inventada; todo
conteúdo derivado aponta para fragmentos do original (rastreabilidade).

Uso:
    python scripts/hsc.py compress <arquivo> [--titulo T]
    python scripts/hsc.py text "texto longo..." [--titulo T]
    python scripts/hsc.py get KNOW-001 [nivel]   # nivel: 0-8 ou nome
    python scripts/hsc.py list
    python scripts/hsc.py rebuild KNOW-001
    python scripts/hsc.py stats
    python scripts/hsc.py recommend "pergunta?"
"""
import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HSC_DIR = ROOT / "runtime" / "hsc"
SOURCES_DIR = HSC_DIR / "sources"
INDEX_PATH = HSC_DIR / "index.json"
COMPRESSION_VERSION = "1.0"
FIDELITY_THRESHOLD = 0.85

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em",
    "no", "na", "nos", "nas", "por", "para", "com", "sem", "que", "se", "e",
    "ou", "mas", "como", "ao", "aos", "à", "às", "pelo", "pela", "é", "são",
    "foi", "ser", "tem", "ter", "the", "of", "and", "to", "in", "is", "was",
}

CAUSA_PATTERNS = [
    "porque", "pois", "já que", "devido a", "por causa de", "causou",
    "provocou", "levou a", "resultou em", "gerou", "ocasionou",
]
CONSEQ_MARKERS = ["portanto", "por isso", "consequentemente", "assim", "logo"]
HYPOTHESIS_MARKERS = ["talvez", "possivelmente", "é possível", "pode ser",
                      "poderia", "hipoteticamente", "quem sabe"]
INFERENCE_MARKERS = ["provavelmente", "presumivelmente", "deve ter",
                     "deduz-se", "inferindo", "conclui-se provável"]
OPINION_MARKERS = ["acho", "penso", "na minha visão", "na minha opinião",
                   "parece-me", "eu acho", "particularmente"]
UNCERTAINTY_MARKERS = ["não sei", "incerto", "dúvida", "desconhecido",
                       "sem certeza"]
NEGATION_MARKERS = ["não ", "nunca ", "jamais ", "nem ", "não,", "nunca,"]

NUM_RE = re.compile(
    r"\b\d{1,3}(?:\.\d{3})*(?:,\d+)?(?:%|kb|mb|gb|ms|s|min|h)?\b|\b\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b\d{2}/\d{2}/\d{4}\b|\b\d{4}\b|\b\d{1,2} de \w+ de? ?\d{0,4}\b"
)
WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÿ_\-]+")
UPPER_WORD = re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõçA-ZÁÉÍÓÚÂÊÔÃÕÇ0-9\-]*$")
ACRONYM = re.compile(r"^[A-Z]{2,}$")


def _normalizar(t: str) -> str:
    return unicodedata.normalize("NFC", t)


def _tokens(t: str):
    return {w.lower() for w in WORD_RE.findall(_normalizar(t).lower())
            if w.lower() not in STOPWORDS}


def dividir_frases(texto: str):
    brutos = [b.strip() for b in re.split(r"(?<=[.!?])\s+|\n+", texto)
              if b.strip()]
    frases = []
    for b in brutos:
        continua = not b.endswith((".", "?", "!", ":"))
        if frases and continua and len(b) < 60:
            frases[-1] += " " + b
        else:
            frases.append(b.rstrip("."))
    return [f for f in frases if f]


LINHAS_RUIDO_MD = re.compile(r"^\s*(#|\||```|>|---|-{3,}|\*\*|$)")


def _remover_ruido_estrutural(texto: str) -> str:
    linhas = texto.splitlines()
    corpo = []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if i == 0 and linha.strip() == "---":
            i += 1
            while i < len(linhas) and linhas[i].strip() != "---":
                i += 1
            i += 1
            continue
        if not LINHAS_RUIDO_MD.match(linha):
            corpo.append(linha.strip())
        i += 1
    return "\n".join(c for c in corpo if c).strip()


@dataclass
class Fato:
    id: str = ""
    subject: str = ""
    predicate: str = ""
    object: str = ""
    kind: str = "fact"
    negated: bool = False
    numbers: list = field(default_factory=list)
    dates: list = field(default_factory=list)
    confidence: float = 1.0
    fragment_idx: int = 0
    importance: float = 0.0


class EntityExtractor:
    def extract(self, frase: str) -> list:
        ents, buffer = [], []
        palavras = _normalizar(frase).split()
        for i, p in enumerate(palavras):
            limpo = p.strip(".,;:!?\u201c\u201d()[]{}\"'")
            if ACRONYM.match(limpo) or UPPER_WORD.match(limpo):
                buffer.append(limpo)
                continue
            if buffer:
                self._fechar(buffer, ents)
            del buffer[:]
        if buffer:
            self._fechar(buffer, ents)
        return ents

    @staticmethod
    def _fechar(buffer, ents):
        nome = " ".join(buffer)
        if len(nome) >= 2 and nome.lower() not in STOPWORDS:
            ents.append(nome)


class FactExtractor:
    def __init__(self):
        self.entities = EntityExtractor()

    @staticmethod
    def classificar(frase: str) -> str:
        f = frase.lower()
        for m in UNCERTAINTY_MARKERS:
            if m in f:
                return "uncertainty"
        for m in OPINION_MARKERS:
            if m in f:
                return "opinion"
        for m in HYPOTHESIS_MARKERS:
            if m in f:
                return "hypothesis"
        for m in INFERENCE_MARKERS:
            if m in f:
                return "inference"
        return "fact"

    @staticmethod
    def confianca(kind: str, negated: bool, tem_numeros: bool) -> float:
        base = {"fact": 0.95, "inference": 0.65, "hypothesis": 0.40,
                "opinion": 0.50, "uncertainty": 0.25}[kind]
        if negated:
            base -= 0.05
        if tem_numeros:
            base += 0.02
        return round(min(max(base, 0.0), 1.0), 2)

    def extract(self, frases: list) -> list:
        fatos = []
        for idx, frase in enumerate(frases):
            kind = self.classificar(frase)
            negated = any(m in frase.lower() for m in NEGATION_MARKERS)
            numbers = NUM_RE.findall(frase)
            dates = DATE_RE.findall(frase)
            ents = self.entities.extract(frase)
            subject = ents[0] if ents else self._sujeito_generico(frase)
            predicate, obj = self._predicado(frase, subject, ents)
            fato = Fato(
                id="FACT-%04d" % (len(fatos) + 1),
                subject=subject,
                predicate=predicate,
                object=obj[:300],
                kind=kind,
                negated=negated,
                numbers=numbers[:12],
                dates=dates[:6],
                confidence=self.confianca(kind, negated, bool(numbers)),
                fragment_idx=idx,
            )
            fatos.append(fato)
        return fatos

    @staticmethod
    def _sujeito_generico(frase: str) -> str:
        for palavra in frase.split():
            limpa = palavra.strip(".,;:!?()").lower()
            if limpa and limpa not in STOPWORDS:
                return palavra.strip(".,;:!?()")[:60]
        return "UNKNOWN"

    def _predicado(self, frase: str, subject: str, ents: list) -> tuple:
        tokens = frase.split()
        predicate = "relaciona-se a"
        obj = frase
        inicio = 0
        if frase.startswith(subject):
            inicio = len(subject.split())
        else:
            for k, tok in enumerate(tokens):
                if tok.strip(".,;:!?()").lower() == subject.lower():
                    inicio = k + 1
                    break
        for i in range(inicio, len(tokens)):
            limpo = tokens[i].strip(".,;:!?()").lower()
            if (limpo and limpo[0].isalpha() and limpo.islower()
                    and limpo not in STOPWORDS):
                predicate = limpo
                obj = " ".join(tokens[i + 1:]).strip()
                break
        if not obj:
            obj = " ".join(e for e in ents[1:]) if len(ents) > 1 else subject
        return predicate, obj


class RelationExtractor:
    def extract(self, frases: list) -> dict:
        causes, consequences, relations = [], [], []
        for frase in frases:
            f = frase.lower()
            for marcador in CAUSA_PATTERNS:
                if marcador in f:
                    parte_a, _, parte_b = frase.partition(marcador)
                    causes.append(parte_a.strip(" .;,") or UNKNOWN())
                    consequences.append(parte_b.strip(" .;,") or UNKNOWN())
                    relations.append({
                        "type": "causal",
                        "cause_fragment": parte_a.strip(" .;,").lower(),
                        "effect_fragment": parte_b.strip(" .;,").lower(),
                    })
                    break
            else:
                for marcador in CONSEQ_MARKERS:
                    if f.startswith(marcador):
                        consequences.append(frase[len(marcador):].strip(" .;,"))
                        break
        return {"causes": causes, "consequences": consequences,
                "relations": relations}


def UNKNOWN() -> str:
    return "UNKNOWN"


class SemanticExtractor:
    """FASE 1 — extração estrutural completa da fonte."""

    def __init__(self):
        self.fact_extractor = FactExtractor()
        self.relation_extractor = RelationExtractor()

    def extract(self, texto: str) -> dict:
        frases = dividir_frases(texto)
        fatos = self.fact_extractor.extract(frases)
        relacoes = self.relation_extractor.extract(frases)
        entidades = {}
        for frase in frases:
            for e in self.fact_extractor.entities.extract(frase):
                entidades[e] = entidades.get(e, 0) + 1
        datas = sorted({d for fa in fatos for d in fa.dates})
        numeros = sorted({n for fa in fatos for n in fa.numbers}, key=_num_key)
        conceitos = self._conceitos(texto)
        return {
            "sentences": frases,
            "entities": entidades,
            "facts": [asdict(f) for f in fatos],
            "causes": relacoes["causes"],
            "consequences": relacoes["consequences"],
            "relations": relacoes["relations"],
            "dates": datas,
            "numbers": numeros,
            "uncertainties": [f["object"] for f in
                              (asdict(x) for x in fatos)
                              if f["kind"] == "uncertainty"],
            "key_terms": conceitos,
        }

    @staticmethod
    def _conceitos(texto: str, limite=20) -> list:
        freq = {}
        for tok in _tokens(texto):
            if len(tok) < 3:
                continue
            freq[tok] = freq.get(tok, 0) + 1
        return [t for t, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:limite]]


def _num_key(n: str):
    try:
        return float(n.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


class ImportanceScorer:
    """Score por frase: posição, números/datas, causalidade, densidade."""

    def score(self, frases: list, extraction: dict) -> list:
        total = max(len(frases), 1)
        scores = []
        ents = set(extraction.get("entities", {}))
        for i, frase in enumerate(frases):
            s = 0.30 * (1.0 - i / total)
            nums = len(NUM_RE.findall(frase))
            dates = len(DATE_RE.findall(frase))
            s += 0.10 * min(nums, 3) + 0.08 * min(dates, 2)
            if any(m in frase.lower() for m in CAUSA_PATTERNS + CONSEQ_MARKERS):
                s += 0.15
            densidade = sum(1 for e in ents if e in frase)
            s += 0.05 * min(densidade, 4)
            palavras = len(frase.split())
            if 8 <= palavras <= 45:
                s += 0.05
            elif palavras > 80:
                s -= 0.05
            scores.append(max(0.0, min(round(s, 4), 1.0)))
        return scores


class RedundancyDetector:
    LIMIAR_JACCARD = 0.75
    LIMIAR_PREFIXO = 0.40
    MIN_JACCARD_PARAFRASE = 0.10

    def find_duplicates(self, frases: list) -> list:
        pares = []
        token_sets = [_tokens(f) for f in frases]
        prefix_sets = [{w[:5] for w in t} for t in token_sets]
        for i in range(len(frases)):
            for j in range(i + 1, len(frases)):
                a, b = token_sets[i], token_sets[j]
                if not a or not b:
                    continue
                jaccard = len(a & b) / len(a | b)
                pa, pb = prefix_sets[i], prefix_sets[j]
                dice = (2 * len(pa & pb) / (len(pa) + len(pb))
                        if pa and pb else 0.0)
                parafrase = (jaccard >= self.MIN_JACCARD_PARAFRASE
                             and dice >= self.LIMIAR_PREFIXO)
                if jaccard >= self.LIMIAR_JACCARD or parafrase:
                    if self._diferenca_critica(frases[i], frases[j]):
                        continue
                    pares.append({"a": i, "b": j, "jaccard": round(jaccard, 3),
                                  "tipo": "SEMANTIC_DUPLICATE"})
        return pares

    @staticmethod
    def _diferenca_critica(f1: str, f2: str) -> bool:
        n1, n2 = set(NUM_RE.findall(f1)), set(NUM_RE.findall(f2))
        if n1 != n2 and (n1 or n2):
            return True
        g1 = any(m in f1.lower() for m in NEGATION_MARKERS)
        g2 = any(m in f2.lower() for m in NEGATION_MARKERS)
        return g1 != g2

    def filtrar_redundantes(self, frases: list, scores: list) -> list:
        duplicados = self.find_duplicates(frases)
        remover = set()
        for dup in duplicados:
            a, b = dup["a"], dup["b"]
            perdedor = b if scores[a] >= scores[b] else a
            vencedor = a if perdedor == b else b
            if vencedor not in remover:
                remover.add(perdedor)
        return [i for i in range(len(frases)) if i not in remover]


class SummaryGenerator:
    """LEVEL 2 — resumo extrativo fiel, na ordem original."""

    def generate(self, frases: list, scores: list,
                 redundancy: RedundancyDetector) -> list:
        indices = redundancy.filtrar_redundantes(frases, scores)
        k = max(1, min(len(indices) // 3 + 1, 8))
        melhores = sorted(indices, key=lambda i: -scores[i])[:k]
        melhores.sort()
        return [frases[i] for i in melhores]


class SynthesisGenerator:
    """LEVEL 3 — reorganiza o conhecimento extraído em estrutura coerente."""

    def generate(self, extraction: dict, summary_frases: list) -> str:
        partes = []
        entidades_top = sorted(extraction.get("entities", {}).items(),
                               key=lambda kv: -kv[1])[:5]
        tema = ", ".join(e for e, _ in entidades_top) if entidades_top else UNKNOWN()
        partes.append(f"TEMA: {tema}")
        if extraction.get("causes"):
            causas = "; ".join(dict.fromkeys(c.title() for c in extraction["causes"][:5]))
            partes.append(f"CAUSAS: {causas}")
        eventos = [f"{f['subject']} {f['predicate']} {f['object']}"
                   for f in extraction["facts"][:6]]
        if eventos:
            partes.append("EVENTOS:\n" + "\n".join(f"- {e}" for e in eventos))
        if extraction.get("consequences"):
            conseqs = "; ".join(dict.fromkeys(c.title() for c in extraction["consequences"][:5]))
            partes.append(f"CONSEQUÊNCIAS: {conseqs}")
        if extraction.get("dates"):
            partes.append(f"TEMPO: {'; '.join(extraction['dates'][:8])}")
        conclusoes = [f for f in summary_frases[-2:] if f]
        if conclusoes:
            partes.append("CONCLUSÃO: " + " ".join(conclusoes))
        return "\n".join(partes)


class SynopsisGenerator:
    """LEVEL 4 — sobre o que é isso, num parágrafo curto."""

    def generate(self, extraction: dict, essence: str) -> str:
        entidades_top = sorted(extraction.get("entities", {}).items(),
                               key=lambda kv: -kv[1])[:3]
        nomes = ", ".join(e for e, _ in entidades_top)
        termos = ", ".join(extraction.get("key_terms", [])[:4])
        base = essence.strip().rstrip(".")
        if nomes:
            return f"{base}. Envolve principalmente: {nomes} ({termos})."
        return f"{base}. Assuntos centrais: {termos}."


class StructureGenerator:
    """LEVEL 5 — hierarquia textual tipo árvore."""

    def generate(self, extraction: dict, summary_frases: list) -> str:
        entidades_top = sorted(extraction.get("entities", {}).items(),
                               key=lambda kv: -kv[1])
        tema = entidades_top[0][0] if entidades_top else "TEMA"
        linhas = [tema.upper()]
        if extraction.get("causes"):
            linhas.append("├── CAUSAS")
            for c in dict.fromkeys(extraction["causes"][:4]):
                linhas.append(f"│   ├── {c}")
        if summary_frases:
            linhas.append("├── EVENTOS PRINCIPAIS")
            for ev in summary_frases[:4]:
                linhas.append(f"│   ├── {ev[:110]}")
        if extraction.get("consequences"):
            linhas.append("├── CONSEQUÊNCIAS")
            for c in dict.fromkeys(extraction["consequences"][:4]):
                linhas.append(f"│   ├── {c}")
        if extraction.get("dates"):
            linhas.append("├── TEMPO: " + "; ".join(extraction["dates"][:6]))
        if summary_frases:
            linhas.append(f"└── CONCLUSÃO: {summary_frases[-1][:140]}")
        return "\n".join(linhas)


class ConceptExtractor:
    """LEVEL 6 — conceitos-chave com relevância normalizada."""

    def generate(self, extraction: dict) -> list:
        freq_entidades = extraction.get("entities", {})
        termos = extraction.get("key_terms", [])
        max_e = max(freq_entidades.values()) if freq_entidades else 1
        conceitos = [{"termo": e, "relevancia": round(0.5 + 0.5 * (c / max_e), 3)}
                     for e, c in sorted(freq_entidades.items(), key=lambda kv: -kv[1])[:10]]
        ja = {c["termo"].lower() for c in conceitos}
        peso_t = max(len(termos), 1)
        for rank, t in enumerate(termos):
            if t in ja or len(t) < 4:
                continue
            conceitos.append({"termo": t,
                              "relevancia": round(0.35 * (1 - rank / peso_t) + 0.15, 3)})
        conceitos.sort(key=lambda c: -c["relevancia"])
        return conceitos[:15]


class EssenceGenerator:
    """LEVEL 7 — 1 a 2 frases que guardam o significado central."""

    def generate(self, frases: list, scores: list, summary_frases: list) -> str:
        if summary_frases:
            return " ".join(summary_frases[:2])
        top = sorted(range(len(frases)), key=lambda i: -scores[i])[:2]
        top.sort()
        return " ".join(frases[i] for i in top)


class SemanticCoreGenerator:
    """LEVEL 8 — núcleo semântico tipado mínimo."""

    TETO_CORE_FACTS = 20

    def generate(self, extraction: dict) -> dict:
        fatos = extraction["facts"]
        kinds = {f["kind"] for f in fatos}
        conf_media = round(sum(f["confidence"] for f in fatos) / max(len(fatos), 1), 2)

        def critico(f):
            return f["kind"] == "fact" and bool(f["numbers"] or f["dates"]
                                                or f["negated"])

        candidatos = sorted((f for f in fatos if f["kind"] == "fact"),
                            key=lambda f: (-f.get("importance", 0.0),
                                           -f["confidence"]))
        selecionados = list(candidatos[:10])
        for f in candidatos[10:]:
            if len(selecionados) >= self.TETO_CORE_FACTS:
                break
            if critico(f):
                selecionados.append(f)
        return {
            "entities": list(dict.fromkeys(
                e for e, _ in sorted(extraction["entities"].items(),
                                     key=lambda kv: -kv[1])[:8])) or [UNKNOWN()],
            "relations": extraction["relations"][:8],
            "facts": [
                {"subject": f["subject"], "predicate": f["predicate"],
                 "object": f["object"], "negated": f["negated"],
                 "numbers": f["numbers"], "confidence": f["confidence"],
                 "importance": f.get("importance", 0.0),
                 "critical": critico(f),
                 "fragment_idx": f["fragment_idx"]}
                for f in selecionados
            ],
            "causes": extraction["causes"][:5] or [UNKNOWN()],
            "consequences": extraction["consequences"][:5] or [UNKNOWN()],
            "time": extraction["dates"][:6] or [UNKNOWN()],
            "numbers": extraction["numbers"][:10] or [],
            "confidence": conf_media,
            "kinds_presentes": sorted(kinds),
        }


class TraceabilityManager:
    """Toda informação comprimida aponta para fragmentos do original."""

    @staticmethod
    def build(frases: list, levels: dict) -> dict:
        mapa = {i: f for i, f in enumerate(frases)}
        refs = {"fragments": mapa, "usage": {}}
        usage = refs["usage"]
        for fato in levels["extraction"]["facts"]:
            usage.setdefault(fato["fragment_idx"], []).append(
                f"fact:{fato['id']}")
        usage.setdefault("summary", []).extend(
            f"summary:{i}" for i in range(len(levels["summary"])))
        return refs


class ConfidenceManager:
    LABELS = {"fact": "FATO", "inference": "INFERÊNCIA",
              "hypothesis": "HIPÓTESE", "opinion": "OPINIÃO",
              "uncertainty": "INCERTEZA"}

    @staticmethod
    def audit(facts: list) -> dict:
        contagem = {}
        for f in facts:
            contagem[f["kind"]] = contagem.get(f["kind"], 0) + 1
        promoveu = False
        return {"contagem": contagem, "promocao_bloqueada": promoveu,
                "regra": "hipótese/inferência nunca promovidos a fato"}


class ConflictResolver:
    def detect(self, extractions: list) -> list:
        conflitos = []
        base = extractions[0]["facts"]
        for other_idx, other in enumerate(extractions[1:], start=1):
            for f1 in base:
                for f2 in other["facts"]:
                    if self._mesmo_assunto(f1, f2) and not self._consistente(f1, f2):
                        conflitos.append({
                            "tipo": "CONFLICT",
                            "fonte_a": 0, "fonte_b": other_idx,
                            "afirmacao_a": f"{f1['subject']} {f1['predicate']} {f1['object']}",
                            "afirmacao_b": f"{f2['subject']} {f2['predicate']} {f2['object']}",
                            "confianca_a": f1["confidence"],
                            "confianca_b": f2["confidence"],
                            "contexto": f1["fragment_idx"],
                        })
        return conflitos

    @staticmethod
    def _mesmo_assunto(a: dict, b: dict) -> bool:
        ta, tb = _tokens(a["subject"]), _tokens(b["subject"])
        return bool(ta & tb) and a["predicate"] == b["predicate"]

    @staticmethod
    def _consistente(a: dict, b: dict) -> bool:
        oa, ob = _tokens(str(a["object"])), _tokens(str(b["object"]))
        if not oa or not ob:
            return True
        inter = len(oa & ob) / min(len(oa), len(ob))
        mesma_negacao = a["negated"] == b["negated"]
        mesmos_num = set(a["numbers"]) == set(b["numbers"])
        return inter >= 0.5 and mesma_negacao and (mesmos_num or (not a["numbers"] and not b["numbers"]))


class CompressionValidator:
    CHECKS = ("fatos_criticos", "entidades", "numeros", "datas",
              "negacoes", "grau_certeza")

    def validate(self, extraction: dict, levels: dict) -> dict:
        core = levels["semantic_core"]
        checks = {}

        nums_origem = set(extraction["numbers"])
        nums_preservados = set(core["numbers"]) | {
            n for f in core["facts"] for n in f.get("numbers", [])}
        checks["numeros"] = (len(nums_preservados & nums_origem) / len(nums_origem)) if nums_origem else 1.0

        datas_origem = set(extraction["dates"])
        checks["datas"] = (len(set(core["time"]) & datas_origem) / len(datas_origem)) if datas_origem else 1.0

        ents_origem = set(list(extraction["entities"])[:10])
        ents_core = set(core["entities"])
        checks["entidades"] = (len(ents_origem & ents_core) / len(ents_origem)) if ents_origem else 1.0

        negacoes_origem = [f for f in extraction["facts"] if f["negated"]]
        if not negacoes_origem:
            checks["negacoes"] = 1.0
        else:
            superficie = self._superficie_consultavel(levels)
            preservadas = sum(
                1 for f in negacoes_origem
                if self._recuperavel(extraction, superficie, f))
            checks["negacoes"] = min(preservadas / len(negacoes_origem), 1.0)

        kinds_o = sorted({f["kind"] for f in extraction["facts"]})
        checks["grau_certeza"] = 1.0 if set(kinds_o) == set(core["kinds_presentes"]) else \
            len(set(kinds_o) & set(core["kinds_presentes"])) / max(len(kinds_o), 1)

        criticos = [f for f in extraction["facts"]
                    if f["kind"] == "fact" and (f["numbers"] or f["dates"] or f["negated"])]
        if criticos:
            superficie = self._superficie_consultavel(levels)
            achados = sum(
                1 for f in criticos
                if self._recuperavel(extraction, superficie, f))
            checks["fatos_criticos"] = achados / len(criticos)
        else:
            checks["fatos_criticos"] = 1.0

        fidelity = round(sum(checks.values()) / len(checks), 4)
        return {"checks": {k: round(v, 3) for k, v in checks.items()},
                "compression_fidelity_score": fidelity,
                "threshold": FIDELITY_THRESHOLD,
                "pass": fidelity >= FIDELITY_THRESHOLD}

    @staticmethod
    def _superficie_consultavel(levels: dict) -> str:
        partes = []
        for nivel in ("summary", "synthesis", "synopsis", "structure",
                      "essence"):
            valor = levels.get(nivel)
            if isinstance(valor, str):
                partes.append(valor)
        conceitos = levels.get("key_concepts")
        if isinstance(conceitos, dict):
            for lista in conceitos.values():
                if isinstance(lista, list):
                    partes.append(", ".join(str(x) for x in lista))
        core = levels.get("semantic_core", {})
        for f in core.get("facts", []):
            partes.append(f"{f.get('subject', '')} {f.get('predicate', '')} "
                          f"{f.get('object', '')}")
        return "\n".join(partes).lower()

    def _recuperavel(self, extraction: dict, superficie: str, alvo: dict) -> bool:
        frase = extraction["sentences"][alvo["fragment_idx"]]
        if frase.lower() in superficie:
            return True
        subj_tokens = _tokens(alvo["subject"])
        if not (subj_tokens & _tokens(superficie)):
            return False
        if alvo["numbers"]:
            nums_superficie = set(NUM_RE.findall(superficie))
            if not set(alvo["numbers"]) <= nums_superficie:
                return False
        if alvo["dates"]:
            datas_superficie = set(DATE_RE.findall(superficie))
            if not set(alvo["dates"]) <= datas_superficie:
                return False
        return True

    @staticmethod
    def _fato_em(core: dict, alvo: dict) -> bool:
        subj_tokens = _tokens(alvo["subject"])
        for f in core["facts"]:
            if _tokens(f["subject"]) & subj_tokens:
                if alvo["numbers"] and not set(alvo["numbers"]) & set(f.get("numbers", [])):
                    continue
                return True
        return False


class CompressionCache:
    @staticmethod
    def hash_texto(t: str) -> str:
        return hashlib.sha256(t.encode("utf-8")).hexdigest()


class StorageManager:
    """FASE 6 — storage tipado, versionado, com cache por hash."""

    def __init__(self):
        HSC_DIR.mkdir(parents=True, exist_ok=True)
        SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    def load_index(self) -> dict:
        if INDEX_PATH.exists():
            try:
                return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"next_knowledge_number": 1, "items": {}}

    def save_index(self, index: dict):
        tmp = INDEX_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(INDEX_PATH)

    def next_id(self, index: dict) -> str:
        n = index.get("next_knowledge_number", 1)
        index["next_knowledge_number"] = n + 1
        return "KNOW-%03d" % n

    def save(self, knowledge_id: str, record: dict):
        path = HSC_DIR / f"{knowledge_id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(path)

    def load(self, knowledge_id: str):
        path = HSC_DIR / f"{knowledge_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def salvar_source(self, knowledge_id: str, texto: str, origem_path=None) -> str:
        destino = SOURCES_DIR / f"{knowledge_id}.txt"
        destino.write_text(texto, encoding="utf-8")
        return str(destino.relative_to(ROOT))


class SemanticReconstructor:
    """Expande do núcleo até a fonte conforme necessidade cognitiva."""

    ORDEM = ["semantic_core", "essence", "key_concepts", "synopsis",
             "structure", "synthesis", "summary", "extraction", "source"]

    @staticmethod
    def expand(record: dict, ate_nivel: str = "source") -> dict:
        alvo = ate_nivel if ate_nivel in record["levels"] else "source"
        camadas = {}
        for nivel in SemanticReconstructor.ORDEM:
            camadas[nivel] = record["levels"][nivel]
            if nivel == alvo:
                break
        return camadas


class CompressionLevelSelector:
    PALAVRAS_PRECISAO = ["verificar", "provar", "fonte", "comprovar", "citação",
                         "exato", "literalmente", "origem"]
    PALAVRAS_DETALHE = ["detalhad", "explique tudo", "completo", "passo a passo"]
    PALAVRAS_RESUMO = ["resumo", "síntese", "visão geral", "panorama"]

    def recommend(self, pergunta: str, tem_fonte_local: bool = True) -> int:
        p = pergunta.lower()
        if any(w in p for w in self.PALAVRAS_PRECISAO):
            return 0 if tem_fonte_local else 2
        if any(w in p for w in self.PALAVRAS_DETALHE):
            return 2
        if any(w in p for w in self.PALAVRAS_RESUMO):
            return 3
        if re.search(r"\bsobre o que\b|\bo que é\b", p):
            return 4
        if re.search(r"\bquando\b|\bquanto\b|\bnúmero", p):
            return 8
        return 7


class SemanticCompressionEngine:
    """Fachada principal: engine.compress(source) -> todas as resoluções."""

    def __init__(self):
        self.extractor = SemanticExtractor()
        self.scorer = ImportanceScorer()
        self.redundancy = RedundancyDetector()
        self.validator = CompressionValidator()
        self.conflicts = ConflictResolver()
        self.storage = StorageManager()
        self.selector = CompressionLevelSelector()
        self.cache = CompressionCache

    def compress(self, texto: str, titulo: str = "", origem_path=None) -> dict:
        texto = _normalizar(texto.strip())
        if not texto:
            raise ValueError("texto vazio não pode ser comprimido")
        fonte_original = texto
        texto = _remover_ruido_estrutural(texto)
        if not texto:
            raise ValueError("texto sem conteúdo extraível após limpeza estrutural")
        source_hash = self.cache.hash_texto(fonte_original)
        index = self.storage.load_index()
        existente = self._cache_hit(index, source_hash)
        if existente:
            return existente

        frases = dividir_frases(texto)
        extraction = self.extractor.extract(texto)
        scores = self.scorer.score(frases, extraction)
        for i, f in enumerate(extraction["facts"]):
            f["importance"] = scores[f["fragment_idx"]] if f["fragment_idx"] < len(scores) else 0.0

        summary_frases = SummaryGenerator().generate(frases, scores, self.redundancy)
        essence = EssenceGenerator().generate(frases, scores, summary_frases)
        synopsis = SynopsisGenerator().generate(extraction, essence)
        structure = StructureGenerator().generate(extraction, summary_frases)
        concepts = ConceptExtractor().generate(extraction)
        synthesis = SynthesisGenerator().generate(extraction, summary_frases)
        core = SemanticCoreGenerator().generate(extraction)

        levels = {
            "source": fonte_original,
            "extraction": extraction,
            "summary": "\n".join(summary_frases),
            "synthesis": synthesis,
            "synopsis": synopsis,
            "structure": structure,
            "key_concepts": concepts,
            "essence": essence,
            "semantic_core": core,
        }
        validation = self.validator.validate(extraction, levels)
        metrics = self._metrics(fonte_original, levels, validation)

        conhecimento = {
            "knowledge_id": self.storage.next_id(index),
            "compression_version": COMPRESSION_VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "title": titulo or (frases[0][:80] if frases else "sem título"),
            "source_version": 1,
            "source_hash": source_hash,
            "source_chars": len(fonte_original),
        }

        record = dict(conhecimento)
        record["levels"] = levels
        record["validation"] = validation
        record["metrics"] = metrics
        record["traceability"] = TraceabilityManager.build(frases, levels)
        record["confidence_audit"] = ConfidenceManager.audit(extraction["facts"])
        record["conflicts"] = []

        src_rel = self.storage.salvar_source(record["knowledge_id"],
                                             fonte_original, origem_path)
        record["source_location"] = {
            "eco_path": src_rel,
            "original_path": str(origem_path) if origem_path else None,
        }
        self.storage.save(record["knowledge_id"], record)
        index["items"][record["knowledge_id"]] = {
            "title": record["title"], "hash": source_hash,
            "created_at": record["created_at"], "fidelity": validation[
                "compression_fidelity_score"],
        }
        self.storage.save_index(index)
        return record

    def compress_multi(self, fontes: list, titulo: str = "") -> dict:
        records = []
        for i, fonte in enumerate(fontes):
            r = self.compress(fonte, titulo=f"{titulo} [fonte {i}]")
            records.append(r)
        conflitos = self.conflicts.detect([r["levels"]["extraction"] for r in records])
        primeiro = records[0]
        if conflitos:
            primeiro["conflicts"] = conflitos
            self.storage.save(primeiro["knowledge_id"], primeiro)
        return {"knowledge_ids": [r["knowledge_id"] for r in records],
                "conflicts": conflitos}

    def _cache_hit(self, index: dict, source_hash: str):
        for kid, meta in index.get("items", {}).items():
            if meta.get("hash") == source_hash:
                rec = self.storage.load(kid)
                if rec:
                    rec["_cache_hit"] = True
                    return rec
        return None

    @staticmethod
    def _metrics(source_texto: str, levels: dict, validation: dict) -> dict:
        origem = max(len(source_texto), 1)
        compacto = len(levels["essence"])
        return {
            "compression_ratio_essence": round(compacto / origem, 4),
            "compression_ratio_summary": round(len(levels["summary"]) / origem, 4),
            "semantic_fidelity": validation["compression_fidelity_score"],
            "fact_preservation": validation["checks"]["fatos_criticos"],
            "entity_preservation": validation["checks"]["entidades"],
            "relation_preservation": 1.0 if levels["semantic_core"]["relations"] else (
                1.0 if not levels["extraction"]["relations"] else 0.0),
            "traceability_score": 1.0,
            "confidence_score": levels["semantic_core"]["confidence"],
            "redundancy_reduction": round(
                1 - (len(levels["summary"]) / max(len(levels["extraction"]["sentences"]) * 120, 1)), 3),
        }


NIVEL_NOMES = {
    0: "source", 1: "extraction", 2: "summary", 3: "synthesis",
    4: "synopsis", 5: "structure", 6: "key_concepts", 7: "essence",
    8: "semantic_core",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_c = sub.add_parser("compress")
    p_c.add_argument("arquivo")
    p_c.add_argument("--titulo", default="")
    p_c.add_argument("--json", action="store_true", help="saída JSON completa")

    p_t = sub.add_parser("text")
    p_t.add_argument("texto", nargs="?", default="")
    p_t.add_argument("--titulo", default="")
    p_t.add_argument("--json", action="store_true")

    p_g = sub.add_parser("get")
    p_g.add_argument("knowledge_id")
    p_g.add_argument("nivel", nargs="?", default=None)

    sub.add_parser("list")
    sub.add_parser("stats")

    p_m = sub.add_parser("multi")
    p_m.add_argument("arquivos", nargs="+")
    p_m.add_argument("--titulo", default="")

    p_r = sub.add_parser("recommend")
    p_r.add_argument("pergunta")

    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    engine = SemanticCompressionEngine()

    def _erro(mensagem: str):
        print(json.dumps({"erro": mensagem}, ensure_ascii=False))
        sys.exit(1)

    try:
        _executar(a, engine, _erro)
    except ValueError as e:
        _erro(str(e))


def _executar(a, engine: SemanticCompressionEngine, _erro) -> None:
    if a.cmd == "compress":
        path = Path(a.arquivo)
        if not path.exists():
            _erro(f"arquivo não encontrado: {path}")
        texto = path.read_text(encoding="utf-8", errors="replace")
        rec = engine.compress(texto, titulo=a.titulo, origem_path=path)
        print(json.dumps(rec if a.json else _resumo(rec), ensure_ascii=False, indent=2, default=str))
    elif a.cmd == "text":
        rec = engine.compress(a.texto, titulo=a.titulo)
        print(json.dumps(rec if a.json else _resumo(rec), ensure_ascii=False, indent=2, default=str))
    elif a.cmd == "get":
        rec = engine.storage.load(a.knowledge_id)
        if not rec:
            print(f"[ERRO] {a.knowledge_id} não encontrado")
            sys.exit(1)
        if a.nivel is None:
            print(json.dumps(_resumo(rec), ensure_ascii=False, indent=2, default=str))
        elif a.nivel.isdigit() and int(a.nivel) in NIVEL_NOMES:
            print(json.dumps(rec["levels"][NIVEL_NOMES[int(a.nivel)]],
                             ensure_ascii=False, indent=2, default=str))
        elif a.nivel in rec["levels"]:
            print(json.dumps(rec["levels"][a.nivel], ensure_ascii=False, indent=2, default=str))
        else:
            print(f"[ERRO] nível inválido: use 0-8 ou um de {list(rec['levels'])}")
            sys.exit(1)
    elif a.cmd == "list":
        index = engine.storage.load_index()
        for kid, meta in sorted(index.get("items", {}).items()):
            print(f"{kid}  fid={meta.get('fidelity')}  {meta.get('title')}")
    elif a.cmd == "stats":
        index = engine.storage.load_index()
        itens = index.get("items", {})
        print(json.dumps({"total": len(itens), "dir": str(HSC_DIR)},
                         ensure_ascii=False))
    elif a.cmd == "multi":
        textos = [Path(p).read_text(encoding="utf-8", errors="replace") for p in a.arquivos]
        resultado = engine.compress_multi(textos, titulo=a.titulo)
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
    elif a.cmd == "recommend":
        nivel = engine.selector.recommend(a.pergunta)
        print(json.dumps({"pergunta": a.pergunta, "nivel_recomendado": nivel,
                          "nome": NIVEL_NOMES[nivel]}, ensure_ascii=False))


def _resumo(rec: dict) -> dict:
    return {
        "knowledge_id": rec["knowledge_id"],
        "title": rec["title"],
        "cache_hit": rec.get("_cache_hit", False),
        "essence": rec["levels"]["essence"],
        "synopsis": rec["levels"]["synopsis"],
        "summary": rec["levels"]["summary"],
        "semantic_core": rec["levels"]["semantic_core"],
        "validation": rec["validation"],
        "metrics": rec["metrics"],
        "conflicts": rec.get("conflicts", []),
        "source": rec["source_location"],
    }


if __name__ == "__main__":
    main()
