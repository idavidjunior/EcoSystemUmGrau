"""Engine — orquestrador do pipeline de deep research."""

import logging
import time
from typing import Optional, Dict, Any

from .models import ResearchReport, ReportSection
from .planner import create_plan
from .searcher import search_all
from .crawler import crawl_top_findings
from .synthesizer import synthesize
from .reporter import generate_report, report_to_markdown
from .graph_writer import persist
from .cache import ResearchCache

log = logging.getLogger("research.engine")

DEFAULT_CONFIG = {
    "vault_path": r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\conhecimento",
    "kg_path": r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\ler-runtime\knowledge\knowledge_graph.json",
    "max_crawl_pages": 8,
    "max_findings": 15,
    "max_search_terms": 3,
}


class ResearchEngine:
    """Orquestrador do pipeline de deep research.

    Pipeline: Planejamento -> Busca -> Crawling -> Síntese -> Relatório -> Persistência
    """

    def __init__(self, llm_fn=None, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            llm_fn: Função LLM (call_llm_json). Se None, importa automaticamente.
            config: Configuração opcional (vault_path, kg_path, max_crawl_pages, etc.)
        """
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.llm_fn = llm_fn or self._import_llm_fn()
        self.cache = ResearchCache(self.config["vault_path"])
        self.current_phase = "idle"
        self.report: Optional[ResearchReport] = None

    def research(self, theme: str, context: str = "") -> ResearchReport:
        """Executa pipeline completo de deep research.

        Args:
            theme: Tema a pesquisar
            context: Contexto opcional do projeto

        Returns:
            ResearchReport com todos os dados
        """
        start = time.time()
        log.info("=== Deep Research iniciado: '%s' ===", theme)

        # Verifica cache
        cached = self.cache.get(theme)
        if cached:
            log.info("Resultado em cache, reutilizando")
            report = self._dict_to_report(cached)
            self.report = report
            return report

        # Fase 1: Planejamento
        self.current_phase = "planning"
        plan = create_plan(theme, context, self.llm_fn)
        log.info("Fase 1 OK: %d sub-queries", len(plan.subqueries))

        # Fase 2: Busca
        self.current_phase = "searching"
        findings = search_all(plan.subqueries, self.config["max_search_terms"])
        log.info("Fase 2 OK: %d achados brutos", len(findings))

        # Fase 3: Crawling
        self.current_phase = "crawling"
        findings = crawl_top_findings(findings, self.config["max_crawl_pages"])
        log.info("Fase 3 OK: crawl concluído")

        # Fase 4: Síntese
        self.current_phase = "synthesizing"
        synthesis = synthesize(plan, findings, self.llm_fn)
        log.info("Fase 4 OK: %d seções", len(synthesis.get("sections", [])))

        # Fase 5: Relatório
        self.current_phase = "reporting"
        report = generate_report(plan, synthesis, findings, self.llm_fn)
        markdown = report_to_markdown(report)
        log.info("Fase 5 OK: relatório gerado")

        # Fase 6: Persistência
        self.current_phase = "persisting"
        persist(report, markdown, self.config["vault_path"], self.config["kg_path"])
        log.info("Fase 6 OK: persistido")

        # Salva cache
        self.cache.set(theme, {
            "theme": report.theme,
            "objective": report.objective,
            "executive_summary": report.executive_summary,
            "sections": [{"title": s.title, "synthesis": s.synthesis,
                          "key_points": s.key_points, "sources": s.sources,
                          "confidence": s.confidence} for s in report.sections],
            "main_insights": report.main_insights,
            "sources": report.sources,
            "overall_confidence": report.overall_confidence,
            "gaps": report.gaps,
            "generated_at": report.generated_at,
        })

        elapsed = time.time() - start
        self.current_phase = "done"
        self.report = report

        log.info("=== Deep Research concluído em %.1fs ===", elapsed)
        log.info("  Confiança: %.0f%% | Fontes: %d | Gaps: %d",
                 report.overall_confidence * 100, len(report.sources), len(report.gaps))

        return report

    def _dict_to_report(self, data: Dict[str, Any]) -> ResearchReport:
        """Converte dados do cache em ResearchReport."""
        from datetime import datetime
        sections = []
        for s in data.get("sections", []):
            sections.append(ReportSection(
                title=s.get("title", ""),
                synthesis=s.get("synthesis", ""),
                key_points=s.get("key_points", []),
                sources=s.get("sources", []),
                confidence=s.get("confidence", 0.5),
            ))
        return ResearchReport(
            theme=data.get("theme", ""),
            objective=data.get("objective", ""),
            executive_summary=data.get("executive_summary", ""),
            sections=sections,
            main_insights=data.get("main_insights", []),
            sources=data.get("sources", []),
            overall_confidence=data.get("overall_confidence", 0.5),
            gaps=data.get("gaps", []),
            raw_findings=[],
            generated_at=data.get("generated_at", datetime.now().isoformat()),
        )

    def _import_llm_fn(self):
        import sys
        from pathlib import Path
        scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from llm_caller import call_llm_json
        return call_llm_json
