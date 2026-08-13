---
tags: [cache, compilador, cpu, java, padrao, reordenações]
aliases: [Java: JVM, bytecode e memory model]
date: 2026-08-13
---

# Java: JVM, bytecode e memory model

**Fonte:** java

## Conceitos centrais

Java compila para **bytecode** (`javac` -> `.class`), executado pela **JVM** (Java Virtual Machine). Bytecode é verificado pelo *classloader/verifier* antes da execução, garantindo type-safety em nível de máquina virtual. O **JIT** (Just-In-Time) compila hotspots para código nativo, enquanto o interpretador cobre o resto; observe que código frio continua interpretado, então medir desempenho só com microbenchmarks (JMH) é essencial.

A **Java Memory Model (JMM)** — definida por `happens-before` (JLS §17.4) — é a base de toda concorrência. Regras principais: um `volatile` cria barreira de visibilidade; a entrada/saída de um `synchronized` (ou lock) estabelece ordem; `start()` de uma thread acontece-antes de qualquer ação da thread; junções via `join()` seguem o mesmo princípio. Sem `happens-before`, campos compartilhados podem ser lidos desatualizados (inclusive em loops "infinitos") por causa de cache de CPU e reordenações do compilador.

## Idioms

- Use `volatile` para flags de estado simples, nunca para contadores compostos.
- Prefira imutabilidade (`final`) e tipos de `java.util.concurrent` a locks manuais.

## Armadilhas

- Reordenação de memória não é apenas teórica: sem barreira, dados podem ficar invisíveis entre threads.
- `double`/`long` exigem `volatile` para acesso atômico garantido pela JMM.
- Tipos primitivos (`int`) moram no stack; objetos sempre no heap.

## Boas práticas

- Entenda o que o JIT realmente otimiza: escape analysis pode eliminar alocações e até locks (biased locking, lock elision).
- Use `-XX:+PrintCompilation`, `jhsdb`, `JFR` (Java Flight Recorder) para diagnosticar, em vez de adivinhar.
- Escreva código thread-safe por construção (imutabilidade + `final`) e documente `happens-before` onde ele importa.
## Conexoes

- [[cluster-hub-programacao]]
- [[java-concorrência-com-threads-e-locks]]
- [[java-garbage-collection-e-tuning]]
- [[java-streams-e-lambdas]]
- [[padrao-hub-padroes]]