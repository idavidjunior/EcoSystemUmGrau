---
name: research-engine
description: Deep research automatizado — investiga temas, sintetiza achados multi-fonte e gera relatórios Markdown no vault. Use quando precisar de pesquisa técnica antes de implementar, validar best practices, ou gerar documentação de referência.
---

# Research Engine

## Objetivo

Pesquisa técnica automatizada com pipeline de 6 fases:
Planejamento → Busca → Crawling → Síntese → Relatório → Persistência

## Uso

### CLI
```bash
# Pesquisa sob demanda
python -m research_engine "tema da pesquisa"

# Com contexto do projeto
python -m research_engine "tema" --context "contexto"

# Listar pesquisas salvas
python -m research_engine --list

# Status do módulo
python -m research_engine --status
```

### Python
```python
import sys
sys.path.insert(0, 'ler-runtime/modules')
from research_engine import ResearchEngine

engine = ResearchEngine()
report = engine.research("Docker security best practices")

print(report.theme)
print(report.executive_summary)
print(len(report.sections), "seções")
print(report.overall_confidence, "confiança")
```

## Arquitetura

```
research_engine/
├── models.py        # Dataclasses: SubQuery, Finding, ResearchPlan, ReportSection, ResearchReport
├── planner.py       # Decomição LLM: tema → 3-6 sub-queries
├── searcher.py      # Busca DuckDuckGo Lite (POST) paralela
├── crawler.py       # Fetch das top 8 URLs via urllib
├── synthesizer.py   # Síntese LLM: achados → seções + insights + gaps
├── reporter.py      # Gera Markdown com frontmatter YAML
├── graph_writer.py  # Persiste vault + Knowledge Graph
├── cache.py         # Cache 24h por hash do tema
├── engine.py        # Orquestrador (6 fases)
└── __main__.py      # CLI entry point
```

## Integrações

- **Maestro (G0):** pesquisa prévia antes de G1-PLAN para temas desconhecidos
- **Vault Obsidian:** relatórios em `conhecimento/Research/`
- **Knowledge Graph:** entradas do tipo `research` em `ler-runtime/knowledge/knowledge_graph.json`
- **LLM Caller:** usa `scripts/llm_caller.py` (NVIDIA NIM + fallback OpenAI)
- **Cache:** TTL 24h, evita pesquisas repetidas para o mesmo tema

## Configuração

Via `ResearchEngine(config={...})`:
- `vault_path`: caminho do vault Obsidian
- `kg_path`: caminho do Knowledge Graph
- `max_crawl_pages`: máximo de URLs para crawl (padrão: 8)
- `max_findings`: máximo de achados brutos para síntese (padrão: 15)
- `max_search_terms`: máximo de termos de busca por sub-query (padrão: 3)

## Dependências

- Python stdlib (urllib, json, re, concurrent.futures)
- scripts/llm_caller.py (NVIDIA NIM API)
- Nenhum pacote externo necessário

## Erros conhecidos

- DuckDuckGo HTML GET bloqueado → usando Lite POST (resolvido)
- LLM às vezes retorna lista em vez de dict → tratado com fallback
- Encoding cp1252 no Windows → graph_writer garante UTF-8
