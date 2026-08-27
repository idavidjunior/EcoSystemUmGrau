"""Searcher — busca web paralela para cada sub-query."""

import json
import logging
import re
import urllib.request
import urllib.parse
import urllib.error
import concurrent.futures
from typing import List

from .models import SubQuery, Finding

log = logging.getLogger("research.searcher")

MAX_RESULTS_PER_TERM = 5
MAX_WORKERS = 6


def search_all(subqueries: List[SubQuery], max_results_per_term: int = MAX_RESULTS_PER_TERM) -> List[Finding]:
    """Executa buscas em paralelo para todas as sub-queries.

    Returns:
        Lista concatenada de achados de todas as sub-queries
    """
    all_findings: List[Finding] = []

    def _search_subquery(sq: SubQuery) -> List[Finding]:
        findings = []
        for term in sq.search_terms[:3]:
            try:
                results = _ddg_search(term, max_results_per_term)
                for r in results:
                    findings.append(Finding(
                        subquery_id=sq.id,
                        url=r.get("url", ""),
                        title=r.get("title", ""),
                        snippet=r.get("snippet", ""),
                        relevance_score=0.5,
                    ))
            except Exception as e:
                log.warning("Searcher: falha ao buscar '%s': %s", term, e)
        return findings

    log.info("Searcher: buscando %d sub-queries em paralelo", len(subqueries))

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_search_subquery, sq): sq for sq in subqueries}
        for future in concurrent.futures.as_completed(futures):
            sq = futures[future]
            try:
                findings = future.result()
                all_findings.extend(findings)
                log.info("  sq_%s: %d achados", sq.id.split("_")[-1], len(findings))
            except Exception as e:
                log.warning("  sq_%s: exceção %s", sq.id, e)

    log.info("Searcher: total de %d achados brutos", len(all_findings))
    return all_findings


def _ddg_search(query: str, max_results: int) -> list:
    """Busca via DuckDuckGo Lite (POST, sem API key)."""
    data = urllib.parse.urlencode({"q": query, "b": "", "kl": ""}).encode()

    req = urllib.request.Request(
        "https://lite.duckduckgo.com/lite/",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError:
        return []

    return _parse_ddg_lite_html(html, max_results)


def _parse_ddg_lite_html(html: str, max_results: int) -> list:
    """Extrai resultados do HTML do DuckDuckGo Lite."""
    results = []

    # DuckDuckGo Lite usa links simples
    links = re.findall(r'href="(https?://[^"]+)"', html)
    # Filtra links do próprio DuckDuckGo
    real_links = [l for l in links if "duckduckgo.com" not in l]

    # Extrai títulos e snippets dos blocos
    blocks = re.findall(
        r'<a[^>]+href="(https?://[^"]+)"[^>]*>\s*([^<]+?)\s*</a>\s*'
        r'(?:<br[^>]*>\s*)?(.*?)(?=<br|</td|</tr|$)',
        html, re.DOTALL
    )

    for href, title, snippet in blocks[:max_results]:
        title = title.strip()
        snippet = re.sub(r'<[^>]+>', '', snippet).strip()
        if "duckduckgo.com" in href:
            continue
        if title and href.startswith("http"):
            results.append({"url": href, "title": title, "snippet": snippet})

    # Fallback: se regex de blocos não funcionou, usa links simples
    if not results:
        for link in real_links[:max_results]:
            results.append({"url": link, "title": link.split("/")[-1].replace("-", " "), "snippet": ""})

    return results
