---
tags: [csharp, iniciar, padrao, padrão, requests, vaza]
aliases: [C#: injeção de dependência e ciclo de vida de serviços]
date: 2026-08-11
---

# C#: injeção de dependência e ciclo de vida de serviços

**Fonte:** csharp

# Injeção de dependência e ciclo de vida de serviços

O ASP.NET Core traz DI embutida no container (`IServiceProvider`). Registre interfaces→implementações em `ConfigureServices`; a resolução preferida é por construtor (constructor injection) — idiomático, testável e explícito.

## Lifetimes
- **Transient**: nova instância a cada resolução (barato, sem estado).
- **Scoped**: uma instância por escopo (tipicamente por request HTTP).
- **Singleton**: uma instância por processo (estado global; exige thread-safety).

## Idioms
- `AddTransient`, `AddScoped`, `AddSingleton`; registre tipos abertos com `AddScoped(typeof(IRepo<>), typeof(Repo<>))`.
- Dependa de interfaces e injete no construtor; o container resolve a árvore inteira.
- `IServiceProvider` injetável serve para fábricas/lazy, mas evite *service locator* como padrão.
- `ValidateOnBuild`/`ValidateScopes` ajudam a achar erros de grafo no startup.

## Armadilhas
- **Captive dependency**: singleton que depende de scoped fica com a primeira instância capturada — estado de request vaza entre requests. Analisadores (CA2012) detectam.
- O container só descarta o que ele criou; resolver `IDisposable` manualmente exige dispose próprio.
- Resolver scoped fora de um escopo (ex.: de singleton) lança; use `CreateScope()` em background services.
- Registre uma implementação por interface por lifetime; substituir entre builds pode esconder erros.
- Dependências exigidas mas não registradas falham apenas na resolução; teste o grafo no startup.

```csharp
builder.Services.AddScoped<IRepo, Repo>();
builder.Services.AddSingleton<ICache, MemoryCache>();
builder.Services.AddScoped(typeof(IValidator<>), typeof(Validator<>));
```

Regra: escopo curto, interfaces claras, dependências só via construtor e valide o grafo ao iniciar.
## Conexoes

- [[c-asyncawait-task-e-o-synchronizationcontext]]
- [[c-linq-execução-diferida-e-iqueryable-vs-ienumerable]]
- [[c-struct-vs-class-gc-e-alocação-de-memória]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]