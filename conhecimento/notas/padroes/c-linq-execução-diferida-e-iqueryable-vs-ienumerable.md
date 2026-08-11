---
tags: [borda, csharp, padrao, resposta, simples, view]
aliases: [C#: LINQ, execução diferida e IQueryable vs IEnumerable]
date: 2026-08-11
---

# C#: LINQ, execução diferida e IQueryable vs IEnumerable

**Fonte:** csharp

# LINQ, execução diferida e IQueryable vs IEnumerable

LINQ transforma coleções com operadores funcionais. O ponto central é a **execução diferida** (lazy): operadores retornam `IEnumerable<T>` que só executam quando enumerados. Chamadas como `Where`/`Select` apenas montam a query.

## Idioms
- Materialize com `ToList()`/`ToArray()` quando for iterar múltiplas vezes ou consumir depois.
- `IEnumerable<T>` opera em memória; `IQueryable<T>` traduz *expression trees* para o provedor (SQL no EF Core). Chamar `ToList()` antes do `Where` derruba a query inteira no banco.
- `First()` lança se vazio; `FirstOrDefault()`/`SingleOrDefault()` quando a ausência é válida.
- Para contagens use `Count()`/`Any()`; prefira `Any()` a `Count() > 0` (não itera tudo).

## Armadilhas
- Reenumeração re-executa a query: efeitos colaterais e custo dobram; capture em lista.
- Capturar variáveis de loop em lambdas (closure): `x => x == i` captura a mesma variável `i` (corrigido em C# 5 para `foreach`).
- Modificar a coleção durante a iteração lança `InvalidOperationException`.
- Projeção prematura: `Select` antes de filtros transforma itens que serão descartados.
- Cadeias gigantes ou introspecção por item são mais lentas que loops simples; meça com benchmark antes de «otimizar».

```csharp
var names = users.Where(u => u.Active)
                 .Select(u => u.Name)
                 .OrderBy(n => n)
                 .Take(10)
                 .ToList(); // execução acontece aqui
```

Regra prática: deixe a query viva até o ponto de consumo e materialize na borda (API, view, resposta).
## Conexoes

- [[c-asyncawait-task-e-o-synchronizationcontext]]
- [[c-injeção-de-dependência-e-ciclo-de-vida-de-serviços]]
- [[c-struct-vs-class-gc-e-alocação-de-memória]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]