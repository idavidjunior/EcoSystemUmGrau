---
tipo: padrao
tags: [source-registry, fontes, conhecimento, knowledge-graph, memory-engine]
data: 2026-09-03
contexto: Sistema de Inteligência de Fontes e Curadoria de Conhecimento Técnico
decisao: Criar módulo source_registry.py para carregar/buscar fontes do catálogo YAML, integrando com knowledge_graph (nodes de fontes) e memory_engine (proveniência)
impacto: 142 fontes catalogadas em 37 domínios, busca por domínio/autoridade/tags, enriquecimento de memórias com proveniência de fontes
---

# Source Registry — Módulo de Fontes de Conhecimento Técnico

## O que foi feito
- Criado `scripts/source_registry.py`: módulo Python para carregar e buscar fontes do catálogo YAML
- Catálogo `config/programming_sources.yaml`: 142 fontes reais classificadas por domínio, autoridade (A-E), confiabilidade (0-1)
- 37 domínios: python, rust, database, devops, ml, architecture, security, algorithms, etc.
- Integrado com knowledge_graph: importa fontes como nodes TECHNOLOGY com edges BELONGS_TO
- Integrado com memory_engine: `enrich_memory_metadata()` retorna proveniência de fontes relevantes
- Atualizado inventário de estruturas

## Funcionalidades
- `SourceRegistry.search()`: busca flexível por query, domain, authority, tags, category, min_reliability
- `SourceRegistry.get_relevant_sources()`: retorna fontes relevantes para um tópico livre
- `SourceRegistry.get_top_authority()`: fontes de maior autoridade (A/B)
- `SourceRegistry.import_to_knowledge_graph()`: importa fontes como nodes no KG
- `SourceRegistry.enrich_memory_metadata()`: enriquece memórias com referências a fontes
- CLI: `python scripts/source_registry.py stats/search/top/relevant/domains`

## Princípios
- Fontes são pontos de partida, não verdade absoluta
- Qualidade = authority + evidence + reproducibility + freshness + relevance + utility
- Fail-soft: YAML ausente/corrompido não bloqueia ninguém
- Não duplicar: reutiliza knowledge_graph e memory_engine existentes

## Decisão
- Separação SPEC vs catálogo: spec ensina como pensar, YAML ensina onde procurar
- Campo `reliability` (0-1) para ordenação, não como critério absoluto
- `import_to_knowledge_graph` aceita filtro por domains para importação parcial

## Conexoes

- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]