---
tags: [absorve, decoupling, escalam, padrao, performance, pico]
aliases: [Performance: concorrência e paralelismo — quando vale a pena]
date: 2026-08-21
---

# Performance: concorrência e paralelismo — quando vale a pena

**Fonte:** performance

Concorrência (múltiplos fluxos intercalados em uma CPU) ≠ paralelismo (execução simultânea em múltiplas CPUs, Amdahl: ganho ≤ 1/(1-p)). Muita concorrência adiciona locks, overhead e bugs sem ganho — o sênior sabe quando NÃO usar.

**Quando ganha de verdade:** 1) I/O-bound (rede, disco, banco, API externa): a thread/coroutine fica esperando o I/O — paralelizar requests simultâneos aumenta throughput diretamente. Este é o caso 90% das vezes: threads em Go (goroutines), async em Python/Node, threads em Java. 2) CPU-bound com N núcleos: paralelismo real só em múltiplos núcleos (Go goroutines são paralelas em multicore; Python precisa de multiprocessing por causa do GIL para CPU puro). Ganho limitado por Amdahl: a parte serial (mescla de resultados, locks de agregação) sempre pesa.

**Quando NÃO vale:** 1) tarefa única rápida (<1ms) — overhead de criar thread/tarefa e sincronizar supera o ganho; 2) bottleneck único (uma tabela, um lock de banco, um arquivo) — você paraleliza e esbarra no mesmo recurso; 3) trabalho CPU-bound pequeno em ambiente single-core; 4) quando o custo de correção de bugs (race conditions, deadlock, data races) é maior que o ganho de latência mensurável. Paralelismo para latência: só ajuda se o workload for paralelizável e os recursos permitirem (p95 de API cheio de locks não melhora).

**Custo real:** threads custam memória (stack ~1MB+; goroutines ~2KB mas o scheduler custa), contention de locks (escrita compartilhada serializa), data races (corrupção silenciosa), deadlocks/livelocks. Regras: 1) dados compartilhados mínimos e imutáveis quando possível; 2) sincronize com primitivas de alto nível (channels, futures, semáforos — nunca lock+busy-wait); 3) limite a concorrência com semáforo/pool (goroutine por request infinito = OOM/DB overwhelm); 4) evite `sync.Mutex` em hot path quando `atomic`/immutabilidade servem; 5) teste sob contenção (race detector em Go, TSAN em C++, pytest-race) e rode testes paralelos.

**Padrões eficientes:** worker pool (fila + N workers, backpressure), fan-out/fan-in (dispara N, agrega — para chamadas independentes de terceiros), async/await para I/O sem bloquear thread, message queue para decoupling (a fila absorve pico, workers escalam). Comece serial, meça, paralelize apenas o gargalo medido.
## Conexoes

- [[cluster-hub-programacao]]
- [[espera-adaptativa-por-tipo-de-recurso]]
- [[padrao-hub-padroes]]
- [[performance-caching-em-camadas-e-invalidação]]
- [[performance-complexidade-assintótica-vs-custo-real]]
- [[performance-profiling-primeiro-onde-o-tempo-realmente-vai]]