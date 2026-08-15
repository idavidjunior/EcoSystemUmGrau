---
tags: [finalizadas, java, listeners, padrao, registrados, removidos]
aliases: [Java: Garbage Collection e tuning]
date: 2026-08-15
---

# Java: Garbage Collection e tuning

**Fonte:** java

## Conceitos centrais

A JVM gerencia heap via **GC**. Objetos nascem no **Young Generation** (Eden + Survivor S0/S1), sobreviventes promovidos para **Old Generation**. O GC parou de ser apenas "stop-the-world": hoje há coletores concorrentes (G1, ZGC, Shenandoah). Para a maioria dos casos, **G1** (default desde Java 9) é suficiente; o **ZGC** oferece pausas de sub-milissegundos com alto throughput, mas trade-off de CPU/memória. Selecione pelo objetivo: *latência* (ZGC/Shenandoah) ou *throughput* (ParallelGC).

Principais flag families: tamanhos de geração (`-Xms`, `-Xmx`, `-XX:NewRatio`), tamanho das regiões (`-XX:G1HeapRegionSize`), e metas (`-XX:MaxGCPauseMillis`). Mudar flags sem medir costuma piorar a situação.

## Idioms

- `-Xms` e `-Xmx` iguais evitam *heap resizing* e surpresas de latência inicial.
- Use `-XX:+UseStringDeduplication` e pooling para reduzir pressão de alocação em cargas de texto.
- `System.gc()` em produção: evite — use `-XX:+ExplicitGCInvokesConcurrent` se absolutamente necessário.

## Armadilhas

- **Memory leak em Java**: é retenção acidental — coleções estáticas que crescem sem limite, caches sem eviction, threads não finalizadas, listeners registrados e nunca removidos. Detectar: compare usages de heap em picos iguais (`jmap -histo:live`, `jcmd GC.heap_dump`).
- Referências fracas/soft (`WeakReference`, `SoftReference`, `PhantomReference`) ajudam caches, mas tornam o código sensível ao timing do GC.
- Objetos grandes (humongous no G1) entram direto na Old Gen e fragmentam o heap.

## Boas práticas

- Meça antes de tunar: GC logs (`-Xlog:gc*`), JFR, `jstat`, `jmap`. Decida por dados, não por intuição.
- Perfil de alocação (allocation profiling) revela mais problemas do que GC tuning.
- Prefira primitivos (`long` vs `Long`) e estruturas evitando boxing para reduzir alocação.
## Conexoes

- [[cluster-hub-programacao]]
- [[java-concorrência-com-threads-e-locks]]
- [[java-jvm-bytecode-e-memory-model]]
- [[java-streams-e-lambdas]]
- [[padrao-hub-padroes]]