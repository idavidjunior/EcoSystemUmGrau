"""Planner — decompõe tema em sub-perguntas pesquisáveis via LLM."""

import json
import re
import logging
from typing import Optional

from .models import ResearchPlan, SubQuery

log = logging.getLogger("research.planner")

SYSTEM_PROMPT = """Você é um planejador de pesquisa técnica. Dado um tema, decomponha-o em 3 a 6 sub-perguntas pesquisáveis e específicas.

Responda APENAS com JSON válido neste formato:
{
  "objective": "objetivo claro da pesquisa em 1 frase",
  "subqueries": [
    {
      "question": "sub-pergunta específica e pesquisável",
      "search_terms": ["termo1", "termo2", "termo3"],
      "priority": 1
    }
  ],
  "context_hint": "dica contextual opcional para orientar a busca"
}

Prioridade: 1=essencial, 2=importante, 3=complementar.
Cada sub-query deve ter 2 a 3 termos de busca otimizados para mecanismos de busca.
Não inclua explicações, apenas JSON."""


def create_plan(theme: str, context: str = "", llm_fn=None) -> ResearchPlan:
    """Decompõe tema em sub-perguntas pesquisáveis.

    Args:
        theme: Tema da pesquisa
        context: Contexto opcional do projeto
        llm_fn: Função LLM (call_llm_json). Se None, importa de scripts/llm_caller.

    Returns:
        ResearchPlan com sub-queries prontas para busca
    """
    if llm_fn is None:
        llm_fn = _import_llm_fn()

    prompt = f"Tema: {theme}"
    if context:
        prompt += f"\nContexto do projeto: {context}"

    log.info("Planner: decompondo tema '%s'", theme)

    try:
        result = llm_fn(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.2, max_tokens=1024)
    except Exception as e:
        log.warning("Planner: LLM falhou (%s), usando plano mínimo", e)
        return _fallback_plan(theme, context)

    if not result or "_parse_error" in result:
        log.warning("Planner: JSON inválido, tentando extrair...")
        return _fallback_plan(theme, context)

    try:
        subqueries = []
        for i, sq in enumerate(result.get("subqueries", []), 1):
            terms = sq.get("search_terms", [])
            if isinstance(terms, str):
                terms = [terms]
            subqueries.append(SubQuery(
                id=f"sq_{i}",
                question=sq.get("question", f"O que é {theme}?"),
                search_terms=terms[:3],
                priority=min(max(int(sq.get("priority", 2)), 1), 3),
            ))

        if not subqueries:
            log.warning("Planner: LLM retornou 0 sub-queries, usando fallback")
            return _fallback_plan(theme, context)

        return ResearchPlan(
            theme=theme,
            objective=result.get("objective", f"Pesquisar sobre {theme}"),
            subqueries=subqueries,
            context_hint=result.get("context_hint", context),
        )
    except Exception as e:
        log.warning("Planner: falha ao parsear resultado (%s), usando fallback", e)
        return _fallback_plan(theme, context)


def _fallback_plan(theme: str, context: str) -> ResearchPlan:
    """Plano mínimo quando o LLM falha."""
    return ResearchPlan(
        theme=theme,
        objective=f"Pesquisar informações atualizadas sobre {theme}",
        subqueries=[
            SubQuery(
                id="sq_1",
                question=f"O que é {theme} e quais são suas principais características?",
                search_terms=[theme],
                priority=1,
            ),
            SubQuery(
                id="sq_2",
                question=f"Quais são as melhores práticas e exemplos de {theme}?",
                search_terms=[f"{theme} best practices", f"{theme} examples"],
                priority=2,
            ),
        ],
        context_hint=context,
    )


def _import_llm_fn():
    """Importa call_llm_json do scripts/llm_caller."""
    import sys
    from pathlib import Path
    scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from llm_caller import call_llm_json
    return call_llm_json
