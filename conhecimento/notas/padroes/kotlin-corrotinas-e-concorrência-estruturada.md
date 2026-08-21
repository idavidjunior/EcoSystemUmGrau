---
tags: [future, kotlin, padrao, ponte, runblocking, tests]
aliases: [Kotlin: corrotinas e concorrência estruturada]
date: 2026-08-21
---

# Kotlin: corrotinas e concorrência estruturada

**Fonte:** kotlin

## Conceitos centrais

**Corrotinas** são threads leves gerenciadas pelo runtime (`kotlinx.coroutines`). `suspend fun` marca funções que podem pausar sem bloquear a thread; o compilador transforma em state machines. Os blocos construtores: `launch` (Fire-and-forget, retorna `Job`), `async` (retorna `Deferred<T>` — equivalente a `Future`), `runBlocking` (ponte para main/tests). **Dispatchers**: `Dispatchers.Main` (UI), `Default` (CPU), `IO` (I/O bloqueante), `Unconfined`. Trocas de contexto: `withContext(Dispatchers.IO) { ... }` — correto para chamadas bloqueantes sem `GlobalScope`.

**Concorrência estruturada**: corrotinas aninhadas herdam o escopo (`CoroutineScope`) do pai; se o pai cancela, os filhos cancelam. `coroutineScope { }` aguarda todos os filhos; `supervisorScope` deixa um filho falhar sem derrubar os irmãos. `Job.cancel()` + `ensureActive()` cooperam com cancelamento cooperativo (só em pontos de suspensão).

## Idioms

- `async {}` em pares e `awaitAll()` para fan-out/fan-in de tarefas paralelas.
- `Flow` para streams assíncronas com backpressure e `flowOn`/`buffer`; `StateFlow`/`SharedFlow` para estado reativo.
- `withContext` para operações bloqueantes — nunca rode trabalho de IO dentro do `Dispatchers.Main`.

## Armadilhas

- **Cancelamento não é interrupção**: código que não suspende (loop CPU-bound, `Thread.sleep`) ignora cancelamento; use `yield()`/`ensureActive()`.
- `GlobalScope.launch` cria corrotinas sem dono — vazam e não são canceladas com a UI; evite.
- Chamar `suspend` de callback/thread normal exige adaptador (`suspendCancellableCoroutine`); funções que ignoram `Continuation` e retornam imediatamente quebram o fluxo.
- Mudar o executor/thread dentro de `withContext` é custoso: agrupe chamadas bloqueantes em um único bloco.

## Boas práticas

- Defina seu próprio `CoroutineScope` (ou `viewModelScope`/`lifecycleScope` no Android) e cancele em cleanup.
- Para testes: `runTest` + `Dispatchers.setMain`; nunca dependa de timing real.
- Prefira `flow` com `catch`/`retry` declarativos a tratamento ad-hoc de exceções em `launch`.
## Conexoes

- [[cluster-hub-programacao]]
- [[kotlin-funções-propriedades-e-data-classes]]
- [[kotlin-null-safety-e-sistema-de-tipos]]
- [[padrao-hub-padroes]]