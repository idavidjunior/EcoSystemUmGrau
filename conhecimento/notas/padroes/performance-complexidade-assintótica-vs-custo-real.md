---
tags: [espalhados, list, mapa, padrao, performance, ponteiros]
aliases: [Performance: complexidade assintótica vs custo real]
date: 2026-08-13
---

# Performance: complexidade assintótica vs custo real

**Fonte:** performance

Big-O é o primeiro filtro, não a resposta final. Um algoritmo O(n log n) com péssima localidade de cache pode perder para O(n²) em tamanhos reais, e o custo dominante em sistemas modernos raramente é o número de operações — é o acesso a memória e syscalls.

**O que custa de verdade (latências aproximadas, ordem de grandeza):** CPU cycle ~0.3ns; cache L1 ~1ns; L2 ~4ns; L3 ~15ns; RAM ~80-100ns; SSD ~50-150µs; rede em DC ~0.5ms; rede geográfica 20-100ms; disk seek ~10ms. **Acesso a disco é ~100.000x mais caro que um ciclo de CPU.** Tradução: reduzir syscalls (cada `read`/`write` tem overhead de kernel — user/kernel mode switch) e melhorar localidade de cache rende mais que trocar um sort.

**Cache locality:** acessar dados contíguos (arrays, slices) aproveita linhas de cache (64 bytes) — loop linear sobre array pode ser 10-50x mais rápido que percorrer linked list ou mapa com ponteiros espalhados. Regras: 1) prefira arrays/struct-of-arrays sobre listas encadeadas em hot path; 2) iterar por linha vs por coluna em matriz muda localidade; 3) padding de structs: ordem dos campos afeta o uso de cache; 4) batch/bulk I/O: ler 1000 linhas com 1 query > 1000 queries (N+1 é o anti-padrão máximo); 5) bufferização: juntar escritas (batch insert, log flush) reduz fsync/syscalls.

**Syscalls e I/O:** cada syscall = trap + copy entre user/kernel space. Minimize: use buffers (bufio), I/O assíncrono (io_uring/epoll) em vez de bloqueante por conexão, e zero-copy quando possível. I/O de rede: conectar é caro — use connection pooling (HTTP, DB, gRPC). Deserialização/JSON parsing: domina o tempo de muitas APIs — perfil com `perf` antes de culpar o banco.

**Decisão prática:** 1) primeiro classifique o dado (n pequeno? n=10⁷?), o acesso (aleatório vs sequencial), o tipo de I/O (memória, disco, rede); 2) escolha estrutura por padrão de acesso (map para lookup, slice ordenado para range scan, hash join vs nested loop); 3) meça o resultado real: tempo de parede, não contagem de ops; 4) só então vale a pena o algoritmo mais \"assintoticamente melhor\" — e até lá, optimize a constante (localidade, alocação) que costuma vencer no mundo real.
## Conexoes

- [[cluster-hub-programacao]]
- [[espera-adaptativa-por-tipo-de-recurso]]
- [[padrao-hub-padroes]]
- [[performance-caching-em-camadas-e-invalidação]]
- [[performance-concorrência-e-paralelismo-quando-vale-a-pena]]
- [[performance-profiling-primeiro-onde-o-tempo-realmente-vai]]