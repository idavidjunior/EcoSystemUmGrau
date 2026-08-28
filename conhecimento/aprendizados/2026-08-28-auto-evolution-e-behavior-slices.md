---
tipo: decisao
tags: [auto-evolution, cartographer, behavior-slices, arquitetura, evidence-grounding]
data: 2026-08-28
contexto: Usuário pediu para o EcoSystemUmGrau aprender com o Cartographer (miltonian/cartographer), absorver capacidades e evoluir com auto-aprendizado.
decisao: Implementar Auto-Evolution Engine + Behavior Slices + evidência-grounding no memory_engine, e integrar novos scripts para não serem movidos à triagem.
impacto: Ecossistema agora analisa automaticamente gaps vs referências externas e rastreia fluxos de comportamento com evidência até source:line.
---

## Decisão

Criar dois módulos novos inspirados no Cartographer e aprimorar a infraestrutura existente de forma aditiva (sem quebrar o que funciona).

## O que foi feito

1. **scripts/auto_evolution.py** — Motor de auto-análise: compara capacidades de referências externas (ex: Cartographer) com as do ecossistema, detecta gaps, gera planos de evolução com steps/validação/rollback, e persiste assessments. Comandos: `scan`, `gaps`, `plan`, `assess`, `evolve`, `status`.

2. **scripts/behavior_slices.py** — Rastreio de fluxos de comportamento (flows) e changesets, com evidence-grounding (SourceAnchor, ConfidenceLevel, ProvenanceKind). Integra com memory_engine para busca semântica.

3. **scripts/memory_engine.py** — Adicionado parâmetro `source_anchors` (aditivo, não quebra nada) para evidence-grounding de memórias.

4. **scripts/runtime_state.py** — Adicionado backup pré-restore automático no `restore()`.

5. **config/opencode.jsonc** — Adicionado comando `/autoevolve`.

## Aprendizado crítico

O **audit_triagem.py** move scripts órfãos (sem referência externa real) para `scripts/_legado/`. Todo script novo precisa ser referenciado por algo (comando no opencode.jsonc, import, ou referência textual detectável por grep) para não ser movido. Meu `auto_evolution.py` foi movido uma vez; a solução foi criar o comando `/autoevolve` no opencode.jsonc, que cria referência real.

## Lições

- Confirmar estado real do código antes de declarar gaps (evita falso-positivos — ex: memory_engine já tinha confidence/source_type).
- Não duplicar capacidades que já existem (cláusula de não-duplicação).
- Integrar novos scripts ao ecossistema (comandos/skills/imports) para protegê-los da triagem automática.
- Cuidado com `add_memory` disparando reindexação semântica (pode travar se outro processo segura lock).

## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[arquitetura-resiliência-retry-circuit-breaker-backoff-e-idem]]