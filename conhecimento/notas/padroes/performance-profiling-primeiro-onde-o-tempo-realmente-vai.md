---
tags: [devtools, frontend, padrao, performance, representa, safari]
aliases: [Performance: profiling primeiro — onde o tempo realmente vai]
date: 2026-08-14
---

# Performance: profiling primeiro — onde o tempo realmente vai

**Fonte:** performance

Regra de ouro: NUNCA otimize por achismo. Sem medição você otimiza a função errada enquanto o gargalo real (quase sempre I/O ou query) fica lá, e ainda adiciona complexidade. \"Otimização prematura é a raiz de todo mal\" (Knuth) — mas \"profile antes de otimizar\" é a raiz de todo acerto.

**Metodologia:** 1) defina o objetivo numérico (SLO: p95 < 150ms) antes de medir; 2) gere carga realista (k6, wrk, hey, gatling) com distribuição e cenário de negócio — microbenchmark isolado não representa produção; 3) meça em produção quando possível (profile de prod com amostragem), ou em staging idêntico — não em dev com laptop e DB local; 4) identifique o gargalo dominante, faça UMA mudança por vez e re-meça (A/B do mesmo cenário); 5) documente o resultado esperado vs real.

**Ferramentas por camada:** CPU — `perf` (Linux), `pprof` (Go), async-profiler/JFR (Java), cProfile/py-spy (Python), Chrome DevTools/Safari (frontend). Wall time vs CPU time: se wall >> cpu, o tempo está em espera (I/O, locks, rede, GC) — otimizar CPU não resolve. Memória: heap profile (pprof, MAT, v8 snapshots) para leaks e excesso de alocação; allocation-heavy causa GC pressure. I/O: `strace`/`strace -f -e trace=file,network` (syscalls — veja syscalls lentos, open stat), `iostat`, `iotop`; rede: tcpdump/Wireshark, ping com mtr, `ss` para conexões.

**Técnicas de profiling:** CPU sampler (amostra stack 100x/s → flamegraph com `FlameGraph.pl`/speedscope): leia de baixo para cima procurando barras largas — função que detém tempo é o alvo. Para I/O: latency traces (OpenTelemetry), p95 vs p99. Databases: EXPLAIN ANALYZE + slow query log + `pg_stat_statements` — a resposta \"por que a API é lenta\" costuma estar em uma query ou lock.

**Armadilhas:** 1) otimizar em ambiente errado (cache quente, dados pequenos); 2) confundir correlação com causa (CPU alto pode ser efeito de sync de I/O); 3) micro-otimizar antes de atacar complexidade algorítmica ou N+1; 4) esquecer que o gargalo de produção é frequentemente lock/contenção, não CPU. Comece: meça wall time por camada (request → app → DB/cache/3rd party) e só então perfila a camada dominante.
## Conexoes

- [[cluster-hub-programacao]]
- [[espera-adaptativa-por-tipo-de-recurso]]
- [[padrao-hub-padroes]]
- [[performance-caching-em-camadas-e-invalidação]]
- [[performance-complexidade-assintótica-vs-custo-real]]
- [[performance-concorrência-e-paralelismo-quando-vale-a-pena]]