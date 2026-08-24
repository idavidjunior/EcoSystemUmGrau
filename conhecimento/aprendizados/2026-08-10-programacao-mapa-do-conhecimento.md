---
tipo: aprendizado
tags: [programacao, linguagens, engenharia, software, conhecimento, perito, mapa]
data: 2026-08-10
contexto: "Pedido do usuário: o EcoSystemUmGrau deve aprender a programar nas principais linguagens e se tornar perito em engenharia/desenvolvimento de software, mantendo organização, sem bagunça e sem redundância."
decisao: >
  Arquitetura do conhecimento de programação do ecossistema:
  1) FONTE ÚNICA = ler-runtime/knowledge/knowledge_graph.json (campo 'patterns').
     As notas do vault (conhecimento/notas/*) são GERADAS a partir dele — nunca
     editar notas à mão (o gerador remove órfãos).
  2) Novo cluster 'programacao' no generate-obsidian-notes.py (CLUSTERS + label),
     com 27 sources (linguagens + domínios de engenharia) agrupando todas as notas.
  3) Precedência do mapeamento explícito por source sobre o ClusterMapper
     aprendido: mapeamento estático vence; mapper só decide quando a fonte é 'geral'.
  4) Um mapa-mestre (este arquivo) como ÍNDICE navegável — sem duplicar o conteúdo
     dos cards (anti-redundância). Cards vivem SÓ no grafo.
impacto: >
  Ecossistema ganhou 105 cartões de conhecimento destilado (12 linguagens + 11
  domínios de engenharia/IT), semanticamente indexados (memory_engine reindexa a
  cada add) e navegáveis no vault Obsidian via cluster-hub-programacao.
  Base técnica consultável por qualquer agente antes de programar. Próximo passo
  natural: criar skill 'programacao' que aponta para este mapa e para o hub.

## Mapa do conhecimento de programação

**Ponto de entrada no vault:** [[cluster-hub-programacao]] (105 notas).

### Como usar
- Antes de codar em uma linguagem, abra a nota da linguagem no hub (ex.: `python-*`, `javascript-*`, `rust-*`).
- Para decisão de arquitetura, consulte as notas `arquitetura-*` e `design-patterns-*`.
- Para qualidade, `testes-*`, `git-*`, `engenharia-*`, `fundamentos-*`.
- Para produção/operação, `devops-*`, `seguranca-*`, `linux-*`, `performance-*`, `bancos-dados-*`.
- Nunca criar nota solta: conhecimento novo entra no `knowledge_graph.json` e o vault é regerado.

### Linguagens (por source)
- **Python** — sintaxe/núcleo, GIL e concorrência, idioms, decoradores e metaprogramação.
- **JavaScript** — closures/escopo/hoisting, `this`/prototypes, assincronismo (event loop/promises), tipos e coerção.
- **TypeScript** — sistema de tipos estrutural, generics/tipos condicionais, type narrowing e guards.
- **Node.js** — event loop e I/O não bloqueante, CommonJS vs ESM, streams e backpressure.
- **Bash** — expansão/aspas/globbing, exit codes e controle de fluxo.
- **Java** — JVM/bytecode/memory model, GC e tuning, Streams/lambdas, concorrência.
- **Kotlin** — null-safety, corrotinas, funções/propriedades/data classes.
- **C** — ponteiros e memória manual, comportamento indefinido, strings/buffers inseguros.
- **C++** — RAII, move semantics/ownership, templates/constexpr.
- **Rust** — ownership/borrow checker, lifetimes, enums/pattern matching, traits/generics.
- **C#** — async/await e SynchronizationContext, LINQ, struct vs class/GC, DI e ciclo de vida.
- **Go** — goroutines/canais/CSP, interfaces implícitas, slices/maps/ponteiros, context e cancelamento.
- **PHP** — SAPI e modelo de execução, tipos/arrays/coerção, PSRs/autoload/Composer.
- **Ruby** — tudo é objeto/duck typing, blocks/procs/lambdas, Rails (ActiveRecord/MVC).
- **SQL** — modelagem relacional/normalização, índices e planos, joins, transações/ACID.

### Domínios de engenharia (por source)
- **fundamentos** — Big-O, estruturas de dados, ordenação/busca, recursão/divisão-e-conquista, DP/greedy.
- **engenharia** — requisitos/escopo, code review, refactoring seguro, dívida técnica, documentação viva.
- **arquitetura** — estilos e trade-offs, camadas vs hexagonal vs clean, event-driven, DDD, ADRs, resiliência.
- **designpatterns** — creacionais, estruturais, comportamentais, SOLID, anti-patterns.
- **testes** — pirâmide, TDD, mocks/fakes/stubs, testes de contrato/API, cobertura.
- **git** — fluxos de trabalho, rebase vs merge, conventional commits, conflitos/revert.
- **apis-web** — HTTP na prática, REST, autenticação/autorização, serialização/GraphQL.
- **bancos-dados** — SQL vs NoSQL, índices/planos, transações/isolamento, ORM/migrations.
- **seguranca** — OWASP Top 10, sessões seguras, criptografia, RBAC/ABAC, hardening/supply chain.
- **devops** — containers, CI/CD, infra como código, observabilidade.
- **linux** — processos/systemd, filesystems/permissões, shell/automação.
- **performance** — profiling, assintótico vs custo real, caching, concorrência.

## Conexoes

- [[cluster-hub-programacao]]
- [[engenharia-code-review-eficaz]]
- [[engenharia-documentação-que-não-vira-lixo-adr-readme-vivo-co]]
- [[engenharia-dívida-técnica-e-manutenibilidade]]
- [[engenharia-refactoring-seguro]]
- [[engenharia-requisitos-e-definição-de-escopo]]