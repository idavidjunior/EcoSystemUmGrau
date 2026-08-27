"""Synthesizer — filtra, agrupa e sintetiza achados via LLM."""

import json
import logging
import re
from typing import List, Dict, Any

from .models import ResearchPlan, Finding

log = logging.getLogger("research.synthesizer")

MAX_FINDINGS_FOR_LLM = 15

SYSTEM_PROMPT = """Você é um sintetizador de pesquisa técnica. Receba achados brutos e produza uma síntese estruturada.

Responda APENAS com JSON válido:
{
  "sections": [
    {
      "title": "Nome da Seção",
      "synthesis": "Síntese de 2 a 4 frases sobre o tema desta seção",
      "key_points": ["ponto 1", "ponto 2"],
      "sources": ["url1", "url2"],
      "confidence": 0.85
    }
  ],
  "main_insights": ["insight 1", "insight 2", "insight 3"],
  "gaps": ["o que não foi encontrado mas seria importante"],
  "overall_confidence": 0.75
}

Regras:
- Crie de 2 a 5 seções temáticas agrupando achados relacionados
- Cada seção deve ter síntese de 2 a 4 frases e 2 a 4 pontos-chave
- Confiança por seção: 0 a 1 (1 = altamente fundamentado, 0 = especulativo)
- Gaps devem ser honestos — apenas o que realmente não foi encontrado
- Insights principais: os 3 a 5 achados mais relevantes da pesquisa inteira
- Não invente informações que não estejam nos achados"""


def synthesize(plan: ResearchPlan, findings: List[Finding], llm_fn=None) -> Dict[str, Any]:
    """Sintetiza achados brutos em seções estruturadas.

    Returns:
        Dict com sections, main_insights, gaps, overall_confidence
    """
    if llm_fn is None:
        llm_fn = _import_llm_fn()

    if not findings:
        log.warning("Synthesizer: nenhum achado para sintetizar")
        return _empty_synthesis()

    # Formata achados para o LLM
    findings_text = _format_findings(findings[:MAX_FINDINGS_FOR_LLM])

    prompt = f"""Tema: {plan.theme}
Objetivo: {plan.objective}

Achados brutos:
{findings_text}

Sintetize os achados acima seguindo o formato JSON especificado."""

    log.info("Synthesizer: sintetizando %d achados", len(findings))

    # Retry: até 2 tentativas
    for attempt in range(2):
        try:
            result = llm_fn(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.2, max_tokens=2048)
        except Exception as e:
            log.warning("Synthesizer: LLM falhou (%s)", e)
            return _empty_synthesis()

        if not result or "_parse_error" in result:
            log.warning("Synthesizer: JSON inválido do LLM (tentativa %d)", attempt + 1)
            continue

        # Se LLM retornou lista, wrap em dict
        if isinstance(result, list):
            log.warning("Synthesizer: LLM retornou lista, convertendo")
            result = {"sections": result, "main_insights": [], "gaps": [], "overall_confidence": 0.5}

        if isinstance(result, dict):
            # Valida estrutura mínima
            if "sections" not in result:
                result["sections"] = []
            if "main_insights" not in result:
                result["main_insights"] = []
            if "gaps" not in result:
                result["gaps"] = []
            if "overall_confidence" not in result:
                result["overall_confidence"] = 0.5

            log.info("Synthesizer: %d seções, %d insights, %d gaps",
                     len(result["sections"]), len(result["main_insights"]), len(result["gaps"]))
            return result

    return _empty_synthesis()


def _format_findings(findings: List[Finding]) -> str:
    """Formata achados em texto legível para o LLM."""
    lines = []
    for i, f in enumerate(findings, 1):
        lines.append(f"[{i}] {f.title}")
        lines.append(f"    URL: {f.url}")
        lines.append(f"    Trecho: {f.snippet[:500]}")
        lines.append(f"    Relevância: {f.relevance_score}")
        lines.append("")
    return "\n".join(lines)


def _empty_synthesis() -> Dict[str, Any]:
    return {
        "sections": [],
        "main_insights": [],
        "gaps": ["Nenhum achado disponível para síntese"],
        "overall_confidence": 0.0,
    }


def _import_llm_fn():
    import sys
    from pathlib import Path
    scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from llm_caller import call_llm_json
    return call_llm_json
