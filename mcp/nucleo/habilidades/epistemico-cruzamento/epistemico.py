#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cruzamento Epistêmico — Memória + Cache Externo + Aprendizados
Stdlib only, sem deps externas.
"""

import sys
import os
import json
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

BASE = Path(__file__).resolve().parents[4]  # EcoSystemUmGrau root
sys.path.insert(0, str(BASE / "scripts"))

from memory_engine import query as mem_query


def get_memory_context(topic: str, min_confidence: float = 0.5) -> List[Dict]:
    """Busca memórias relevantes com confidence e source_type."""
    results = mem_query(text=topic, min_confidence=min_confidence, limit=10)
    out = []
    for m in results:
        conf = m.get("confidence", 1.0)
        src = m.get("source_type", "desconhecido")
        if conf >= min_confidence:
            out.append({
                "id": m.get("id"),
                "kind": m.get("kind"),
                "task": m.get("task"),
                "summary": m.get("summary"),
                "confidence": conf,
                "source_type": src,
                "tags": m.get("tags", []),
                "created_at": m.get("created_at"),
            })
    return out


def get_wikidata_context(entity: str) -> Dict:
    """Consulta Wikidata via SPARQL para fatos sobre entidade."""
    # Busca mais flexível: label, description, alias
    query = f"""
    SELECT ?item ?itemLabel ?description WHERE {{
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel) = 'pt' || LANG(?itemLabel) = 'en')
      FILTER(CONTAINS(LCASE(?itemLabel), LCASE("{entity}")) ||
             CONTAINS(LCASE(STR(?item)), LCASE("{entity}")))
      OPTIONAL {{ ?item schema:description ?description . FILTER(LANG(?description) = 'pt') }}
    }} LIMIT 10
    """
    url = "https://query.wikidata.org/sparql"
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    full_url = f"{url}?{params}"
    headers = {"User-Agent": "EcoSystemUmGrau-Epistemico/1.0", "Accept": "application/sparql-results+json"}

    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "items": []}

    items = []
    for binding in data.get("results", {}).get("bindings", []):
        items.append({
            "item": binding.get("item", {}).get("value"),
            "label": binding.get("itemLabel", {}).get("value"),
            "description": binding.get("description", {}).get("value", ""),
        })
    return {"items": items, "query": entity}


def get_aprendizados_context(topic: str) -> List[Dict]:
    """Busca em aprendizados consolidados (BM25 simples via grep)."""
    aprendizados_dir = BASE / "conhecimento" / "aprendizados"
    if not aprendizados_dir.exists():
        return []

    items = []
    for md_file in aprendizados_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if topic.lower() in content.lower():
                # Extrai frontmatter básico
                lines = content.split("\n")
                frontmatter = {}
                in_fm = False
                for line in lines:
                    if line.strip() == "---":
                        if not in_fm:
                            in_fm = True
                        else:
                            break
                    elif in_fm and ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip()] = v.strip()
                items.append({
                    "file": md_file.name,
                    "title": frontmatter.get("titulo", md_file.stem),
                    "tipo": frontmatter.get("tipo", "desconhecido"),
                    "tags": frontmatter.get("tags", []),
                    "data": frontmatter.get("data", ""),
                    "snippet": content[:500],
                })
        except Exception:
            continue
    return items


def calculate_avg_confidence(items: List[Dict], conf_key: str = "confidence") -> float:
    if not items:
        return 0.0
    vals = [i.get(conf_key, 1.0) for i in items if conf_key in i]
    return sum(vals) / len(vals) if vals else 0.0


def classify_confidence(conf: float, source_type: str = "") -> str:
    if conf >= 0.9 and source_type in ("experiencia", "api"):
        return "fato_confirmado"
    elif conf >= 0.7:
        return "provável"
    else:
        return "hipótese"


def cruzar(pergunta: str) -> Dict:
    """Função principal: cruza as 3 fontes e retorna síntese."""
    # 1. Memória
    mem_items = get_memory_context(pergunta, min_confidence=0.3)
    mem_conf = calculate_avg_confidence(mem_items)

    # 2. Wikidata (entidades técnicas prováveis na pergunta)
    wikidata_items = []
    for term in ["python", "android", "mcp", "github", "docker", "kubernetes", "api", "sqlite", "gradle", "opencode"]:
        if term in pergunta.lower():
            wd = get_wikidata_context(term)
            wikidata_items.extend(wd.get("items", []))

    # 3. Aprendizados
    apr_items = get_aprendizados_context(pergunta)

    # Síntese simples
    fontes = [
        {"tipo": "memoria", "items": mem_items, "confidence_media": round(mem_conf, 2)},
        {"tipo": "wikidata", "items": wikidata_items[:5], "confidence_media": 0.95 if wikidata_items else 0},
        {"tipo": "aprendizados", "items": apr_items, "confidence_media": 0.9 if apr_items else 0},
    ]

    # Lacunas: tópicos sem memória de alta confiança
    lacunas = []
    if mem_conf < 0.7:
        lacunas.append(f"Memória insuficiente sobre '{pergunta}' (confiança média: {mem_conf:.2f})")
    if not wikidata_items:
        lacunas.append("Nenhum fato externo encontrado no Wikidata")
    if not apr_items:
        lacunas.append("Nenhum aprendizado consolidado relacionado")

    # Recomendação
    if mem_conf >= 0.9 and wikidata_items:
        recomendacao = "Fato bem fundamentado — pode prosseguir com confiança"
    elif mem_conf >= 0.7:
        recomendacao = "Provável — verificar com fonte externa antes de decidir"
    else:
        recomendacao = "Incerto — buscar mais evidências ou registrar como hipótese"

    # Sintese curta
    partes = []
    if mem_items:
        partes.append(f"Memória: {len(mem_items)} itens (conf. média {mem_conf:.2f})")
    if wikidata_items:
        partes.append(f"Wikidata: {len(wikidata_items)} fatos")
    if apr_items:
        partes.append(f"Aprendizados: {len(apr_items)} registros")
    sintese = "; ".join(partes) if partes else "Nenhuma fonte encontrou informação relevante"

    return {
        "pergunta": pergunta,
        "sintese": sintese,
        "fontes": fontes,
        "lacunas": lacunas,
        "recomendacao": recomendacao,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python epistemico.py \"<pergunta>\"")
        sys.exit(1)
    pergunta = " ".join(sys.argv[1:])
    result = cruzar(pergunta)
    print(json.dumps(result, ensure_ascii=False, indent=2))