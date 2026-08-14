---
tags: [blockingqueue, cyclicbarrier, fases, java, padrao, sincronizar]
aliases: [Java: Concorrência com threads e locks]
date: 2026-08-14
---

# Java: Concorrência com threads e locks

**Fonte:** java

## Conceitos centrais

`java.lang.Thread` é a unidade de execução; `Runnable`/`Callable` descrevem trabalho. Criar threads na mão por chamada é anti-padrão — use **`ExecutorService`** (pools): `Executors.newFixedThreadPool(n)`, `newCachedThreadPool`, `newScheduledThreadPool`. Trabalho assíncrono: `submit` retorna `Future`; `invokeAll`/`invokeAny` para lote. `CompletableFuture` compõe futuros com `thenApply`, `thenCompose`, `exceptionally` e `allOf`, cobrindo 90% das necessidades de async sem locks manuais.

Sincronização: `synchronized` (monitor) ou `ReentrantLock` (tryLock com timeout, fairness, interrupção). Alternativas de alto nível: `AtomicInteger`/`AtomicReference` (CAS lock-free), `ConcurrentHashMap` (segmentado, sem bloqueio de leitura), `Semaphore` (limitar concurrency), `CountDownLatch`/`CyclicBarrier` (sincronizar fases), `BlockingQueue` (producer-consumer).

## Idioms

- Producer-consumer: `ArrayBlockingQueue` + executor; nunca `wait/notify` na mão para esse padrão.
- `ConcurrentHashMap.computeIfAbsent` para caches thread-safe sem lock externo.
- `ThreadLocal` para estado por thread (contexto, conexões), mas lembre de `remove()` em `finally` — senão, vazamento em pools.

## Armadilhas

- **Deadlock**: ordem consistente de aquisição de locks + timeouts (`tryLock(ms)`); use `jstack`/`jcmd Thread.print` para diagnosticar.
- **Starving/races**: não-volatile counter é o clássico; use `AtomicLong`/`LongAdder` (LongAdder para hotspots de escrita intensa).
- **Thread safety de simples mutações**: `HashMap`, `ArrayList`, `SimpleDateFormat` não são thread-safe. `StringBuffer` foi substituído por `StringBuilder` (não thread-safe) — thread-safety tem custo.
- Esquecer de shutdown: `ExecutorService` precisa `shutdown()`/`awaitTermination`, senão threads-fantasma impedem o exit da JVM.

## Boas práticas

- Prefira código imutável + estruturas concorrentes prontas a locks manuais.
- Documente o contrato de concorrência de cada classe (o que é garantido, o que precisa de sincronização externa).
- Para alta contensão de escrita em contadores, `LongAdder` > `AtomicLong` > `synchronized`.
## Conexoes

- [[cluster-hub-programacao]]
- [[java-garbage-collection-e-tuning]]
- [[java-jvm-bytecode-e-memory-model]]
- [[java-streams-e-lambdas]]
- [[padrao-hub-padroes]]