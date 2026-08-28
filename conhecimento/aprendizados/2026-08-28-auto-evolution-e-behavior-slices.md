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

## Fechamento do ciclo (2026-08-28, v0.2)

Implementei o ciclo fechado de auto-evolução conforme a spec `specs/auto-evolution-ciclo-fechado.spec.md`. O motor agora:

- **Delega** a execução a subagente externo (`opencode run --agent` ou `ler`), nunca altera diretamente.
- **Checkpoint** de código via snapshot dos arquivos do plano (em `runtime/learning/evolution/cycle/`).
- **Detecta mudanças** comparando `git status --porcelain` antes/depois.
- **Valida escopo** com `FORBIDDEN_PATHS` e `allowed_paths` do plano.
- **Preflight técnico + ético** obrigatórios (com flag `--no-preflight` para auditoria manual).
- **Testes** via `valida_specs.py`.
- **Persistência** exclusiva via `persistencia.ps1 run-sync` (nunca git direto).
- **Rollback** em camadas: restaura snapshots de código + checkpoint de runtime, preservando memória de auditoria.
- **Idempotência** por fingerprint (hash do gap + arquivos + steps).
- **Lock** por repositório com tratamento de lock órfão (`_process_alive` via tasklist).
- **Máquina de estados** enxuta (18 estados funcionais, não os 28 da spec — decisão de simplicidade).

Comportamento seguro por padrão: `evolve` = dry-run; `--apply` sem `--max-plans N` não executa nada (0 planos).

## Lições

- Confirmar estado real do código antes de declarar gaps (evita falso-positivos — ex: memory_engine já tinha confidence/source_type).
- Não duplicar capacidades que já existem (cláusula de não-duplicação).
- Integrar novos scripts ao ecossistema (comandos/skills/imports) para protegê-los da triagem automática.
- Cuidado com `add_memory` disparando reindexação semântica (pode travar se outro processo segura lock).
- Subagente `opencode run` é pesado — teste de integração com `--apply` precisa de timeout > 2min.
- Lock órfão (processo morto) precisa ser detectado por PID vivo (`tasklist`), não só por existência de arquivo.
- `--apply --max-plans 0` deve executar 0 planos (seguro), não "todos" — diferenciar dry-run (0=mostra todos) de apply (0=nenhum).
- O `valida_specs.py` dispara o auto_evolution em runtime (via import), poluindo a saída — validar a spec específica com `--spec`.

## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[arquitetura-resiliência-retry-circuit-breaker-backoff-e-idem]]