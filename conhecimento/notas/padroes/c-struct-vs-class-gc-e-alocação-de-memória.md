---
tags: [arrays, cache, contíguos, csharp, friendly, padrao]
aliases: [C#: struct vs class, GC e alocação de memória]
date: 2026-08-17
---

# C#: struct vs class, GC e alocação de memória

**Fonte:** csharp

# struct vs class, GC e alocação de memória

Em C#, `class` (tipo de referência) vive no heap gerenciado; a variável guarda uma referência. `struct` (tipo de valor) é copiado por valor e pode viver na stack ou inline em arrays — arrays de struct são contíguos e cache-friendly.

## GC
O coletor é generacional (Gen0/1/2) com *mark-and-sweep*; objetos grandes (>85 KB) vão direto para o LOH. Alocar é barato (bump pointer), mas pressão de alocação aumenta o número de coletas. Menos alocação = menos pause.

## Idioms
- Prefira `struct` para dados pequenos, imutáveis e sem polimorfismo (coordenadas, IDs). Use `readonly struct`.
- `Span<T>`/`ref struct` habilitam processamento zero-copy sobre buffers; não podem ser capturados por closures nem usados em `async`.
- `ArrayPool<T>` para buffers reutilizáveis em caminhos quentes.

## Armadilhas
- **Boxing**: atribuir struct a `object`/interface (ou usar em coleções não genéricas) aloca e copia; evite.
- Mutação perdida: alterar uma cópia não altera a origem — `int`, `DateTime` são structs, métodos não mudam o «objeto».
- `default(T)` de struct é «zeroed», nunca `null`; use `Nullable<T>` (`T?`) para valores opcionais.
- `async` captura structs no state machine e pode causar boxing.
- Igualdade: structs usam reflexão por padrão (`Equals`); override `Equals`/`GetHashCode` se comparar muito.

```csharp
readonly struct Point { public readonly int X, Y; }
Span<byte> buffer = stackalloc byte[256]; // zero alocação
```

Regra: pequeno, imutável, sem herança e de curta vida → struct; caso contrário, class. Otimize só sob evidência de profiler.
## Conexoes

- [[c-asyncawait-task-e-o-synchronizationcontext]]
- [[c-injeção-de-dependência-e-ciclo-de-vida-de-serviços]]
- [[c-linq-execução-diferida-e-iqueryable-vs-ienumerable]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]