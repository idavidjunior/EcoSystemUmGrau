"""Reporter — gera relatório Markdown a partir da síntese."""

import logging
import re
from typing import Dict, Any, List

from .models import ResearchPlan, Finding, ResearchReport, ReportSection

log = logging.getLogger("research.reporter")

EXECUTIVE_SUMMARY_PROMPT = """Escreva um resumo executivo de 2 a 3 parágrafos sobre a pesquisa realizada.
Seja conciso, técnico e direto. Destaque os achados mais importantes e a confiança geral.
Língua: português do Brasil."""


def generate_report(plan: ResearchPlan, synthesis: Dict[str, Any],
                    findings: List[Finding], llm_fn=None) -> ResearchReport:
    """Gera relatório consolidado a partir da síntese.

    Returns:
        ResearchReport completo
    """
    if llm_fn is None:
        llm_fn = _import_llm_fn()

    log.info("Reporter: gerando relatório para '%s'", plan.theme)

    # Gera resumo executivo via LLM
    executive_summary = _generate_summary(plan, synthesis, llm_fn)

    # Monta seções a partir da síntese
    sections = []
    for s in synthesis.get("sections", []):
        sections.append(ReportSection(
            title=s.get("title", "Sem título"),
            synthesis=s.get("synthesis", ""),
            key_points=s.get("key_points", []),
            sources=s.get("sources", []),
            confidence=s.get("confidence", 0.5),
        ))

    # Coleta URLs únicas
    all_urls = list(dict.fromkeys(f.url for f in findings if f.url))

    # Monta relatório
    report = ResearchReport(
        theme=plan.theme,
        objective=plan.objective,
        executive_summary=executive_summary,
        sections=sections,
        main_insights=synthesis.get("main_insights", []),
        sources=all_urls[:20],
        overall_confidence=synthesis.get("overall_confidence", 0.5),
        gaps=synthesis.get("gaps", []),
        raw_findings=findings,
    )

    log.info("Reporter: relatório gerado (%d seções, %d fontes, confiança %.0f%%)",
             len(sections), len(all_urls), report.overall_confidence * 100)

    return report


def report_to_markdown(report: ResearchReport) -> str:
    """Converte relatório em Markdown com frontmatter YAML para Obsidian."""
    lines = []

    # Frontmatter YAML
    safe_theme = re.sub(r'[^\w\s-]', '', report.theme).strip().replace(' ', '-')
    lines.append("---")
    lines.append(f"title: \"{report.theme}\"")
    lines.append("type: research")
    lines.append(f"date: {report.generated_at[:10]}")
    lines.append(f"confidence: {report.overall_confidence:.2f}")
    lines.append(f"tags: [deep-research, auto-generated, {safe_theme.lower()}]")
    lines.append("---")
    lines.append("")

    # Corpo
    lines.append(f"# {report.theme}")
    lines.append("")
    lines.append(f"**Objetivo:** {report.objective}")
    lines.append(f"**Confiança:** {report.overall_confidence:.0%} | **Fontes:** {len(report.sources)}")
    lines.append("")

    # Resumo executivo
    lines.append("## Resumo Executivo")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")

    # Seções
    for section in report.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.synthesis)
        lines.append("")
        if section.key_points:
            lines.append("**Pontos-chave:**")
            for pt in section.key_points:
                lines.append(f"- {pt}")
            lines.append("")
        lines.append(f"*Confiança da seção: {section.confidence:.0%}*")
        lines.append("")

    # Insights principais
    if report.main_insights:
        lines.append("## Insights Principais")
        lines.append("")
        for insight in report.main_insights:
            lines.append(f"**{insight}**")
            lines.append("")

    # Gaps
    if report.gaps:
        lines.append("## Gaps Identificados")
        lines.append("")
        for gap in report.gaps:
            lines.append(f"- {gap}")
        lines.append("")

    # Fontes
    if report.sources:
        lines.append("## Fontes")
        lines.append("")
        for i, url in enumerate(report.sources[:20], 1):
            lines.append(f"{i}. {url}")
        lines.append("")

    return "\n".join(lines)


def _generate_summary(plan: ResearchPlan, synthesis: Dict[str, Any], llm_fn) -> str:
    """Gera resumo executivo via LLM."""
    insights = synthesis.get("main_insights", [])
    gaps = synthesis.get("gaps", [])
    conf = synthesis.get("overall_confidence", 0.5)
    n_sections = len(synthesis.get("sections", []))

    prompt = f"""Tema: {plan.theme}
Objetivo: {plan.objective}
Número de seções: {n_sections}
Confiança geral: {conf:.0%}
Insights principais: {json.dumps(insights, ensure_ascii=False)}
Gaps identificados: {json.dumps(gaps, ensure_ascii=False)}

Escreva um resumo executivo de 2 a 3 parágrafos."""

    try:
        result = llm_fn(prompt=prompt, system=EXECUTIVE_SUMMARY_PROMPT,
                        temperature=0.3, max_tokens=512)
        # call_llm_json pode retornar dict ou lista
        if isinstance(result, dict) and not result.get("_parse_error"):
            # Se veio como JSON estruturado, pega campo text ou str
            return result.get("text", str(result))
        elif isinstance(result, str) and result:
            return result
        elif isinstance(result, list) and result:
            return str(result[0]) if isinstance(result[0], str) else str(result)
    except Exception as e:
        log.warning("Reporter: LLM falhou ao gerar resumo (%s)", e)

    # Fallback: resumo sem LLM
    parts = [f"A pesquisa sobre '{plan.theme}' identificou {n_sections} seções temáticas."]
    if insights:
        parts.append(f"Achado principal: {insights[0]}.")
    if gaps:
        parts.append(f"Lacuna identificada: {gaps[0]}.")
    parts.append(f"Nível de confiança geral: {conf:.0%}.")
    return " ".join(parts)


def _import_llm_fn():
    import sys
    from pathlib import Path
    scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from llm_caller import call_llm
    return call_llm


# Necessário para _generate_summary
import json
