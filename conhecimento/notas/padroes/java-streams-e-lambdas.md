---
tags: [construção, corromper, java, padrao, performance, pode]
aliases: [Java: Streams e lambdas]
date: 2026-08-20
---

# Java: Streams e lambdas

**Fonte:** java

## Conceitos centrais

`java.util.stream.Stream` abstrai pipelines *lazy* sobre coleções: uma operação terminal (collect, toList, reduce, count, forEach) dispara a computação; intermediárias (map, filter, flatMap, sorted, distinct, limit) são compostas sem execução imediata. A computação é **short-circuit** quando possível: `findFirst()`, `anyMatch()`, `limit()` param de consumir mais fonte assim que satisfeitos. Streams são **single-use**: após operação terminal, a stream está consumida.

Lambdas são *closures*: capturam variáveis efetivamente final. Expressões de método (`Method::ref`) e interfaces funcionais (`Function`, `Predicate`, `Supplier`, `Consumer`, `UnaryOperator`, `BiFunction`) são os blocos de construção.

## Idioms

- `collect(Collectors.toMap(...))` exige chave/valor únicos; conflitos geram `IllegalStateException` — forneça `BinaryOperator` de merge.
- `flatMap` é o caminho para "lista de listas" e para opcionais aninhados: `list.stream().map(Optional::get)` é ruim; use `flatMap(Optional::stream)` (Java 9+).
- `IntStream.range` / `Stream.iterate` para loops indexados ou infinitos com `limit`.

## Armadilhas

- **Ordem de operações importa**: `filter` antes de `map`/`flatMap` reduz trabalho (custo de execução); `sorted` é caro e materializa toda a stream.
- `parallel()` em dados não preparados (listas `LinkedList`, fontes com estado compartilhado) degrada performance e pode corromper estado. Parallel = coleções `ArrayList` + operações independentes, senão não use.
- Streams **não reutilizáveis**; reusar causa `IllegalStateException`. Lambdas capturando variáveis não-final não compilam.
- `Stream.toList()` (Java 16+) retorna lista imutável; `collect(toList())` retorna `ArrayList` mutável — escolha consciente.

## Boas práticas

- Prefira pipelines declarativos a loops aninhados, mas não force: streams são menos indicadas para transformações que precisam de índice ou saída antecipada baseada em estado externo.
- Evite efeitos colaterais dentro de `map`/`filter` (viola natureza funcional e quebra em streams paralelas).
- Para agrupamento: `Collectors.groupingBy(classifier, downstream)` resolve histogramas e agregações em uma linha.
## Conexoes

- [[cluster-hub-programacao]]
- [[java-concorrência-com-threads-e-locks]]
- [[java-garbage-collection-e-tuning]]
- [[java-jvm-bytecode-e-memory-model]]
- [[padrao-hub-padroes]]