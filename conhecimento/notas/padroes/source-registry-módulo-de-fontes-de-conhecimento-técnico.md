---
tags: [category, etc, min, opencodeopencode, padrao, reliability]
aliases: [Source Registry — Módulo de Fontes de Conhecimento Técnico]
date: 2026-09-03
---

# Source Registry — Módulo de Fontes de Conhecimento Técnico

**Fonte:** opencode+opencode

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
- `SourceRegistry.enrich_memory_metadata()`: enriquece memória
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]