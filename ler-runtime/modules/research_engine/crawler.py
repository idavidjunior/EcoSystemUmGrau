"""Crawler — extrai conteúdo real das URLs mais promissoras."""

import logging
import re
import urllib.request
import urllib.error
import concurrent.futures
from typing import List

from .models import Finding

log = logging.getLogger("research.crawler")

MAX_CRAWL_PAGES = 8
MAX_CONTENT_CHARS = 3000
MAX_WORKERS = 4


def crawl_top_findings(findings: List[Finding], max_pages: int = MAX_CRAWL_PAGES) -> List[Finding]:
    """Faz crawl das URLs com maior relevance_score.

    Modifica os achados in-place: substitui snippet por conteúdo extraído
    e aumenta relevance_score para 0.7 quando o crawl é bem-sucedido.

    Returns:
        Lista de achados (a mesma referência, modificada)
    """
    if not findings:
        return findings

    # Ordena por score decrescente, pega os top N
    sorted_findings = sorted(findings, key=lambda f: f.relevance_score, reverse=True)
    to_crawl = sorted_findings[:max_pages]

    log.info("Crawler: crawlando %d de %d achados", len(to_crawl), len(findings))

    def _fetch(f: Finding) -> Finding:
        try:
            content = _fetch_page(f.url)
            if content:
                f.snippet = content[:MAX_CONTENT_CHARS]
                f.relevance_score = 0.7
                log.info("  OK: %s (%d chars)", f.url[:60], len(content))
            else:
                log.info("  VAZIO: %s", f.url[:60])
        except Exception as e:
            log.warning("  ERRO: %s — %s", f.url[:60], e)
        return f

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(executor.map(_fetch, to_crawl))

    return findings


def _fetch_page(url: str) -> str:
    """Busca conteúdo de uma URL e extrai texto limpo."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,text/plain",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return ""
            raw = resp.read(500_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError):
        return ""

    return _html_to_text(raw)


def _html_to_text(html: str) -> str:
    """Converte HTML em texto legível, removendo tags e scripts."""
    # Remove script e style
    text = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decodifica entidades HTML
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    text = re.sub(r'&nbsp;', ' ', text)
    # Limpa espaços extras
    text = re.sub(r'\s+', ' ', text).strip()
    return text
