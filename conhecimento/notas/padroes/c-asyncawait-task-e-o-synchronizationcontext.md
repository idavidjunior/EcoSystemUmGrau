---
tags: [asp, bloqueado, csharp, default, modernos, padrao]
aliases: [C#: async/await, Task e o SynchronizationContext]
date: 2026-08-11
---

# C#: async/await, Task e o SynchronizationContext

**Fonte:** csharp

# async/await, Task e o SynchronizationContext

`async/await` é açúcar sintático sobre `Task`/`Task<T>`. Um método `async` executa sincronamente até o primeiro `await` de uma task incompleta; dali em diante a continuação é agendada. O `SynchronizationContext` vigente no ponto do `await` é capturado e usado para retomar a execução no mesmo contexto (UI, ASP.NET, WPF).

## Idioms
- `Task<T>` para operações com retorno; `Task` para efeitos colaterais; `ValueTask`/`ValueTask<T>` em caminhos quentes para evitar alocação.
- CPU-bound: envolva em `Task.Run`; não torne o corpo `async` por si só.
- I/O-bound: use as APIs async nativas (`HttpClient`, streams); evite `.Result`/`.Wait()` — bloqueiam o thread do contexto e causam *deadlock*.
- Em bibliotecas, use `ConfigureAwait(false)` para não capturar contexto (em apps modernos é o default; a captura só importa em UI/WinForms/WPF/WebForms).
- Propague sempre o `CancellationToken` em todas as camadas.

## Armadilhas
- *Deadlock clássico*: a UI thread chama `.Result` num método async que precisa retomar no context — que está bloqueado. Solução: `async` até o topo.
- Exceções: `await` propaga a primeira exceção; `Task.WhenAll` agrega em `AggregateException`. Tasks «fire and forget» engolem falhas silenciosamente.
- `IAsyncEnumerable<T>` executa sob demanda; não assuma efeitos antes da iteração.
- Não use `async void` fora de event handlers: exceções não são capturadas.

```csharp
var data = await client.GetStringAsync(url).ConfigureAwait(false);
var results = await Task.WhenAll(items.Select(x => Work(x)));
```

Prefira async/await desde a borda do I/O e mantenha a cadeia inteira async; nunca bloqueie o contexto com `.Result`/`.Wait()`.
## Conexoes

- [[c-injeção-de-dependência-e-ciclo-de-vida-de-serviços]]
- [[c-linq-execução-diferida-e-iqueryable-vs-ienumerable]]
- [[c-struct-vs-class-gc-e-alocação-de-memória]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]