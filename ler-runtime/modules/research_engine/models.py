"""Estruturas de dados do Research Engine."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class SubQuery:
    id: str
    question: str
    search_terms: List[str]
    priority: int  # 1=alta, 2=media, 3=baixa
    status: str = "pending"  # pending / done / error


@dataclass
class Finding:
    subquery_id: str
    url: str
    title: str
    snippet: str
    relevance_score: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))


@dataclass
class ResearchPlan:
    theme: str
    objective: str
    subqueries: List[SubQuery]
    max_crawl_pages: int = 8
    max_findings: int = 15
    context_hint: str = ""


@dataclass
class ReportSection:
    title: str
    synthesis: str
    key_points: List[str]
    sources: List[str]
    confidence: float


@dataclass
class ResearchReport:
    theme: str
    objective: str
    executive_summary: str
    sections: List[ReportSection]
    main_insights: List[str]
    sources: List[str]
    overall_confidence: float
    gaps: List[str]
    raw_findings: List[Finding] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
